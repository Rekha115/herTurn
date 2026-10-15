import os
import logging
from typing import List, Dict, Any, Optional
import chromadb

from .ingestion import get_chroma_client, COLLECTION_NAME

logger = logging.getLogger("herturn.rag.retriever")


def retrieve_verified_resources(
    target_role: str,
    skill_gaps: Optional[List[str]] = None,
    top_k: int = 6,
    chroma_client: Optional[chromadb.ClientAPI] = None,
    collection_name: str = COLLECTION_NAME,
) -> Dict[str, Any]:
    """
    Retrieves verified learning resources from ChromaDB vector store
    based on the candidate's target role and identified skill gaps.

    Returns structured dictionary with:
      - rag_status: "retrieved", "empty", or "unavailable"
      - is_rag_used: bool
      - resources: List[Dict] with title, url, provider, type, difficulty, relevance_score
      - context_text: String prompt context for Gemini
      - source_count: int
    """
    try:
        client = chroma_client or get_chroma_client()
        # Check if collection exists
        try:
            collection = client.get_collection(name=collection_name)
        except Exception:
            logger.warning(f"ChromaDB collection '{collection_name}' does not exist.")
            return {
                "rag_status": "unavailable",
                "is_rag_used": False,
                "resources": [],
                "context_text": "",
                "source_count": 0,
                "message": f"Vector database collection '{collection_name}' not found. Please run ingestion.",
            }

        collection_count = collection.count()
        if collection_count == 0:
            logger.warning("ChromaDB collection is empty.")
            return {
                "rag_status": "empty",
                "is_rag_used": False,
                "resources": [],
                "context_text": "",
                "source_count": 0,
                "message": "Knowledge base collection is empty.",
            }

        # Build search queries
        clean_gaps = [g.strip() for g in (skill_gaps or []) if g and g.strip()]
        queries: List[str] = []

        # Primary composite query
        if clean_gaps:
            queries.append(f"Target Role: {target_role}. Skills and tool gaps to bridge: {', '.join(clean_gaps)}")
            # Individual gap queries for targeted coverage
            for gap in clean_gaps[:4]:
                queries.append(f"Learning tutorial guide for {gap} in role {target_role}")
        else:
            queries.append(f"Curriculum and learning guides for career role: {target_role}")

        # Query ChromaDB
        query_results = collection.query(
            query_texts=queries,
            n_results=min(top_k, collection_count),
            include=["documents", "metadatas", "distances"]
        )

        # Deduplicate and rank results across all query runs
        seen_ids = set()
        retrieved_items: List[Dict[str, Any]] = []

        raw_ids_list = query_results.get("ids", [])
        raw_metas_list = query_results.get("metadatas", [])
        raw_distances_list = query_results.get("distances", [])

        for q_idx in range(len(raw_ids_list)):
            q_ids = raw_ids_list[q_idx]
            q_metas = raw_metas_list[q_idx] if q_idx < len(raw_metas_list) else []
            q_dists = raw_distances_list[q_idx] if q_idx < len(raw_distances_list) else []

            for i in range(len(q_ids)):
                res_id = q_ids[i]
                if res_id in seen_ids:
                    continue
                seen_ids.add(res_id)

                meta = q_metas[i] if i < len(q_metas) else {}
                distance = q_dists[i] if i < len(q_dists) else 1.0

                # Compute approximate normalized relevance score (1.0 = identical)
                score = round(max(0.0, 1.0 - (float(distance) / 2.0)), 3)

                skills_list = [s.strip() for s in str(meta.get("skills_csv", "")).split(",") if s.strip()]
                roles_list = [r.strip() for r in str(meta.get("roles_csv", "")).split(",") if r.strip()]

                item = {
                    "id": meta.get("id", res_id),
                    "title": meta.get("title", "Educational Resource"),
                    "url": meta.get("url", "#"),
                    "provider": meta.get("provider", "Curated Reference"),
                    "type": meta.get("type", "Guide"),
                    "difficulty": meta.get("difficulty", "All Levels"),
                    "description": meta.get("description", ""),
                    "isVerified": bool(meta.get("isVerified", True)),
                    "skills": skills_list,
                    "targetRoles": roles_list,
                    "relevanceScore": score,
                }
                retrieved_items.append(item)

        # Sort by relevance score descending and limit to top_k
        retrieved_items.sort(key=lambda x: x["relevanceScore"], reverse=True)
        final_resources = retrieved_items[:top_k]

        if not final_resources:
            return {
                "rag_status": "no_matches",
                "is_rag_used": False,
                "resources": [],
                "context_text": "",
                "source_count": 0,
                "message": "No relevant resources matched candidate skill gaps.",
            }

        # Build prompt context string for Gemini
        context_lines = [
            "RETRIEVED VERIFIED LEARNING RESOURCES (RAG):",
            "The following verified educational resources were retrieved from the HerTurn curated knowledge base for this candidate:",
        ]

        for idx, res in enumerate(final_resources, 1):
            skills_display = ", ".join(res["skills"]) if isinstance(res["skills"], list) else str(res["skills"])
            context_lines.append(
                f"{idx}. Title: {res['title']}\n"
                f"   Provider: {res['provider']}\n"
                f"   Canonical URL: {res['url']}\n"
                f"   Type: {res['type']} | Difficulty: {res['difficulty']}\n"
                f"   Key Skills: {skills_display}\n"
                f"   Relevance Score: {res['relevanceScore']}"
            )

        context_lines.append(
            "\nCRITICAL CITATION & ANTI-HALLUCINATION RULES:\n"
            "1. You may ONLY cite external learning links that are explicitly listed in the RETRIEVED VERIFIED LEARNING RESOURCES above.\n"
            "2. When attaching a resource to a week module, use the EXACT Title and canonical URL from the list above.\n"
            "3. Set 'label': 'Verified Curriculum Resource (RAG)' for any resource cited from this list.\n"
            "4. NEVER invent, fabricate, or hallucinate URLs or resource names not in this list.\n"
            "5. If a week does not have an exact matching resource from this list, leave its resources array empty []."
        )

        context_text = "\n".join(context_lines)

        return {
            "rag_status": "retrieved",
            "is_rag_used": True,
            "resources": final_resources,
            "context_text": context_text,
            "source_count": len(final_resources),
            "message": f"Successfully retrieved {len(final_resources)} verified resources from ChromaDB.",
        }

    except Exception as e:
        logger.error(f"Error during ChromaDB retrieval: {e}", exc_info=True)
        return {
            "rag_status": "unavailable",
            "is_rag_used": False,
            "resources": [],
            "context_text": "",
            "source_count": 0,
            "message": f"RAG retrieval encountered an error: {str(e)}",
        }

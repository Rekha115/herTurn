import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import chromadb

logger = logging.getLogger("herturn.rag.ingestion")

# Default paths relative to backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_KB_PATH = Path(__file__).resolve().parent / "knowledge_base.json"
DEFAULT_CHROMA_PATH = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "herturn_resources"


def get_chroma_client(persist_directory: Optional[Path | str] = None) -> chromadb.ClientAPI:
    """
    Initializes a persistent ChromaDB client pointing to the local storage path,
    or an ephemeral Client if specifically configured (e.g., during tests).
    """
    if persist_directory == ":memory:":
        return chromadb.EphemeralClient()

    target_dir = Path(persist_directory or os.getenv("CHROMA_PERSIST_DIR") or DEFAULT_CHROMA_PATH)
    target_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(target_dir))


def load_knowledge_base(kb_file_path: Optional[Path | str] = None) -> List[Dict[str, Any]]:
    """
    Loads and validates the curated knowledge base JSON file.
    """
    file_path = Path(kb_file_path or DEFAULT_KB_PATH)
    if not file_path.exists():
        raise FileNotFoundError(f"Knowledge base file not found at: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Knowledge base root must be a JSON array of resources.")

    return data


def normalize_resource_chunk(resource: Dict[str, Any]) -> tuple[str, str, Dict[str, Any]]:
    """
    Normalizes a resource item and returns:
    (resource_id, document_chunk_text, metadata_dict)
    """
    res_id = str(resource.get("id") or f"res-{abs(hash(resource.get('url', '')))}")
    title = str(resource.get("title", "")).strip()
    url = str(resource.get("url", "")).strip()
    provider = str(resource.get("provider", "Unknown")).strip()
    res_type = str(resource.get("type", "Guide")).strip()
    difficulty = str(resource.get("difficulty", "All Levels")).strip()
    description = str(resource.get("description", "")).strip()

    skills = [str(s).strip() for s in resource.get("skills", []) if s]
    target_roles = [str(r).strip() for r in resource.get("targetRoles", []) if r]
    is_verified = bool(resource.get("isVerified", False))

    # Construct rich text chunk for vector embedding
    chunk_text = (
        f"Title: {title}\n"
        f"Provider: {provider}\n"
        f"Resource Type: {res_type}\n"
        f"Difficulty Level: {difficulty}\n"
        f"Target Roles: {', '.join(target_roles)}\n"
        f"Applicable Skills: {', '.join(skills)}\n"
        f"Description: {description}"
    )

    metadata = {
        "id": res_id,
        "title": title,
        "url": url,
        "provider": provider,
        "type": res_type,
        "difficulty": difficulty,
        "isVerified": is_verified,
        "skills_csv": ", ".join(skills),
        "roles_csv": ", ".join(target_roles),
        "description": description[:500],
    }

    return res_id, chunk_text, metadata


def ingest_resources(
    resources: Optional[List[Dict[str, Any]]] = None,
    kb_path: Optional[Path | str] = None,
    chroma_client: Optional[chromadb.ClientAPI] = None,
    persist_dir: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """
    Idempotent ingestion pipeline for curated career learning resources.
    Extracts, normalizes, embeds, and upserts into ChromaDB.
    """
    raw_resources = resources if resources is not None else load_knowledge_base(kb_path)
    client = chroma_client or get_chroma_client(persist_dir)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Curated verified returnee learning resources for HerTurn"}
    )

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for item in raw_resources:
        res_id, chunk_text, meta = normalize_resource_chunk(item)
        ids.append(res_id)
        documents.append(chunk_text)
        metadatas.append(meta)

    # Idempotent upsert: replaces existing records with matching IDs, adds new ones
    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    count = collection.count()
    logger.info(f"Ingested {len(ids)} resources into ChromaDB collection '{COLLECTION_NAME}'. Total count: {count}")

    return {
        "status": "success",
        "ingested_count": len(ids),
        "total_collection_count": count,
        "collection_name": COLLECTION_NAME,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = ingest_resources()
    print("Ingestion Complete:")
    print(json.dumps(result, indent=2))

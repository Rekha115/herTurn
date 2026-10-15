#!/usr/bin/env python
"""
Standalone CLI script to ingest curated career learning resources into ChromaDB.
Usage:
    python backend/scripts/ingest_knowledge_base.py
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.ingestion import ingest_resources

if __name__ == "__main__":
    print("Ingesting HerTurn Curated Knowledge Base into ChromaDB...")
    result = ingest_resources()
    print(f"Success! Ingested {result['ingested_count']} resources. Total collection count: {result['total_collection_count']}.")

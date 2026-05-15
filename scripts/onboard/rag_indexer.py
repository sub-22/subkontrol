"""RAG indexer — incremental indexing của project-design repo vào ChromaDB."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

CHUNK_SIZE = 80   # lines per chunk
CHUNK_OVERLAP = 10
SKIP_DIRS = {".git", ".morai", "node_modules", "__pycache__"}
INDEXABLE_EXTS = {".md", ".txt", ".yaml", ".yml", ".json"}


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _load_index(index_path: Path) -> dict[str, str]:
    """Load {filepath: hash} index."""
    if index_path.exists():
        return json.loads(index_path.read_text())
    return {}


def _save_index(index_path: Path, index: dict[str, str]) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2))


def _chunk_text(text: str, source: str) -> list[dict]:
    lines = text.splitlines()
    chunks = []
    i = 0
    chunk_idx = 0
    while i < len(lines):
        chunk_lines = lines[i: i + CHUNK_SIZE]
        content = "\n".join(chunk_lines).strip()
        if content:
            chunks.append({
                "id": f"{source}::chunk{chunk_idx}",
                "content": content,
                "metadata": {"source": source, "chunk": chunk_idx},
            })
            chunk_idx += 1
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _get_collection(chroma_path: str, namespace: str):
    import chromadb
    client = chromadb.PersistentClient(path=chroma_path)
    return client.get_or_create_collection(namespace)


def index(
    repo_dir: Path,
    namespace: str,
    chroma_path: str = ".morai/rag",
) -> dict[str, int]:
    """Incremental index: chỉ index files mới hoặc changed.

    Args:
        repo_dir: Root của project-design repo
        namespace: ChromaDB collection name, e.g. "subkontrol-design"
        chroma_path: Path tới ChromaDB storage
    Returns:
        {"indexed": N, "skipped": N, "deleted": N}
    """
    index_path = repo_dir / ".morai" / "rag" / "index.json"
    old_index = _load_index(index_path)
    new_index: dict[str, str] = {}
    stats = {"indexed": 0, "skipped": 0, "deleted": 0}

    collection = _get_collection(chroma_path, namespace)

    # Collect all indexable files
    all_files: list[Path] = []
    for path in repo_dir.rglob("*"):
        if path.is_file() and path.suffix in INDEXABLE_EXTS:
            if not any(skip in path.parts for skip in SKIP_DIRS):
                all_files.append(path)

    log.info("Found %d indexable files", len(all_files))

    for file_path in all_files:
        rel = str(file_path.relative_to(repo_dir))
        file_hash = _file_hash(file_path)
        new_index[rel] = file_hash

        # Skip nếu không thay đổi
        if old_index.get(rel) == file_hash:
            stats["skipped"] += 1
            continue

        # Index file
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        chunks = _chunk_text(text, rel)
        if not chunks:
            continue

        # Delete old chunks của file này (nếu có)
        try:
            existing = collection.get(where={"source": rel})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

        collection.add(
            ids=[c["id"] for c in chunks],
            documents=[c["content"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks],
        )
        log.info("Indexed: %s (%d chunks)", rel, len(chunks))
        stats["indexed"] += 1

    # Delete entries cho files đã bị xóa
    deleted_files = set(old_index.keys()) - set(new_index.keys())
    for rel in deleted_files:
        try:
            existing = collection.get(where={"source": rel})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
                stats["deleted"] += 1
                log.info("Deleted from index: %s", rel)
        except Exception:
            pass

    _save_index(index_path, new_index)
    log.info("RAG index updated: %s", stats)
    return stats

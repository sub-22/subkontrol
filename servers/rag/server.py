"""RAG MCP server — index và search documents/codebase."""

from __future__ import annotations

import os
import hashlib
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-rag")

CHROMA_PATH = os.getenv("CHROMA_PATH", ".morai/rag")

# File extensions được index
INDEXABLE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rb", ".rs",
    ".md", ".mdx", ".txt", ".yaml", ".yml", ".json", ".toml", ".env.example",
    ".sql", ".graphql", ".proto", ".sh", ".dockerfile",
}

# Thư mục bỏ qua
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "vendor", "target",
}

CHUNK_SIZE = 80   # lines per chunk
CHUNK_OVERLAP = 15


def _get_client():
    try:
        import chromadb
        return chromadb.PersistentClient(path=CHROMA_PATH)
    except ImportError:
        raise RuntimeError("chromadb not installed — run: uv sync")
    except Exception as e:
        raise RuntimeError(f"ChromaDB init failed at '{CHROMA_PATH}': {e}") from e


def _get_collection(namespace: str):
    client = _get_client()
    return client.get_or_create_collection(
        name=namespace,
        metadata={"hnsw:space": "cosine"},
    )


def _chunk_text(text: str, source: str) -> list[dict]:
    """Chia text thành chunks với overlap."""
    lines = text.splitlines()
    if len(lines) <= CHUNK_SIZE:
        return [{"content": text, "source": source, "chunk": 0}]

    chunks = []
    start = 0
    chunk_idx = 0
    while start < len(lines):
        end = min(start + CHUNK_SIZE, len(lines))
        chunk_text = "\n".join(lines[start:end])
        chunks.append({
            "content": chunk_text,
            "source": source,
            "chunk": chunk_idx,
        })
        chunk_idx += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def _make_id(source: str, chunk: int) -> str:
    raw = f"{source}::{chunk}"
    return hashlib.md5(raw.encode()).hexdigest()


@mcp.tool()
def scan_project(path: str, namespace: str = "default") -> dict:
    """Scan toàn bộ project, index vào RAG.

    Walk directory, đọc source files, chunk và embed.
    Bỏ qua node_modules, .git, binary files, lock files.

    Args:
        path: Absolute path tới project root
        namespace: Namespace để phân tách giữa các projects
    Returns:
        {"indexed": int, "skipped": int, "files": list[str]}
    """
    root = Path(path).resolve()
    if not root.exists():
        raise ValueError(f"Path không tồn tại: {path}")

    collection = _get_collection(namespace)

    indexed_files: list[str] = []
    skipped = 0
    all_docs: list[str] = []
    all_ids: list[str] = []
    all_metas: list[dict] = []

    for file_path in root.rglob("*"):
        # Bỏ qua thư mục trong skip list
        if any(skip in file_path.parts for skip in SKIP_DIRS):
            continue
        if not file_path.is_file():
            continue
        # Bỏ qua lock files và binary files
        if file_path.name in {"package-lock.json", "yarn.lock", "uv.lock", "poetry.lock"}:
            skipped += 1
            continue
        if file_path.suffix.lower() not in INDEXABLE_EXTENSIONS:
            skipped += 1
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            skipped += 1
            continue

        if not content.strip():
            skipped += 1
            continue

        rel_path = str(file_path.relative_to(root))
        chunks = _chunk_text(content, rel_path)

        for chunk in chunks:
            doc_id = _make_id(chunk["source"], chunk["chunk"])
            all_ids.append(doc_id)
            all_docs.append(chunk["content"])
            all_metas.append({
                "source": chunk["source"],
                "chunk": chunk["chunk"],
                "extension": file_path.suffix,
            })

        indexed_files.append(rel_path)

        # Upsert theo batch 100
        if len(all_ids) >= 100:
            collection.upsert(documents=all_docs, ids=all_ids, metadatas=all_metas)
            all_docs, all_ids, all_metas = [], [], []

    if all_ids:
        collection.upsert(documents=all_docs, ids=all_ids, metadatas=all_metas)

    return {
        "indexed": len(indexed_files),
        "skipped": skipped,
        "files": indexed_files,
    }


@mcp.tool()
def index_documents(docs: list[dict], namespace: str = "default") -> str:
    """Index danh sách documents vào vector store.

    Args:
        docs: List of {"content": str, "source": str, "metadata": dict (optional)}
        namespace: Namespace để phân tách context
    Returns:
        Số documents đã index
    """
    collection = _get_collection(namespace)

    all_ids: list[str] = []
    all_docs: list[str] = []
    all_metas: list[dict] = []

    for i, doc in enumerate(docs):
        content = doc.get("content", "").strip()
        if not content:
            continue
        source = doc.get("source", f"doc_{i}")
        meta = doc.get("metadata", {})
        meta["source"] = source

        chunks = _chunk_text(content, source)
        for chunk in chunks:
            all_ids.append(_make_id(chunk["source"], chunk["chunk"]))
            all_docs.append(chunk["content"])
            all_metas.append({**meta, "chunk": chunk["chunk"]})

    if all_ids:
        collection.upsert(documents=all_docs, ids=all_ids, metadatas=all_metas)

    return f"Đã index {len(all_ids)} chunks từ {len(docs)} documents"


@mcp.tool()
def search(query: str, namespace: str = "default", k: int = 5) -> list[dict]:
    """Semantic search trong vector store.

    Args:
        query: Câu truy vấn tự nhiên hoặc keyword
        namespace: Namespace cần search
        k: Số kết quả trả về
    Returns:
        List of {"content": str, "source": str, "score": float}
    """
    collection = _get_collection(namespace)

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "content": doc,
            "source": meta.get("source", ""),
            "score": round(1 - dist, 4),
        })

    return output


@mcp.tool()
def get_context(topic: str, namespace: str = "default", k: int = 8) -> str:
    """Lấy context đã format sẵn để đưa vào prompt.

    Args:
        topic: Chủ đề cần lấy context
        namespace: Namespace cần search
        k: Số chunks lấy về
    Returns:
        Formatted context string
    """
    results = search(topic, namespace, k)
    if not results:
        return f"Không tìm thấy context cho: {topic}"

    parts = []
    for r in results:
        parts.append(f"### {r['source']} (score: {r['score']})\n{r['content']}")

    return "\n\n---\n\n".join(parts)


@mcp.tool()
def list_namespaces() -> list[str]:
    """Liệt kê tất cả namespaces đang có trong vector store."""
    client = _get_client()
    return [c.name for c in client.list_collections()]


@mcp.tool()
def delete_namespace(namespace: str) -> str:
    """Xóa toàn bộ dữ liệu của một namespace.

    Args:
        namespace: Namespace cần xóa
    """
    client = _get_client()
    client.delete_collection(namespace)
    return f"Đã xóa namespace: {namespace}"


if __name__ == "__main__":
    mcp.run()

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.config import settings

try:
    import chromadb
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
except ImportError:
    chromadb = None
    EmbeddingFunction = object
    Documents = List[str]
    Embeddings = List[List[float]]


class GeminiOrFallbackEmbeddingFunction(EmbeddingFunction):
    """
    Multilingual embedding function that uses Gemini gemini-embedding-001
    with in-memory caching, fast 3s timeout, and instant deterministic hash fallback.
    """
    def __init__(self, api_key: str = "", model_name: str = "gemini-embedding-001"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._client = None
        self._sdk_type = None
        self._cache: Dict[str, List[float]] = {}
        self._init_gemini_client()

    def _init_gemini_client(self):
        if not self.api_key:
            return
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._sdk_type = "google-genai"
            return
        except Exception:
            pass

        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            self._client = legacy_genai
            self._sdk_type = "google-generativeai"
            return
        except Exception:
            pass

        try:
            import requests
            self._client = requests
            self._sdk_type = "rest"
        except Exception:
            self._client = None
            self._sdk_type = None

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        missing_docs = []
        missing_indices = []

        for idx, doc in enumerate(input):
            if doc in self._cache:
                embeddings.append(self._cache[doc])
            else:
                embeddings.append(None)
                missing_docs.append(doc)
                missing_indices.append(idx)

        if not missing_docs:
            return embeddings

        # Try to embed missing docs
        if self._client and self.api_key:
            try:
                if self._sdk_type == "rest":
                    import requests
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:embedContent?key={self.api_key}"
                    for m_idx, doc in zip(missing_indices, missing_docs):
                        payload = {"content": {"parts": [{"text": doc[:1000]}]}}
                        resp = requests.post(url, json=payload, timeout=3)
                        if resp.status_code == 200:
                            emb = resp.json().get("embedding", {}).get("values", [])
                            if emb:
                                self._cache[doc] = emb
                                embeddings[m_idx] = emb
                elif self._sdk_type == "google-genai":
                    for m_idx, doc in zip(missing_indices, missing_docs):
                        res = self._client.models.embed_content(model=self.model_name, contents=doc[:1000])
                        emb = res.embedding.values
                        self._cache[doc] = emb
                        embeddings[m_idx] = emb
            except Exception:
                pass

        # For any that remain None, compute deterministic fallback (dim=128)
        for idx, emb in enumerate(embeddings):
            if emb is None:
                doc = input[idx]
                vec = [0.0] * 128
                tokens = doc.lower().split()
                for token in tokens:
                    h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
                    idx_h = h % 128
                    vec[idx_h] += 1.0
                norm = sum(x * x for x in vec) ** 0.5
                if norm > 0:
                    vec = [x / norm for x in vec]
                self._cache[doc] = vec
                embeddings[idx] = vec

        return embeddings


class VectorStoreService:
    """
    Manages storage and semantic vector retrieval of policy documents using ChromaDB,
    with a JSON store fallback when ChromaDB is not installed.
    """
    COLLECTION_NAME = "gov_policies"

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = Path(persist_dir or settings.CHROMA_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.fallback_file = self.persist_dir / "store.json"
        
        self.embedding_fn = GeminiOrFallbackEmbeddingFunction(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.EMBEDDING_MODEL
        )

        if chromadb is not None:
            self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self.embedding_fn,
                metadata={"description": "Multilingual Indian Government Schemes and Policies"}
            )
            self._use_fallback = False
        else:
            self._use_fallback = True
            self.collection = None
            if not self.fallback_file.exists():
                self._save_fallback({})

    def _load_fallback(self) -> Dict[str, Any]:
        if self.fallback_file.exists():
            try:
                with open(self.fallback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_fallback(self, data: Dict[str, Any]):
        with open(self.fallback_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def reload_embeddings(self, api_key: str):
        self.embedding_fn = GeminiOrFallbackEmbeddingFunction(
            api_key=api_key,
            model_name=settings.EMBEDDING_MODEL
        )
        if not self._use_fallback and self.chroma_client:
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self.embedding_fn,
                metadata={"description": "Multilingual Indian Government Schemes and Policies"}
            )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0

        if not self._use_fallback and self.collection is not None:
            ids = [c["chunk_id"] for c in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [
                {
                    "document_name": c["document_name"],
                    "page_number": int(c["page_number"]),
                    "scheme_name": c.get("scheme_name", ""),
                }
                for c in chunks
            ]
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            return len(chunks)

        # Fallback storage
        store = self._load_fallback()
        for c in chunks:
            cid = c["chunk_id"]
            store[cid] = {
                "chunk_id": cid,
                "text": c["text"],
                "document_name": c["document_name"],
                "page_number": int(c["page_number"]),
                "scheme_name": c.get("scheme_name", ""),
            }
        self._save_fallback(store)
        return len(chunks)

    def query(
        self,
        query_text: str,
        n_results: int = 4,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self._use_fallback and self.collection is not None:
            if self.collection.count() == 0:
                return []
            actual_n = min(n_results, self.collection.count())
            results = self.collection.query(
                query_texts=[query_text],
                n_results=actual_n,
                where=where
            )
            formatted = []
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
                ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

                for doc, meta, dist, chunk_id in zip(docs, metas, distances, ids):
                    similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0))) if dist is not None else 0.8
                    formatted.append({
                        "chunk_id": chunk_id,
                        "text": doc,
                        "document_name": meta.get("document_name", "Unknown"),
                        "page_number": meta.get("page_number", 1),
                        "scheme_name": meta.get("scheme_name", ""),
                        "score": round(similarity, 3)
                    })
            return formatted

        # Fallback search
        store = self._load_fallback()
        if not store:
            return []

        query_tokens = set(query_text.lower().split())
        scored = []
        for cid, item in store.items():
            if where and where.get("scheme_name") and item.get("scheme_name") != where["scheme_name"]:
                continue
            text_tokens = set(item["text"].lower().split())
            intersection = query_tokens.intersection(text_tokens)
            score = len(intersection) / max(1, len(query_tokens))
            scored.append({
                "chunk_id": cid,
                "text": item["text"],
                "document_name": item["document_name"],
                "page_number": item["page_number"],
                "scheme_name": item["scheme_name"],
                "score": round(min(1.0, score + 0.5 if score > 0 else 0.1), 3)
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:n_results]

    def list_documents(self) -> List[Dict[str, Any]]:
        if not self._use_fallback and self.collection is not None:
            total = self.collection.count()
            if total == 0:
                return []
            all_data = self.collection.get(include=["metadatas"])
            docs_summary: Dict[str, Dict[str, Any]] = {}
            for meta in all_data.get("metadatas", []):
                if not meta:
                    continue
                doc_name = meta.get("document_name", "Unknown")
                page_num = meta.get("page_number", 1)
                scheme = meta.get("scheme_name", "")
                if doc_name not in docs_summary:
                    docs_summary[doc_name] = {
                        "filename": doc_name,
                        "chunks_count": 0,
                        "pages": set(),
                        "schemes": set()
                    }
                docs_summary[doc_name]["chunks_count"] += 1
                docs_summary[doc_name]["pages"].add(page_num)
                if scheme:
                    docs_summary[doc_name]["schemes"].add(scheme)

            return [
                {
                    "filename": name,
                    "chunks_count": data["chunks_count"],
                    "pages_count": len(data["pages"]),
                    "schemes": list(data["schemes"])
                }
                for name, data in docs_summary.items()
            ]

        # Fallback list
        store = self._load_fallback()
        docs_summary = {}
        for item in store.values():
            name = item["document_name"]
            if name not in docs_summary:
                docs_summary[name] = {"filename": name, "chunks_count": 0, "pages": set(), "schemes": set()}
            docs_summary[name]["chunks_count"] += 1
            docs_summary[name]["pages"].add(item["page_number"])
            if item.get("scheme_name"):
                docs_summary[name]["schemes"].add(item["scheme_name"])
        return [
            {
                "filename": name,
                "chunks_count": data["chunks_count"],
                "pages_count": len(data["pages"]),
                "schemes": list(data["schemes"])
            }
            for name, data in docs_summary.items()
        ]

    def delete_document(self, filename: str) -> int:
        if not self._use_fallback and self.collection is not None:
            all_data = self.collection.get(
                where={"document_name": filename},
                include=["metadatas"]
            )
            ids_to_del = all_data.get("ids", [])
            if ids_to_del:
                self.collection.delete(ids=ids_to_del)
            return len(ids_to_del)

        store = self._load_fallback()
        to_del = [k for k, v in store.items() if v["document_name"] == filename]
        for k in to_del:
            del store[k]
        self._save_fallback(store)
        return len(to_del)

    def get_stats(self) -> Dict[str, Any]:
        count = self.collection.count() if (not self._use_fallback and self.collection) else len(self._load_fallback())
        return {
            "total_chunks": count,
            "documents": self.list_documents()
        }


vector_store = VectorStoreService()

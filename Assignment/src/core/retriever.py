"""
Document retriever with semantic and hybrid search.
"""
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings

from ..config import CHROMA_DIR, EMBEDDING_MODEL, TOP_K_RETRIEVAL
from ..models.document import Document, DocumentChunk, SearchResult, RetrievalResult
from ..models.user import User
from ..utils.embeddings import get_embedding_model
from .rbac_enforcer import RBACEnforcer


class DocumentRetriever:
    """
    Retrieves documents using semantic search and hybrid retrieval.
    """

    def __init__(self, collection_name: str = "enterprise_docs"):
        self.collection_name = collection_name
        self.embedding_model = get_embedding_model()
        self.rbac_enforcer = RBACEnforcer()

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[Document]):
        """
        Add documents to the vector store.
        """
        if not documents:
            return

        ids = []
        texts = []
        metadatas = []
        embeddings = []

        for doc in documents:
            for chunk in doc.chunks:
                ids.append(chunk.id)
                texts.append(chunk.text)
                metadatas.append({
                    "document_id": doc.id,
                    "title": doc.title,
                    "department": doc.department,
                    "sensitivity_level": doc.sensitivity_level,
                    "role_required": doc.role_required,
                    "document_type": doc.document_type.value,
                    "file_name": doc.file_name,
                    "chunk_number": chunk.chunk_number,
                    "tags": ",".join(doc.tags) if doc.tags else ""
                })

                # Generate embedding
                embedding = self.embedding_model.embed_text(chunk.text)
                embeddings.append(embedding)

        # Add to collection
        if ids:
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            print(f"Added {len(ids)} chunks to vector store")

    def search(
        self,
        query: str,
        user: User,
        top_k: int = TOP_K_RETRIEVAL,
        where: Optional[Dict] = None,
        min_score: float = 0.0
    ) -> RetrievalResult:
        """
        Search for documents matching the query, with RBAC enforcement.
        """
        start_time = time.time()

        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(query)

        # Apply RBAC filters
        rbac_filter = self.rbac_enforcer.enforce_query_filter(user, where or {})

        # Search in ChromaDB
        try:
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k * 2,  # Get more, then filter
                "include": ["documents", "metadatas", "distances"]
            }
            if rbac_filter:
                query_params["where"] = rbac_filter

            results = self.collection.query(**query_params)
        except Exception as e:
            print(f"Search error: {e}")
            return RetrievalResult(
                query=query,
                results=[],
                total_count=0,
                processing_time=time.time() - start_time
            )

        # Process results
        search_results = []

        if results and results.get('ids') and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                # Convert distance to similarity score (cosine)
                distance = results['distances'][0][i] if results.get('distances') else 0
                score = 1.0 - distance  # Convert distance to similarity

                if score < min_score:
                    continue

                metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                text = results['documents'][0][i] if results.get('documents') else ""

                # Create a minimal Document and DocumentChunk from metadata
                from datetime import datetime

                doc = Document(
                    id=metadata.get("document_id", "unknown"),
                    title=metadata.get("title", "Unknown"),
                    content=text,
                    document_type=metadata.get("document_type", "unknown"),
                    source_path="",
                    file_name=metadata.get("file_name", "unknown"),
                    department=metadata.get("department", "general"),
                    sensitivity_level=metadata.get("sensitivity_level", "internal"),
                    role_required=metadata.get("role_required", "employee"),
                    tags=metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    file_size=0,
                    file_format=metadata.get("document_type", "unknown"),
                    mime_type="",
                    additional_metadata={}
                )

                chunk = DocumentChunk(
                    id=chunk_id,
                    text=text,
                    document_id=doc.id,
                    chunk_number=metadata.get("chunk_number", 0),
                    metadata=metadata
                )

                search_results.append(SearchResult(
                    document=doc,
                    chunk=chunk,
                    score=score,
                    metadata=metadata
                ))

        # Sort by score and take top K
        search_results.sort(key=lambda x: x.score, reverse=True)
        search_results = search_results[:top_k]

        processing_time = time.time() - start_time

        retrieval_result = RetrievalResult(
            query=query,
            results=search_results,
            total_count=len(search_results),
            processing_time=processing_time
        )

        return retrieval_result

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the document collection.
        """
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection_name
        }

    def clear_collection(self):
        """
        Clear all documents from the collection.
        """
        try:
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            print(f"Error clearing collection: {e}")

"""
Main RAG pipeline orchestrator.
"""
import time
import uuid
from typing import List, Dict, Any, Optional

from ..models.user import User
from ..models.query import Query, QueryResult, QueryRouter, QueryType, DataSource
from ..models.document import Document, RetrievalResult
from ..config import TOP_K_RETRIEVAL
from ..utils.audit_logger import get_audit_logger
from .retriever import DocumentRetriever
from .generator import ResponseGenerator
from .rbac_enforcer import RBACEnforcer


class RAGPipeline:
    """
    Main RAG pipeline that orchestrates retrieval, generation, and RBAC.
    """

    def __init__(self):
        self.retriever = DocumentRetriever()
        self.generator = ResponseGenerator()
        self.rbac_enforcer = RBACEnforcer()
        self.query_router = QueryRouter()
        self.audit_logger = get_audit_logger()

    def query(
        self,
        query_text: str,
        user: User,
        top_k: int = TOP_K_RETRIEVAL,
        require_citations: bool = True,
        temperature: float = 0.7,
        filters: Optional[Dict] = None
    ) -> QueryResult:
        """
        Process a user query through the full RAG pipeline.
        """
        start_time = time.time()
        query_id = f"q_{uuid.uuid4().hex[:12]}"

        # Create Query object
        query = Query(
            id=query_id,
            text=query_text,
            user_id=user.username,
            filters=filters or {}
        )

        # Classify query
        query.query_type = self.query_router.classify_query(query_text)
        query.target_sources = self.query_router.route_query(query_text)

        # Retrieve relevant documents (with RBAC enforcement)
        retrieval_result = self.retriever.search(
            query=query_text,
            user=user,
            top_k=top_k,
            where=filters
        )

        # Generate response
        try:
            answer = self.generator.generate_response(
                query=query_text,
                retrieval_result=retrieval_result,
                temperature=temperature,
                require_citations=require_citations
            )
        except Exception as e:
            print(f"Generation error: {e}")
            answer = "An error occurred while generating the response."

        # Calculate confidence
        confidence = self.generator.calculate_confidence(query_text, retrieval_result)

        # Build result
        processing_time = time.time() - start_time

        result = QueryResult(
            query=query,
            answer=answer,
            retrieved_documents=[
                {
                    "document_id": r.document.id,
                    "title": r.document.title,
                    "department": r.document.department,
                    "sensitivity": r.document.sensitivity_level,
                    "score": r.similarity_score,
                    "text_preview": r.chunk.text[:200] + "..." if len(r.chunk.text) > 200 else r.chunk.text
                } for r in retrieval_result.results
            ],
            citations=retrieval_result.get_citations() if require_citations else [],
            confidence=confidence,
            processing_time=processing_time,
            metadata={
                "query_type": query.query_type.value if query.query_type else None,
                "target_sources": [s.value for s in query.target_sources],
                "retrieval_time": retrieval_result.processing_time,
                "num_results": retrieval_result.total_count
            }
        )

        # Update user query count
        user.increment_query_count()

        # Log the query
        self.audit_logger.log_query(
            user_id=user.username,
            query_text=query_text,
            result_count=retrieval_result.total_count,
            processing_time=processing_time,
            success=True
        )

        return result

    def ingest_documents(self, documents: List[Document]):
        """
        Ingest documents into the RAG system.
        """
        if not documents:
            print("No documents to ingest")
            return

        print(f"Ingesting {len(documents)} documents...")
        self.retriever.add_documents(documents)
        self.audit_logger.log_system_event(
            event_type="document_ingestion",
            details={"num_documents": len(documents)}
        )

    def get_statistics(self) -> Dict:
        """
        Get pipeline statistics.
        """
        embedding_name = hasattr(self.retriever.embedding_model, 'model_name') and self.retriever.embedding_model.model_name or "tf-idf"
        generator_name = hasattr(self.generator, 'model_name') and self.generator.model_name or "extractive"

        return {
            "vector_store": self.retriever.get_collection_stats(),
            "generator_model": generator_name,
            "embedding_model": embedding_name
        }

    def search_similar(
        self,
        query_text: str,
        user: User,
        top_k: int = 5
    ) -> RetrievalResult:
        """
        Search for similar documents without generation.
        """
        return self.retriever.search(
            query=query_text,
            user=user,
            top_k=top_k
        )

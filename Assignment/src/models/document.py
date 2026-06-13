"""
Document models for storing enterprise data with metadata.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """Type of document source."""
    PDF = "pdf"
    SQL = "sql"
    JSON = "json"
    CSV = "csv"
    UNKNOWN = "unknown"


@dataclass
class DocumentChunk:
    """
    A chunk of text from a document with associated metadata.
    """
    id: str
    text: str
    document_id: str
    chunk_number: int
    metadata: Dict[str, Any]

    def __hash__(self):
        return hash(self.id)


@dataclass
class Document:
    """
    Represents an enterprise document with full metadata.
    """
    id: str
    title: str
    content: str
    document_type: DocumentType
    source_path: str
    file_name: str

    # RBAC metadata
    department: str
    sensitivity_level: str
    role_required: str
    tags: List[str]

    # System metadata
    created_at: datetime
    updated_at: datetime
    file_size: int
    file_format: str
    mime_type: str

    # Additional metadata for different document types
    additional_metadata: Dict[str, Any]

    # Chunks (split text for retrieval)
    chunks: List[DocumentChunk] = None

    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []

        if not isinstance(self.tags, list):
            self.tags = list(self.tags)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "document_type": self.document_type.value,
            "source_path": self.source_path,
            "file_name": self.file_name,
            "department": self.department,
            "sensitivity_level": self.sensitivity_level,
            "role_required": self.role_required,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "file_size": self.file_size,
            "file_format": self.file_format,
            "mime_type": self.mime_type,
            "additional_metadata": self.additional_metadata,
            "chunks": [
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "document_id": chunk.document_id,
                    "chunk_number": chunk.chunk_number,
                    "metadata": chunk.metadata
                } for chunk in self.chunks
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create Document from dictionary."""
        chunk_data = data.pop("chunks", [])
        chunks = [
            DocumentChunk(
                id=chunk["id"],
                text=chunk["text"],
                document_id=chunk["document_id"],
                chunk_number=chunk["chunk_number"],
                metadata=chunk["metadata"]
            ) for chunk in chunk_data
        ]

        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            document_type=DocumentType(data["document_type"]),
            source_path=data["source_path"],
            file_name=data["file_name"],
            department=data["department"],
            sensitivity_level=data["sensitivity_level"],
            role_required=data["role_required"],
            tags=data["tags"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            file_size=data["file_size"],
            file_format=data["file_format"],
            mime_type=data["mime_type"],
            additional_metadata=data["additional_metadata"],
            chunks=chunks
        )


@dataclass
class SearchResult:
    """
    Represents a single search result with score and context.
    """
    document: Document
    chunk: DocumentChunk
    score: float
    metadata: Dict[str, Any]

    @property
    def similarity_score(self) -> float:
        """Return similarity score between 0 and 1."""
        return float(self.score)


@dataclass
class RetrievalResult:
    """
    Complete retrieval results from multiple sources.
    """
    query: str
    results: List[SearchResult]
    total_count: int
    processing_time: float

    @property
    def documents(self) -> List[Document]:
        """Unique documents retrieved."""
        return list({r.document for r in self.results})

    def filter_by_sensitivity(self, max_sensitivity: str) -> List[SearchResult]:
        """Filter results by sensitivity level."""
        sensitivity_order = ["public", "internal", "confidential", "restricted"]
        max_idx = sensitivity_order.index(max_sensitivity)

        return [
            r for r in self.results
            if sensitivity_order.index(r.document.sensitivity_level) <= max_idx
        ]

    def filter_by_department(self, departments: List[str]) -> List[SearchResult]:
        """Filter results by department."""
        return [
            r for r in self.results
            if r.document.department in departments
        ]

    def get_top_k(self, k: int) -> List[SearchResult]:
        """Get top K results by score."""
        return sorted(self.results, key=lambda x: x.score, reverse=True)[:k]

    def get_sources(self) -> List[str]:
        """Get unique source document names."""
        return list(set([r.document.file_name for r in self.results]))

    def get_citations(self) -> List[str]:
        """Generate citation strings for all results."""
        citations = []
        for result in self.results:
            citations.append(
                f"Source: {result.document.file_name} "
                f"(Department: {result.document.department}, "
                f"Sensitivity: {result.document.sensitivity_level}, "
                f"Score: {result.similarity_score:.3f})"
            )
        return citations

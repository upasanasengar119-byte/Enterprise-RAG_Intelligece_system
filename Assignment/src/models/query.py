"""
Query models and routing logic.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class QueryType(Enum):
    """Type of query to route to different handlers."""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    PROCEDURAL = "procedural"
    DEFINITION = "definition"
    UNKNOWN = "unknown"


class DataSource(Enum):
    """Available data sources."""
    PDFS = "pdfs"
    DATABASES = "databases"
    JSON_LOGS = "json_logs"
    ALL = "all"


@dataclass
class Query:
    """
    Represents a user query with context and metadata.
    """
    id: str
    text: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    query_type: Optional[QueryType] = None
    target_sources: List[DataSource] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    max_results: int = 5
    temperature: float = 0.7
    require_citations: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.target_sources is None:
            self.target_sources = [DataSource.ALL]
        if self.filters is None:
            self.filters = {}

    def add_filter(self, key: str, value: Any):
        """Add a filter to the query."""
        self.filters[key] = value

    def add_source(self, source: DataSource):
        """Add a target source to the query."""
        if source not in self.target_sources:
            self.target_sources.append(source)

    def to_dict(self) -> Dict:
        """Convert query to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "query_type": self.query_type.value if self.query_type else None,
            "target_sources": [s.value for s in self.target_sources],
            "filters": self.filters,
            "max_results": self.max_results,
            "temperature": self.temperature,
            "require_citations": self.require_citations,
            "metadata": self.metadata
        }


@dataclass
class QueryResult:
    """
    Represents the result of a query execution.
    """
    query: Query
    answer: str
    retrieved_documents: List[Dict] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def add_citation(self, citation: str):
        """Add a citation to the result."""
        if citation not in self.citations:
            self.citations.append(citation)

    def add_document(self, document: Dict):
        """Add a retrieved document reference."""
        self.retrieved_documents.append(document)

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "query": self.query.to_dict(),
            "answer": self.answer,
            "retrieved_documents": self.retrieved_documents,
            "citations": self.citations,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "error": self.error
        }


class QueryRouter:
    """
    Routes queries to appropriate data sources based on query analysis.
    """

    def __init__(self):
        self.routing_rules = self._load_routing_rules()

    def _load_routing_rules(self) -> Dict[str, List[DataSource]]:
        """
        Load routing rules based on keywords and patterns.
        """
        return {
            # Document-related keywords → PDFs
            "pdf_keywords": [
                "document", "report", "policy", "procedure", "manual",
                "whitepaper", "specification", "guide", "handbook",
                "compliance", "regulation", "contract"
            ],

            # Database-related keywords → SQL/CSV
            "database_keywords": [
                "database", "table", "record", "row", "column",
                "sql", "query", "select", "insert", "update",
                "delete", "aggregate", "sum", "count", "average",
                "sales", "revenue", "expense", "profit", "budget",
                "employee", "payroll", "salary", "compensation"
            ],

            # Log-related keywords → JSON logs
            "log_keywords": [
                "log", "event", "alert", "audit", "monitoring",
                "incident", "error", "warning", "trace", "debug",
                "performance", "metric", "monitor", "notification"
            ],
        }

    def classify_query(self, query_text: str) -> QueryType:
        """
        Classify the type of query.
        """
        text_lower = query_text.lower()

        # Analytical queries
        if any(word in text_lower for word in ["analyze", "analysis", "trend", "pattern", "insight", "why", "how many"]):
            return QueryType.ANALYTICAL

        # Comparative queries
        if any(word in text_lower for word in ["compare", "difference", "vs", "versus", "better", "worse", "between"]):
            return QueryType.COMPARATIVE

        # Procedural queries
        if any(word in text_lower for word in ["how to", "steps", "process", "procedure", "method", "way to"]):
            return QueryType.PROCEDURAL

        # Definition queries
        if any(word in text_lower for word in ["what is", "define", "definition", "meaning", "explain", "describe"]):
            return QueryType.DEFINITION

        # Factual queries (default)
        if any(word in text_lower for word in ["what", "when", "where", "who", "which"]):
            return QueryType.FACTUAL

        return QueryType.UNKNOWN

    def route_query(self, query_text: str) -> List[DataSource]:
        """
        Route query to appropriate data sources based on keywords.
        """
        text_lower = query_text.lower()
        sources = []

        # Check PDF keywords
        if any(keyword in text_lower for keyword in self.routing_rules["pdf_keywords"]):
            sources.append(DataSource.PDFS)

        # Check database keywords
        if any(keyword in text_lower for keyword in self.routing_rules["database_keywords"]):
            sources.append(DataSource.DATABASES)

        # Check log keywords
        if any(keyword in text_lower for keyword in self.routing_rules["log_keywords"]):
            sources.append(DataSource.JSON_LOGS)

        # If no specific source matched, search all
        if not sources:
            sources = [DataSource.ALL]

        return sources

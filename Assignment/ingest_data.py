"""
Data ingestion script for the Enterprise RAG system.
Processes all enterprise data sources and loads them into the vector store.
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import ENTERPRISE_DATA_DIR
from src.data_sources.pdf_processor import PDFProcessor
from src.data_sources.database_handler import DatabaseHandler
from src.data_sources.json_processor import JSONLogProcessor
from src.core.rag_pipeline import RAGPipeline
from src.models.document import Document


# Define file metadata (department, sensitivity, role_required, tags)
PDF_METADATA: Dict[str, Dict[str, Any]] = {
    "employee_handbook.pdf": {
        "department": "hr",
        "sensitivity_level": "public",
        "role_required": "employee",
        "tags": ["handbook", "policies", "onboarding"]
    },
    "security_protocol.pdf": {
        "department": "operations",
        "sensitivity_level": "confidential",
        "role_required": "manager",
        "tags": ["security", "protocol", "confidential"]
    },
    "financial_report_q4.pdf": {
        "department": "finance",
        "sensitivity_level": "restricted",
        "role_required": "manager",
        "tags": ["finance", "quarterly", "earnings"]
    },
    "engineering_best_practices.pdf": {
        "department": "engineering",
        "sensitivity_level": "internal",
        "role_required": "employee",
        "tags": ["engineering", "best-practices", "development"]
    },
    "compensation_policy.pdf": {
        "department": "hr",
        "sensitivity_level": "confidential",
        "role_required": "manager",
        "tags": ["compensation", "salary", "benefits"]
    },
}

CSV_METADATA: Dict[str, Dict[str, Any]] = {
    "employees.csv": {
        "department": "hr",
        "sensitivity_level": "confidential",
        "role_required": "manager",
        "tags": ["employees", "hr-data"]
    },
    "sales.csv": {
        "department": "finance",
        "sensitivity_level": "internal",
        "role_required": "employee",
        "tags": ["sales", "transactions", "revenue"]
    },
    "budget.csv": {
        "department": "finance",
        "sensitivity_level": "confidential",
        "role_required": "manager",
        "tags": ["budget", "finance", "planning"]
    },
}

SQL_METADATA: Dict[str, Dict[str, Any]] = {
    "schema.sql": {
        "department": "engineering",
        "sensitivity_level": "internal",
        "role_required": "employee",
        "tags": ["database", "schema", "engineering"]
    },
}

JSON_METADATA: Dict[str, Dict[str, Any]] = {
    "audit_logs.json": {
        "department": "operations",
        "sensitivity_level": "confidential",
        "role_required": "manager",
        "tags": ["audit", "logs", "security"]
    },
    "system_alerts.json": {
        "department": "operations",
        "sensitivity_level": "internal",
        "role_required": "employee",
        "tags": ["alerts", "monitoring", "operations"]
    },
    "application_logs.json": {
        "department": "operations",
        "sensitivity_level": "internal",
        "role_required": "employee",
        "tags": ["application", "logs", "debugging"]
    },
}


def ingest_all_data():
    """
    Ingest all data from enterprise data sources into the RAG system.
    """
    print("=" * 70)
    print("Enterprise RAG - Data Ingestion")
    print("=" * 70)

    all_documents = []

    # Initialize processors
    pdf_processor = PDFProcessor()
    db_handler = DatabaseHandler()
    json_processor = JSONLogProcessor()

    # 1. Process PDFs
    print("\n[1/3] Processing PDF documents...")
    pdf_dir = ENTERPRISE_DATA_DIR / "pdfs"
    if pdf_dir.exists():
        pdf_docs = pdf_processor.process_directory(pdf_dir, PDF_METADATA)
        all_documents.extend(pdf_docs)
        print(f"  -> Processed {len(pdf_docs)} PDF documents")
    else:
        print(f"  ! PDF directory not found: {pdf_dir}")

    # 2. Process databases (CSV + SQL)
    print("\n[2/3] Processing database files...")
    db_dir = ENTERPRISE_DATA_DIR / "databases"
    if db_dir.exists():
        # Combine metadata for all database files
        all_db_metadata = {**CSV_METADATA, **SQL_METADATA}
        db_docs = db_handler.process_directory(db_dir, all_db_metadata)
        all_documents.extend(db_docs)
        print(f"  -> Processed {len(db_docs)} database documents")
    else:
        print(f"  ! Database directory not found: {db_dir}")

    # 3. Process JSON logs
    print("\n[3/3] Processing JSON logs...")
    json_dir = ENTERPRISE_DATA_DIR / "json_logs"
    if json_dir.exists():
        json_docs = json_processor.process_directory(json_dir, JSON_METADATA)
        all_documents.extend(json_docs)
        print(f"  -> Processed {len(json_docs)} JSON documents")
    else:
        print(f"  ! JSON directory not found: {json_dir}")

    # 4. Add to RAG system
    print(f"\n[4/4] Loading {len(all_documents)} documents into vector store...")
    print("  (This may take a few minutes on first run as it downloads models...)")

    try:
        rag = RAGPipeline()
        rag.ingest_documents(all_documents)

        # Show statistics
        stats = rag.get_statistics()
        print("\n" + "=" * 70)
        print("Ingestion Complete!")
        print("=" * 70)
        print(f"Vector Store: {stats['vector_store']}")
        print(f"Embedding Model: {stats['embedding_model']}")
        print(f"Generation Model: {stats['generator_model']}")

    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = ingest_all_data()
    sys.exit(0 if success else 1)

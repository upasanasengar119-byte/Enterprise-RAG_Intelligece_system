"""
Database handler for SQL and CSV files.
"""
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..models.document import Document, DocumentChunk, DocumentType
from ..utils.text_splitter import TextSplitter


class DatabaseHandler:
    """
    Handles SQL/CSV database files and converts them to documents.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def process_csv(
        self,
        csv_path: Path,
        department: str = "general",
        sensitivity_level: str = "internal",
        role_required: str = "employee",
        tags: List[str] = None
    ) -> Document:
        """
        Process a CSV file and return a Document object.
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Read CSV
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        # Convert to text representation
        text = self._rows_to_text(rows, csv_path.stem)

        # Get file stats
        file_stats = csv_path.stat()
        file_size = file_stats.st_size
        file_name = csv_path.name

        # Generate document ID
        doc_id = self._generate_document_id(text, file_name)

        # Create chunks
        text_chunks = self.text_splitter.split_text(text)
        chunks = []
        for i, chunk in enumerate(text_chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_metadata = {
                "department": department,
                "sensitivity_level": sensitivity_level,
                "role_required": role_required,
                "source_file": file_name,
                "chunk_number": i,
                "total_chunks": len(text_chunks)
            }
            chunks.append(DocumentChunk(
                id=chunk_id,
                text=chunk.text,
                document_id=doc_id,
                chunk_number=i,
                metadata=chunk_metadata
            ))

        document = Document(
            id=doc_id,
            title=f"Database Table: {csv_path.stem.replace('_', ' ').title()}",
            content=text,
            document_type=DocumentType.CSV,
            source_path=str(csv_path),
            file_name=file_name,
            department=department,
            sensitivity_level=sensitivity_level,
            role_required=role_required,
            tags=tags or [],
            created_at=datetime.fromtimestamp(file_stats.st_ctime),
            updated_at=datetime.fromtimestamp(file_stats.st_mtime),
            file_size=file_size,
            file_format="csv",
            mime_type="text/csv",
            additional_metadata={
                "num_rows": len(rows),
                "columns": list(rows[0].keys()) if rows else []
            },
            chunks=chunks
        )

        return document

    def process_sql(
        self,
        sql_path: Path,
        department: str = "general",
        sensitivity_level: str = "internal",
        role_required: str = "employee",
        tags: List[str] = None
    ) -> Document:
        """
        Process a SQL file and return a Document object.
        """
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")

        # Read SQL
        with open(sql_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Get file stats
        file_stats = sql_path.stat()
        file_size = file_stats.st_size
        file_name = sql_path.name

        # Generate document ID
        doc_id = self._generate_document_id(text, file_name)

        # Create chunks
        text_chunks = self.text_splitter.split_text(text)
        chunks = []
        for i, chunk in enumerate(text_chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_metadata = {
                "department": department,
                "sensitivity_level": sensitivity_level,
                "role_required": role_required,
                "source_file": file_name,
                "chunk_number": i,
                "total_chunks": len(text_chunks)
            }
            chunks.append(DocumentChunk(
                id=chunk_id,
                text=chunk.text,
                document_id=doc_id,
                chunk_number=i,
                metadata=chunk_metadata
            ))

        document = Document(
            id=doc_id,
            title=f"SQL Schema: {sql_path.stem.replace('_', ' ').title()}",
            content=text,
            document_type=DocumentType.SQL,
            source_path=str(sql_path),
            file_name=file_name,
            department=department,
            sensitivity_level=sensitivity_level,
            role_required=role_required,
            tags=tags or [],
            created_at=datetime.fromtimestamp(file_stats.st_ctime),
            updated_at=datetime.fromtimestamp(file_stats.st_mtime),
            file_size=file_size,
            file_format="sql",
            mime_type="application/sql",
            additional_metadata={
                "num_chunks": len(chunks)
            },
            chunks=chunks
        )

        return document

    def _rows_to_text(self, rows: List[Dict], table_name: str) -> str:
        """
        Convert CSV rows to a natural language text representation.
        """
        if not rows:
            return f"Empty table: {table_name}"

        text_parts = [f"Database table: {table_name}"]
        text_parts.append(f"Total records: {len(rows)}")
        text_parts.append("")

        # Add column information
        columns = list(rows[0].keys())
        text_parts.append(f"Columns: {', '.join(columns)}")
        text_parts.append("")

        # Add summary statistics for numeric columns
        numeric_columns = self._get_numeric_columns(rows, columns)
        if numeric_columns:
            text_parts.append("Summary statistics:")
            for col in numeric_columns:
                values = [float(row[col]) for row in rows if row.get(col) and self._is_numeric(row[col])]
                if values:
                    text_parts.append(
                        f"- {col}: min={min(values)}, max={max(values)}, "
                        f"avg={sum(values)/len(values):.2f}, total={sum(values):.2f}"
                    )
            text_parts.append("")

        # Add record details (limit to first 50 for context)
        text_parts.append("Records:")
        for i, row in enumerate(rows[:50]):
            row_text = f"Record {i+1}: "
            row_parts = []
            for col, value in row.items():
                if value is not None and str(value).strip():
                    row_parts.append(f"{col}={value}")
            row_text += ", ".join(row_parts)
            text_parts.append(row_text)

        if len(rows) > 50:
            text_parts.append(f"... and {len(rows) - 50} more records")

        return "\n".join(text_parts)

    def _get_numeric_columns(self, rows: List[Dict], columns: List[str]) -> List[str]:
        """
        Identify numeric columns in the data.
        """
        numeric_cols = []
        for col in columns:
            # Check if most values are numeric
            numeric_count = sum(1 for row in rows if row.get(col) and self._is_numeric(row[col]))
            if numeric_count > len(rows) * 0.5:
                numeric_cols.append(col)
        return numeric_cols

    def _is_numeric(self, value: str) -> bool:
        """
        Check if a string value is numeric.
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _generate_document_id(self, content: str, file_name: str) -> str:
        """
        Generate a unique document ID.
        """
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        file_hash = hashlib.md5(file_name.encode('utf-8')).hexdigest()[:8]
        return f"db_{file_hash}_{content_hash}"

    def process_directory(
        self,
        directory: Path,
        file_metadata: Dict[str, Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process all CSV and SQL files in a directory.
        """
        documents = []
        if not directory.exists():
            return documents

        file_metadata = file_metadata or {}

        # Process CSV files
        for csv_file in directory.glob("*.csv"):
            meta = file_metadata.get(csv_file.name, {})
            try:
                doc = self.process_csv(
                    csv_path=csv_file,
                    department=meta.get("department", "general"),
                    sensitivity_level=meta.get("sensitivity_level", "internal"),
                    role_required=meta.get("role_required", "employee"),
                    tags=meta.get("tags", [])
                )
                documents.append(doc)
                print(f"Processed CSV: {csv_file.name} ({doc.additional_metadata['num_rows']} rows)")
            except Exception as e:
                print(f"Error processing {csv_file.name}: {e}")

        # Process SQL files
        for sql_file in directory.glob("*.sql"):
            meta = file_metadata.get(sql_file.name, {})
            try:
                doc = self.process_sql(
                    sql_path=sql_file,
                    department=meta.get("department", "general"),
                    sensitivity_level=meta.get("sensitivity_level", "internal"),
                    role_required=meta.get("role_required", "employee"),
                    tags=meta.get("tags", [])
                )
                documents.append(doc)
                print(f"Processed SQL: {sql_file.name} ({len(doc.chunks)} chunks)")
            except Exception as e:
                print(f"Error processing {sql_file.name}: {e}")

        return documents
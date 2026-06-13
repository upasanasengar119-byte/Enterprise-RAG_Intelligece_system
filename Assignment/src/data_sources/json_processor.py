"""
JSON log processor for audit trails and event logs.
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..models.document import Document, DocumentChunk, DocumentType
from ..utils.text_splitter import TextSplitter


class JSONLogProcessor:
    """
    Processes JSON log files and audit trails.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def process_json(
        self,
        json_path: Path,
        department: str = "general",
        sensitivity_level: str = "internal",
        role_required: str = "employee",
        tags: List[str] = None
    ) -> List[Document]:
        """
        Process a JSON log file and return one or more Document objects.
        """
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        # Read JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Get file stats
        file_stats = json_path.stat()
        file_size = file_stats.st_size
        file_name = json_path.name

        documents = []

        # Handle different JSON structures
        if isinstance(data, list):
            # Group logs into chunks of 20 per document
            chunk_size_records = 20
            for i in range(0, len(data), chunk_size_records):
                batch = data[i:i+chunk_size_records]
                doc = self._create_log_document(
                    logs=batch,
                    file_path=json_path,
                    file_name=file_name,
                    file_size=file_size,
                    department=department,
                    sensitivity_level=sensitivity_level,
                    role_required=role_required,
                    tags=tags,
                    batch_number=i // chunk_size_records
                )
                documents.append(doc)
        elif isinstance(data, dict):
            # Single JSON object
            doc = self._create_log_document(
                logs=[data],
                file_path=json_path,
                file_name=file_name,
                file_size=file_size,
                department=department,
                sensitivity_level=sensitivity_level,
                role_required=role_required,
                tags=tags,
                batch_number=0
            )
            documents.append(doc)
        else:
            # Scalar or other type
            text = str(data)
            doc = self._create_text_document(
                text=text,
                file_path=json_path,
                file_name=file_name,
                file_size=file_size,
                department=department,
                sensitivity_level=sensitivity_level,
                role_required=role_required,
                tags=tags
            )
            documents.append(doc)

        return documents

    def _create_log_document(
        self,
        logs: List[Dict],
        file_path: Path,
        file_name: str,
        file_size: int,
        department: str,
        sensitivity_level: str,
        role_required: str,
        tags: List[str],
        batch_number: int
    ) -> Document:
        """
        Create a Document from a batch of log entries.
        """
        # Convert logs to text
        text = self._logs_to_text(logs, file_path.stem, batch_number)

        # Generate document ID
        doc_id = self._generate_document_id(text, file_name, batch_number)

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
                "total_chunks": len(text_chunks),
                "log_batch": batch_number
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
            title=f"Log File: {file_path.stem} (Batch {batch_number + 1})",
            content=text,
            document_type=DocumentType.JSON,
            source_path=str(file_path),
            file_name=file_name,
            department=department,
            sensitivity_level=sensitivity_level,
            role_required=role_required,
            tags=tags or [],
            created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
            updated_at=datetime.fromtimestamp(file_path.stat().st_mtime),
            file_size=file_size,
            file_format="json",
            mime_type="application/json",
            additional_metadata={
                "num_logs": len(logs),
                "batch_number": batch_number
            },
            chunks=chunks
        )

        return document

    def _create_text_document(
        self,
        text: str,
        file_path: Path,
        file_name: str,
        file_size: int,
        department: str,
        sensitivity_level: str,
        role_required: str,
        tags: List[str]
    ) -> Document:
        """
        Create a Document from plain text content.
        """
        # Generate document ID
        doc_id = self._generate_document_id(text, file_name, 0)

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
            title=f"Log File: {file_path.stem}",
            content=text,
            document_type=DocumentType.JSON,
            source_path=str(file_path),
            file_name=file_name,
            department=department,
            sensitivity_level=sensitivity_level,
            role_required=role_required,
            tags=tags or [],
            created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
            updated_at=datetime.fromtimestamp(file_path.stat().st_mtime),
            file_size=file_size,
            file_format="json",
            mime_type="application/json",
            additional_metadata={"num_chunks": len(chunks)},
            chunks=chunks
        )

        return document

    def _logs_to_text(self, logs: List[Dict], source_name: str, batch_number: int) -> str:
        """
        Convert log entries to natural language text.
        """
        if not logs:
            return f"Empty log file: {source_name}"

        text_parts = [f"Log entries from: {source_name} (Batch {batch_number + 1})"]
        text_parts.append(f"Total log entries: {len(logs)}")
        text_parts.append("")

        # Add summary
        if logs:
            first_log = logs[0]
            text_parts.append(f"First entry timestamp: {first_log.get('timestamp', 'N/A')}")
            last_log = logs[-1]
            text_parts.append(f"Last entry timestamp: {last_log.get('timestamp', 'N/A')}")

            # Count log levels/types
            levels = {}
            for log in logs:
                level = log.get('level', log.get('severity', log.get('type', 'INFO')))
                levels[level] = levels.get(level, 0) + 1

            if levels:
                text_parts.append("Log level distribution:")
                for level, count in sorted(levels.items()):
                    text_parts.append(f"- {level}: {count}")
            text_parts.append("")

        # Add detailed log entries
        text_parts.append("Log entries:")
        for i, log in enumerate(logs):
            log_text = f"Entry {i+1}: "
            log_parts = []

            # Common fields
            for field in ['timestamp', 'level', 'severity', 'type', 'event', 'action', 'user', 'message', 'description', 'status', 'code']:
                if field in log:
                    value = log[field]
                    if isinstance(value, (str, int, float, bool)):
                        log_parts.append(f"{field}={value}")

            # If we have message/description, include it
            if 'message' in log:
                log_parts.append(f"details: {log['message']}")
            elif 'description' in log:
                log_parts.append(f"details: {log['description']}")

            # Include any other fields not yet included
            included_fields = {'timestamp', 'level', 'severity', 'type', 'event', 'action', 'user', 'message', 'description', 'status', 'code'}
            for key, value in log.items():
                if key not in included_fields and isinstance(value, (str, int, float, bool)):
                    log_parts.append(f"{key}={value}")

            log_text += ", ".join(log_parts)
            text_parts.append(log_text)

        return "\n".join(text_parts)

    def _generate_document_id(self, content: str, file_name: str, batch_number: int) -> str:
        """
        Generate a unique document ID.
        """
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        file_hash = hashlib.md5(file_name.encode('utf-8')).hexdigest()[:8]
        return f"json_{file_hash}_{batch_number}_{content_hash}"

    def process_directory(
        self,
        directory: Path,
        file_metadata: Dict[str, Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process all JSON files in a directory.
        """
        documents = []
        if not directory.exists():
            return documents

        file_metadata = file_metadata or {}

        for json_file in directory.glob("*.json"):
            meta = file_metadata.get(json_file.name, {})
            try:
                docs = self.process_json(
                    json_path=json_file,
                    department=meta.get("department", "general"),
                    sensitivity_level=meta.get("sensitivity_level", "internal"),
                    role_required=meta.get("role_required", "employee"),
                    tags=meta.get("tags", [])
                )
                documents.extend(docs)
                print(f"Processed JSON: {json_file.name} ({len(docs)} documents)")
            except Exception as e:
                print(f"Error processing {json_file.name}: {e}")

        return documents
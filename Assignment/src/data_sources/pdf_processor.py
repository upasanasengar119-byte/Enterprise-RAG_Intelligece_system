"""
Document processor for text-based document files.
Handles .pdf, .txt, .md files as document content.
"""
import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..models.document import Document, DocumentChunk, DocumentType
from ..utils.text_splitter import TextSplitter


class PDFProcessor:
    """
    Processes document files and extracts text with metadata.
    Works with both real PDFs (if pypdf available) and text-based files.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.pypdf_available = self._check_pypdf()

    def _check_pypdf(self) -> bool:
        """Check if pypdf is available for real PDF processing."""
        try:
            from pypdf import PdfReader
            return True
        except ImportError:
            return False

    def process_pdf(
        self,
        file_path: Path,
        department: str = "general",
        sensitivity_level: str = "internal",
        role_required: str = "employee",
        tags: List[str] = None
    ) -> Document:
        """Process a document file and return a Document object."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Extract text
        if file_path.suffix.lower() == '.pdf' and self.pypdf_available:
            text = self._extract_pdf_text(file_path)
        else:
            # Treat as text file
            text = self._extract_text_file(file_path)

        # Get file metadata
        file_stats = file_path.stat()
        file_size = file_stats.st_size
        file_name = file_path.name

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

        # Extract title
        title = self._extract_title(text, file_name)

        # Create document
        document = Document(
            id=doc_id,
            title=title,
            content=text,
            document_type=DocumentType.PDF,
            source_path=str(file_path),
            file_name=file_name,
            department=department,
            sensitivity_level=sensitivity_level,
            role_required=role_required,
            tags=tags or [],
            created_at=datetime.fromtimestamp(file_stats.st_ctime),
            updated_at=datetime.fromtimestamp(file_stats.st_mtime),
            file_size=file_size,
            file_format=file_path.suffix.lstrip('.'),
            mime_type=self._get_mime_type(file_path.suffix),
            additional_metadata={
                "num_chunks": len(chunks),
                "num_pages": self._count_pages(file_path) if self.pypdf_available else 1
            },
            chunks=chunks
        )

        return document

    def _extract_text_file(self, file_path: Path) -> str:
        """Read a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
        return self._clean_text(text)

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from a real PDF file."""
        from pypdf import PdfReader
        text = ""
        try:
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        except Exception as e:
            print(f"Error extracting PDF text from {pdf_path}: {e}")
        return self._clean_text(text)

    def _count_pages(self, pdf_path: Path) -> int:
        """Count pages in a real PDF."""
        if not self.pypdf_available:
            return 1
        try:
            from pypdf import PdfReader
            return len(PdfReader(str(pdf_path)).pages)
        except Exception:
            return 1

    def _get_mime_type(self, suffix: str) -> str:
        """Get MIME type for file extension."""
        mime_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(suffix.lower(), 'application/octet-stream')

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()

    def _extract_title(self, text: str, file_name: str) -> str:
        """Extract title from text or use filename."""
        if text:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                first_line = lines[0]
                if 5 <= len(first_line) <= 200:
                    return first_line
        return Path(file_name).stem.replace('_', ' ').replace('-', ' ').title()

    def _generate_document_id(self, content: str, file_name: str) -> str:
        """Generate a unique document ID."""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        file_hash = hashlib.md5(file_name.encode('utf-8')).hexdigest()[:8]
        return f"doc_{file_hash}_{content_hash}"

    def process_directory(
        self,
        directory: Path,
        file_metadata: Dict[str, Dict[str, Any]] = None
    ) -> List[Document]:
        """Process all document files in a directory."""
        documents = []
        if not directory.exists():
            return documents

        file_metadata = file_metadata or {}

        # Process .pdf, .txt, .md files
        for pattern in ["*.pdf", "*.txt", "*.md"]:
            for file_path in directory.glob(pattern):
                meta = file_metadata.get(file_path.name, {})
                try:
                    doc = self.process_pdf(
                        file_path=file_path,
                        department=meta.get("department", "general"),
                        sensitivity_level=meta.get("sensitivity_level", "internal"),
                        role_required=meta.get("role_required", "employee"),
                        tags=meta.get("tags", [])
                    )
                    documents.append(doc)
                    print(f"  Processed: {file_path.name} ({len(doc.chunks)} chunks)")
                except Exception as e:
                    print(f"  Error processing {file_path.name}: {e}")

        return documents

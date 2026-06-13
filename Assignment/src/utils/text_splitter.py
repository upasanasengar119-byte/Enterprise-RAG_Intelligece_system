"""
Text splitting and chunking utilities.
"""
import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    text: str
    start_index: int
    end_index: int
    chunk_number: int


class TextSplitter:
    """
    Splits text into smaller chunks for embedding and retrieval.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = " "
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> List[TextChunk]:
        """
        Split text into chunks with overlap.
        """
        if not text or not text.strip():
            return []

        # Clean and normalize text
        text = self._clean_text(text)

        # Split by sentences first for better boundaries
        sentences = self._split_sentences(text)

        if not sentences:
            return []

        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_number = 0
        char_position = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence would exceed chunk size, save current chunk
            if current_chunk and len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                chunks.append(TextChunk(
                    text=current_chunk.strip(),
                    start_index=current_start,
                    end_index=current_start + len(current_chunk),
                    chunk_number=chunk_number
                ))
                chunk_number += 1

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and chunks:
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + " " + sentence
                    current_start = char_position - len(overlap_text)
                else:
                    current_chunk = sentence
                    current_start = char_position
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    current_start = char_position

            char_position += len(sentence) + 1

        # Add the last chunk
        if current_chunk:
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                start_index=current_start,
                end_index=current_start + len(current_chunk),
                chunk_number=chunk_number
            ))

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        """
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        """
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_text(self, text: str) -> str:
        """
        Get overlap text from the end of a chunk.
        """
        if len(text) <= self.chunk_overlap:
            return text

        # Get last N characters, but try to break at a word boundary
        overlap = text[-self.chunk_overlap:]
        # Find first space
        space_idx = overlap.find(' ')
        if space_idx > 0:
            overlap = overlap[space_idx+1:]

        return overlap


def split_into_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    Convenience function to split text into chunks.
    """
    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)
    return [chunk.text for chunk in chunks]

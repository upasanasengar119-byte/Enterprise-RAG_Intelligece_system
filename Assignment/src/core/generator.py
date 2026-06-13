"""
Simplified response generator using extractive summarization.
Combines retrieved chunks into a coherent response with citations.
"""
import time
import re
from typing import List, Dict, Any
from collections import Counter

from ..models.document import RetrievalResult
from ..config import GENERATION_CONFIG


class ResponseGenerator:
    """
    Generates responses using extractive summarization of retrieved documents.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or "extractive-summarizer"
        self.model = None
        self.tokenizer = None
        # Try loading transformers, but don't fail if unavailable
        self._try_load_model()

    def _try_load_model(self):
        """Try to load a generative model, but don't fail."""
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch

            from ..config import GENERATION_MODEL
            print(f"Loading model: {GENERATION_MODEL}")
            self.tokenizer = AutoTokenizer.from_pretrained(GENERATION_MODEL, use_fast=True)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(GENERATION_MODEL)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model_name = GENERATION_MODEL
            print("Model loaded successfully")
        except Exception as e:
            print(f"Note: Using extractive summarization (transformers unavailable: {type(e).__name__})")
            self.model = None

    def generate_response(
        self,
        query: str,
        retrieval_result: RetrievalResult,
        temperature: float = 0.7,
        max_length: int = 512,
        require_citations: bool = True
    ) -> str:
        """Generate a response based on query and retrieved documents."""
        if self.model is not None:
            return self._generate_with_model(query, retrieval_result, max_length, require_citations)
        return self._generate_extractive(query, retrieval_result, require_citations)

    def _generate_with_model(self, query, retrieval_result, max_length, require_citations):
        """Generate using the loaded model."""
        import torch

        context = self._build_context(retrieval_result)
        if not context:
            return "I couldn't find relevant information to answer your question."

        prompt = f"""Based on the following documents, answer the user's question.
Be factual, concise, and cite your sources.

Documents:
{context}

Question: {query}

Answer:"""

        start_time = time.time()
        input_ids = self.tokenizer.encode(
            prompt,
            return_tensors="pt",
            max_length=1024,
            truncation=True
        )

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids,
                max_length=max_length,
                temperature=GENERATION_CONFIG.get("temperature", 0.7),
                num_beams=GENERATION_CONFIG.get("num_beams", 4),
                top_p=GENERATION_CONFIG.get("top_p", 0.9),
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )

        processing_time = time.time() - start_time
        return self._post_process_response(
            response, retrieval_result, processing_time, require_citations
        )

    def _generate_extractive(self, query: str, retrieval_result: RetrievalResult,
                            require_citations: bool) -> str:
        """Generate response using extractive summarization."""
        if not retrieval_result.results:
            return (
                "I could not find any relevant information in the accessible data sources "
                "to answer your question. This may be because the information is not "
                "available, or it may be restricted based on your access permissions."
            )

        # Build a structured response from the top retrieved documents
        response_parts = []
        top_results = retrieval_result.results[:3]

        # Extract the most relevant sentences from each top result
        for i, result in enumerate(top_results, 1):
            relevant_text = self._extract_relevant_sentences(
                result.chunk.text, query, max_sentences=3
            )
            if relevant_text:
                response_parts.append(relevant_text)

        # Combine into a response
        if response_parts:
            answer = " ".join(response_parts)
        else:
            # Fall back to using the full text of the top result
            answer = top_results[0].chunk.text[:500]

        return self._post_process_response(
            answer, retrieval_result, retrieval_result.processing_time, require_citations
        )

    def _extract_relevant_sentences(self, text: str, query: str, max_sentences: int = 3) -> str:
        """Extract sentences most relevant to the query."""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        if not sentences:
            return text[:500]

        # Score sentences by query term overlap
        query_terms = set(re.findall(r'\b\w{3,}\b', query.lower()))

        scored = []
        for sent in sentences:
            sent_terms = set(re.findall(r'\b\w{3,}\b', sent.lower()))
            overlap = len(query_terms & sent_terms)
            scored.append((overlap, sent))

        # Sort by score, take top sentences
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [s for _, s in scored[:max_sentences]]

        return " ".join(top)

    def _build_context(self, retrieval_result: RetrievalResult) -> str:
        """Build context from retrieved documents."""
        context_parts = []
        for i, result in enumerate(retrieval_result.results[:3]):
            context_parts.append(
                f"Source {i+1}: {result.document.title} "
                f"(Department: {result.document.department}, "
                f"Sensitivity: {result.document.sensitivity_level})\n"
                f"Content: {result.chunk.text}\n"
            )
        return "\n".join(context_parts)

    def _post_process_response(
        self,
        response: str,
        retrieval_result: RetrievalResult,
        processing_time: float,
        require_citations: bool
    ) -> str:
        """Post-process the generated response."""
        response = response.strip()

        if require_citations and retrieval_result.results:
            citations = retrieval_result.get_citations()[:3]
            response += "\n\n" + "\n".join(citations)

        info = f"\n\n[Processing time: {processing_time:.2f}s | Sources: {retrieval_result.total_count}]"
        response += info

        return response

    def calculate_confidence(self, query: str, retrieval_result: RetrievalResult) -> float:
        """Calculate confidence score for the response."""
        if not retrieval_result.results:
            return 0.0

        top_scores = [r.score for r in retrieval_result.results[:3]]
        avg_score = sum(top_scores) / len(top_scores) if top_scores else 0.0

        num_sources = len(retrieval_result.get_sources())
        if num_sources > 1:
            avg_score = min(avg_score + 0.1, 1.0)

        return round(avg_score, 2)

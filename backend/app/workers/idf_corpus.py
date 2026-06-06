"""
AI-Native IDF Learning Loop Corpus - Phase E: Intelligent Learning

Builds a corpus of job descriptions, candidate profiles, and assessment outcomes.
Calculates TF-IDF (Term Frequency-Inverse Document Frequency) statistics.
Enables domain-aware semantic scoring that improves over time.

Key concepts:
- Term frequency (TF): How often a term appears in a document
- Inverse document frequency (IDF): How rare/common a term is across corpus
- TF-IDF: Combined metric favoring rare, meaningful terms
- Corpus domain: Terms that are common in tech jobs are less discriminative
- Learning: As corpus grows, IDF scores refine and improve matching
"""
import json
import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class CorpusDocument:
    """Single document in IDF corpus (CV or JD)."""

    document_id: str
    doc_type: str  # 'cv' or 'jd'
    content: str  # Raw text
    terms: List[str]  # Tokenized terms
    assessment_outcome: Optional[str] = None  # hire, reject, review (for learning)
    performance_rating: Optional[float] = None  # Post-hire performance (0-1)
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()

    def term_count(self, term: str) -> int:
        """Get frequency of term in document."""
        return self.terms.count(term)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["term_count"] = len(self.terms)
        data["unique_terms"] = len(set(self.terms))
        return data


class IDFCorpus:
    """
    Inverse Document Frequency corpus for domain-aware semantic scoring.

    Learns from assessment outcomes to improve matching over time.
    """

    def __init__(self, min_term_length: int = 3):
        self.documents: Dict[str, CorpusDocument] = {}  # document_id -> doc
        self.cv_documents: List[str] = []  # CV document IDs
        self.jd_documents: List[str] = []  # JD document IDs
        self.min_term_length = min_term_length

        # IDF statistics
        self.idf_scores: Dict[str, float] = {}  # term -> idf score
        self.term_document_count: Dict[str, int] = {}  # term -> count of docs with term
        self.total_documents = 0

        # Learning from outcomes
        self.outcome_term_stats: Dict[str, Dict[str, float]] = {
            "hire": {},  # terms associated with hires
            "reject": {},  # terms associated with rejections
            "review": {},  # terms associated with reviews
        }

    def add_document(
        self,
        document_id: str,
        doc_type: str,  # 'cv' or 'jd'
        content: str,
        assessment_outcome: Optional[str] = None,
        performance_rating: Optional[float] = None,
    ) -> CorpusDocument:
        """
        Add document to corpus.

        If assessment_outcome provided, learns from hiring decision.
        """
        # Simple tokenization: lowercase, split on whitespace/punctuation
        terms = self._tokenize(content)

        doc = CorpusDocument(
            document_id=document_id,
            doc_type=doc_type,
            content=content,
            terms=terms,
            assessment_outcome=assessment_outcome,
            performance_rating=performance_rating,
        )

        self.documents[document_id] = doc
        if doc_type == "cv":
            self.cv_documents.append(document_id)
        else:
            self.jd_documents.append(document_id)

        # Update document count
        self.total_documents = len(self.documents)

        logger.info(
            f"Document added to corpus: {document_id}",
            extra={
                "doc_type": doc_type,
                "term_count": len(terms),
                "outcome": assessment_outcome,
            },
        )

        # Recalculate IDF scores
        self._update_idf_scores()

        # Record outcome term statistics
        if assessment_outcome:
            self._update_outcome_stats(assessment_outcome, terms)

        return doc

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split, filter short terms."""
        # Simple: lowercase and split on whitespace/punctuation
        import re

        tokens = re.findall(r"\b\w+\b", text.lower())
        # Filter out short terms and common stopwords
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "be",
        }
        return [t for t in tokens if len(t) >= self.min_term_length and t not in stopwords]

    def _update_idf_scores(self):
        """Recalculate IDF scores for all terms."""
        # Count documents containing each term
        term_doc_count = defaultdict(int)

        for doc in self.documents.values():
            unique_terms = set(doc.terms)
            for term in unique_terms:
                term_doc_count[term] += 1

        # Calculate IDF: log(total_docs / docs_with_term)
        self.term_document_count = dict(term_doc_count)
        self.idf_scores = {}

        for term, doc_count in term_doc_count.items():
            if doc_count > 0:
                # Add 1 to avoid division by zero
                idf = math.log((self.total_documents + 1) / (doc_count + 1))
                self.idf_scores[term] = idf

        logger.info(
            f"IDF scores updated: {len(self.idf_scores)} unique terms",
            extra={"corpus_size": self.total_documents},
        )

    def _update_outcome_stats(self, outcome: str, terms: List[str]):
        """Record which terms are associated with hiring outcomes."""
        if outcome not in self.outcome_term_stats:
            self.outcome_term_stats[outcome] = {}

        for term in set(terms):
            if term not in self.outcome_term_stats[outcome]:
                self.outcome_term_stats[outcome][term] = 0
            self.outcome_term_stats[outcome][term] += 1

    def calculate_tfidf(self, document_id: str, term: str) -> float:
        """
        Calculate TF-IDF score for a term in a document.

        TF-IDF = Term Frequency × Inverse Document Frequency
        """
        if document_id not in self.documents:
            return 0.0

        doc = self.documents[document_id]

        # Term frequency (raw count)
        tf = doc.term_count(term)
        if tf == 0:
            return 0.0

        # Inverse document frequency
        idf = self.idf_scores.get(term, 0.0)

        return tf * idf

    def get_document_tfidf_vector(self, document_id: str) -> Dict[str, float]:
        """
        Get TF-IDF vector for document.

        Returns all terms with their TF-IDF scores.
        """
        if document_id not in self.documents:
            return {}

        doc = self.documents[document_id]
        vector = {}

        for term in set(doc.terms):
            vector[term] = self.calculate_tfidf(document_id, term)

        return vector

    def cosine_similarity(self, doc1_id: str, doc2_id: str) -> float:
        """
        Calculate cosine similarity between two documents using TF-IDF vectors.

        Range: 0 (completely different) to 1 (identical)
        """
        vector1 = self.get_document_tfidf_vector(doc1_id)
        vector2 = self.get_document_tfidf_vector(doc2_id)

        if not vector1 or not vector2:
            return 0.0

        # Calculate dot product
        dot_product = 0.0
        for term in set(vector1.keys()) & set(vector2.keys()):
            dot_product += vector1[term] * vector2[term]

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(v**2 for v in vector1.values()))
        magnitude2 = math.sqrt(sum(v**2 for v in vector2.values()))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_outcome_bias(self, term: str) -> Dict[str, float]:
        """
        Get outcome bias for a term.

        Shows which outcomes (hire/reject/review) are associated with term.
        """
        total_occurrences = sum(
            count for count in self.outcome_term_stats.values()
            for count in count.values() if isinstance(count, (int, float))
        )
        wait_let_me_recalculate = sum(
            self.outcome_term_stats[outcome].get(term, 0)
            for outcome in self.outcome_term_stats
        )

        if wait_let_me_recalculate == 0:
            return {"hire": 0.0, "reject": 0.0, "review": 0.0}

        bias = {}
        for outcome in self.outcome_term_stats:
            count = self.outcome_term_stats[outcome].get(term, 0)
            bias[outcome] = count / wait_let_me_recalculate if wait_let_me_recalculate > 0 else 0.0

        return bias

    def find_similar_documents(
        self, document_id: str, doc_type: str, top_k: int = 5
    ) -> List[tuple[str, float]]:
        """
        Find top-K most similar documents in corpus.

        Useful for finding comparable CVs or similar JDs.
        """
        if document_id not in self.documents:
            return []

        # Filter to same document type
        candidate_docs = (
            self.jd_documents if doc_type == "jd" else self.cv_documents
        )

        similarities = []
        for other_id in candidate_docs:
            if other_id != document_id:
                sim = self.cosine_similarity(document_id, other_id)
                similarities.append((other_id, sim))

        # Sort by similarity, descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_corpus_stats(self) -> Dict[str, Any]:
        """Get corpus statistics."""
        total_terms = len(self.idf_scores)
        avg_terms_per_doc = (
            sum(len(doc.terms) for doc in self.documents.values())
            / len(self.documents)
            if self.documents
            else 0
        )

        outcome_counts = {
            outcome: len([d for d in self.documents.values() if d.assessment_outcome == outcome])
            for outcome in ["hire", "reject", "review"]
        }

        return {
            "total_documents": self.total_documents,
            "cv_documents": len(self.cv_documents),
            "jd_documents": len(self.jd_documents),
            "unique_terms": total_terms,
            "avg_terms_per_document": avg_terms_per_doc,
            "outcome_distribution": outcome_counts,
        }

    def get_important_terms(
        self, outcome: Optional[str] = None, top_k: int = 20
    ) -> List[tuple[str, float]]:
        """
        Get most important terms by IDF score.

        If outcome specified, get terms most associated with that outcome.
        """
        if outcome and outcome in self.outcome_term_stats:
            # Sort by outcome association
            terms = sorted(
                self.outcome_term_stats[outcome].items(),
                key=lambda x: x[1],
                reverse=True,
            )
            return terms[:top_k]
        else:
            # Sort by IDF score
            terms = sorted(
                self.idf_scores.items(), key=lambda x: x[1], reverse=True
            )
            return terms[:top_k]


# Global corpus instance
_corpus: Optional[IDFCorpus] = None


def get_idf_corpus() -> IDFCorpus:
    """Get or create IDF corpus."""
    global _corpus
    if _corpus is None:
        _corpus = IDFCorpus()
    return _corpus

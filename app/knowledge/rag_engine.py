"""
RAG Engine & Hybrid Search for Analytics Career Connect (ACC)
Combines TF-IDF vectorization, BM25 scoring, and entity-intent matching
for high-precision retrieval across documents and website data.
"""

import os
import re
import json
import math
from typing import List, Dict, Any, Tuple
from collections import Counter

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

class HybridRAGEngine:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.programs: List[Dict[str, Any]] = []
        self.company_profile: Dict[str, Any] = {}
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.idf: Dict[str, float] = {}
        self.vocabulary: set = set()
        self.load_data()
        self.build_index()

    def load_data(self):
        """Loads indexed chunks, programs catalog, and company profile."""
        kb_path = os.path.join(DATA_DIR, "knowledge_base.json")
        programs_path = os.path.join(DATA_DIR, "programs_catalog.json")
        profile_path = os.path.join(DATA_DIR, "company_profile.json")

        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)

        if os.path.exists(programs_path):
            with open(programs_path, "r", encoding="utf-8") as f:
                self.programs = json.load(f)

        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                self.company_profile = json.load(f)

    def tokenize(self, text: str) -> List[str]:
        """Normalizes and tokenizes text into lowercase words/terms."""
        text = text.lower()
        # Keep alphanumeric words and numbers
        tokens = re.findall(r'\b[a-z0-9_+#.-]+\b', text)
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'in', 'of', 'to',
            'for', 'with', 'by', 'about', 'as', 'into', 'like', 'through', 'after',
            'over', 'between', 'out', 'against', 'during', 'without', 'before', 'under',
            'around', 'among', 'this', 'that', 'these', 'those', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'but',
            'if', 'can', 'could', 'will', 'would', 'should', 'what', 'how', 'who', 'where'
        }
        return [t for t in tokens if t not in stop_words and len(t) > 1]

    def build_index(self):
        """Builds BM25 and TF-IDF index structures for in-memory retrieval."""
        if not self.chunks:
            return

        total_docs = len(self.chunks)
        doc_freqs: Dict[str, int] = {}
        self.doc_term_freqs = []
        self.doc_lengths = []

        for chunk in self.chunks:
            # Combine title, category, target_batch and content for rich representation
            full_text = f"{chunk.get('title', '')} {chunk.get('category', '')} {chunk.get('target_batch', '')} {chunk.get('content', '')}"
            tokens = self.tokenize(full_text)
            term_counts = Counter(tokens)
            self.doc_term_freqs.append(term_counts)
            self.doc_lengths.append(len(tokens))

            for term in set(tokens):
                doc_freqs[term] = doc_freqs.get(term, 0) + 1
                self.vocabulary.add(term)

        self.avg_doc_len = sum(self.doc_lengths) / max(1, total_docs)

        # Calculate BM25 IDF
        for term, df in doc_freqs.items():
            self.idf[term] = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """Hybrid search combining BM25 scoring with entity boost, intent filters, and optional single-document filtering."""
        query_tokens = self.tokenize(query)

        # Pre-filter candidate chunks if a specific source/document is requested
        candidate_indices = []
        if source_filter and source_filter.strip() and source_filter.lower() != 'all':
            s_filter = source_filter.strip().lower()
            for idx, c in enumerate(self.chunks):
                s_name = c.get('source_name', '').lower()
                s_title = c.get('title', '').lower()
                s_cat = c.get('category', '').lower()
                # Check for direct match or substring
                if s_filter in s_name or s_name in s_filter or s_filter in s_title or s_filter in s_cat:
                    candidate_indices.append(idx)
            # If no direct match, check if s_filter keywords match
            if not candidate_indices:
                keywords = [k for k in re.findall(r'\b\w+\b', s_filter) if len(k) > 2]
                for idx, c in enumerate(self.chunks):
                    text = (c.get('source_name', '') + ' ' + c.get('title', '')).lower()
                    if any(kw in text for kw in keywords):
                        candidate_indices.append(idx)
        else:
            candidate_indices = list(range(len(self.chunks)))

        if not candidate_indices:
            candidate_indices = list(range(len(self.chunks)))

        if not query_tokens:
            # Return top chunks from candidate indices
            return [dict(self.chunks[i], relevance_score=1.0) for i in candidate_indices[:top_k]]

        # Entity boost patterns
        query_lower = query.lower()
        key_entities = {
            '2026': ['2026', 'graduates', 'datayug', 'placement'],
            '2027': ['2027', 'college', 'students', 'internship'],
            '2028': ['2028', 'college', 'students', 'internship'],
            '2029': ['2029', 'college', 'students', 'internship'],
            'scam': ['scam', 'fee', 'charge', 'free', 'money', 'alert'],
            'founder': ['wasim', 'patwari', 'sadaf', 'khan', 'founder', 'ceo'],
            'marketing': ['marketing', 'growth', 'social', 'content', 'outreach'],
            'datayug': ['datayug', 'option 1', 'option 2', 'option 3'],
            'stipend': ['stipend', '5k', '10k', 'unpaid', 'performance', 'incentives'],
            'power bi': ['power bi', 'dax', 'dashboard', 'visualization'],
            'sql': ['sql', 'queries', 'joins', 'window functions'],
            'python': ['python', 'pandas', 'numpy', 'matplotlib']
        }

        entity_matches = set()
        for ent, related in key_entities.items():
            if ent in query_lower:
                entity_matches.update(related)

        # BM25 Parameters
        k1 = 1.5
        b = 0.75
        scores: List[Tuple[int, float]] = []

        for idx in candidate_indices:
            term_counts = self.doc_term_freqs[idx]
            doc_len = self.doc_lengths[idx]
            score = 0.0
            for token in query_tokens:
                if token in term_counts:
                    tf = term_counts[token]
                    idf = self.idf.get(token, 0.5)
                    numerator = tf * (k1 + 1.0)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                    score += idf * (numerator / denominator)

            # Boost for entity matches in chunk title/content
            chunk_content = (self.chunks[idx].get('content', '') + ' ' + self.chunks[idx].get('title', '')).lower()
            for em in entity_matches:
                if em in chunk_content:
                    score += 1.8

            # Extra boost for exact phrase match
            if len(query.split()) > 1 and query_lower in chunk_content:
                score += 4.0

            # Base relevance if filtered to a specific document
            if source_filter and source_filter.lower() != 'all':
                score += 0.5

            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        if scores:
            for idx, score in scores[:top_k]:
                item = dict(self.chunks[idx])
                item['relevance_score'] = round(score, 3)
                results.append(item)
        elif candidate_indices:
            # Fallback for single document search if no direct BM25 hits
            for idx in candidate_indices[:top_k]:
                item = dict(self.chunks[idx])
                item['relevance_score'] = 0.5
                results.append(item)

        return results

    def get_program_by_batch(self, batch_year: int) -> List[Dict[str, Any]]:
        """Returns program recommendations based on user's graduation batch year."""
        matched = []
        for prog in self.programs:
            if batch_year <= 2026:
                if "2026" in prog["batch"] or "All" in prog["batch"]:
                    matched.append(prog)
            else:
                if str(batch_year) in prog["batch"] or "College Students" in prog["batch"] or "All" in prog["batch"]:
                    matched.append(prog)
        return matched

    def get_all_programs(self) -> List[Dict[str, Any]]:
        """Returns the full catalog of ACC programs."""
        return self.programs

    def get_company_profile(self) -> Dict[str, Any]:
        """Returns verified company information."""
        return self.company_profile

# Global engine instance
rag_engine = HybridRAGEngine()

from typing import List, Dict
from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.term import Term
import math


class BM25FScoringFunction:
    def __init__(self, k1: float = 1.5, b: float = 0.75, field_weights: Dict[str, float] = None, index=None):
        self.k1 = k1
        self.b = b
        self.index = index
        self.field_weights = field_weights or {'title': 2.0, 'body': 1.0, 'author': 0.5}
        self.postings_dict = {}

    def _build_postings_dict(self, postings: List[Posting]):
        for posting in postings:
            if posting.term_id not in self.postings_dict:
                self.postings_dict[posting.term_id] = []
            self.postings_dict[posting.term_id].append(posting)

    def __call__(self, document: DocumentInfo, postings: List[Posting], query: List[Term]) -> float:
        self._build_postings_dict(postings)
        score = 0.0
        for term in query:
            if term.id in self.postings_dict:
                score += self._rsv(term, document)
        return round(score, 4)  # Round to 4 decimals for reproducibility

    def _rsv(self, term: Term, document: DocumentInfo) -> float:
        tfd = self._wtf(term, document)
        
        if tfd > 0:
            return (tfd / (self.k1 + tfd)) * math.log(term.info['idf'])
        return 0.0

    def _wtf(self, term: Term, document: DocumentInfo) -> float:
        tfd = 0.0
        field_indices = {"author": 0, "title": 1, "body": 2}

        if term.id not in self.postings_dict:
            return 0.0

        for posting in self.postings_dict[term.id]:
            if posting.doc_id == document.id:
                for field, weight in self.field_weights.items():
                    field_index = field_indices[field]
                    avg_dlf = self.index.get_global_info()['avg_field_lengths'][field]
                    bb = 1 - self.b + self.b * document.lengths[field_index] / avg_dlf
                    tf = len(posting.occurrences.get(field, []))
                    tfd += weight * tf / bb
        return tfd

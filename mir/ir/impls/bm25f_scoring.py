from typing import List, Dict
from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.scoring_function import ScoringFunction
from mir.ir.term import Term
import math


class BM25FScoringFunction(ScoringFunction):
    def __init__(self, k1: float = 1.5, b: float = 0.75, field_weights: Dict[str, float] = None):
        self.k1 = k1
        self.b = b
        self.field_weights = field_weights if field_weights is not None else {'title': 2.0, 'body': 1.0, 'author': 0.5}

    def _build_postings_dict(self, postings: List[Posting]) -> Dict[int, Posting]:
        return {posting.term_id: posting for posting in postings}

    def __call__(self, document: DocumentInfo, postings: List[Posting], query: List[Term], *, num_docs: int, avg_field_lengths: dict[str, int], **_) -> float:
        postings_dict = self._build_postings_dict(postings)
        score = 0.0
        for term in query:
            if term.id in postings_dict:
                score += self._rsv(term, document, num_docs, postings_dict, avg_field_lengths)
        return score

    def _rsv(self, term: Term, document: DocumentInfo, num_docs: int, postings_dict: dict[int, Posting], avg_field_lengths: dict[str, int]) -> float:
        tfd = self._wtf(term, document, postings_dict, avg_field_lengths)
        
        if tfd > 0:
            return (tfd / (self.k1 + tfd)) * math.log(term.info['posting_list_len'] / num_docs)
        return 0.0

    def _wtf(self, term: Term, document: DocumentInfo, postings_dict: dict[int, Posting], avg_field_lengths: dict[str, int]) -> float:
        tfd = 0.0
        field_indices = {"author": 0, "title": 1, "body": 2}

        if term.id not in postings_dict:
            return 0.0

        posting = postings_dict[term.id]
        for field, weight in self.field_weights.items():
            field_index = field_indices[field]
            avg_dlf = avg_field_lengths[field]
            bb = 1 - self.b + self.b * document.lengths[field_index] / avg_dlf
            tf = posting.occurrences.get(field, 0)
            tfd += weight * tf / bb

        return tfd

import math
import unittest
from unittest.mock import MagicMock
from typing import List, Dict, Literal
from mir.ir.document_info import DocumentInfo
from mir.ir.impls.bm25f_scoring import BM25FScoringFunction
from mir.ir.posting import Posting
from mir.ir.term import Term


class TestBM25FScoringFunction(unittest.TestCase):
    def setUp(self):
        # Mock data
        self.document = DocumentInfo(id=1, lengths=[100, 200, 300])  # Example document with field lengths
        self.postings = [
            Posting(term_id=1, doc_id=1, occurrences={"title": 2, "body": 1}),
            Posting(term_id=2, doc_id=1, occurrences={"body": 2})
        ]
        self.query = [Term(term="term1", id=1, posting_list_len=6), Term(term="term2", id=2, posting_list_len=3)]
        
        # Mock index
        self.index_mock = MagicMock()
        self.index_mock.get_global_info.return_value = {
            "avg_field_lengths": {"title": 150, "body": 250, "author": 50},
            "num_docs": 2
        }
        
        # Initialize BM25F
        self.bm25f = BM25FScoringFunction(
            k1=1.2,
            b=0.8,
            field_weights={'title': 1.5, 'body': 1.0},
        )


        # how to not make a test, please never do this, I reimplemented the whole feature
        self.expected_value = 0.0
        len_index = {"author": 0, "title": 1, "body": 2}
        postings_lookup = {p.term_id: p for p in self.postings}
        for q in self.query:
            idf = math.log(q.info["posting_list_len"] / self.index_mock.get_global_info()["num_docs"])
            p = postings_lookup.get(q.id)
            tf = 0
            for field, o in p.occurrences.items():
                tf += o * self.bm25f.field_weights[field] /\
                    ((1-self.bm25f.b) + self.bm25f.b * self.document.lengths[len_index[field]] / self.index_mock.get_global_info()["avg_field_lengths"][field])
            self.expected_value += idf * (tf / (self.bm25f.k1 + tf))

    def test_bm25f_score(self):
        # Run BM25F scoring
        score = self.bm25f(self.document, self.postings, self.query, **self.index_mock.get_global_info())
        
        # Expected result (replace with the actual expected value after computation)
        self.assertAlmostEqual(score, self.expected_value, places=4)


if __name__ == "__main__":
    unittest.main()

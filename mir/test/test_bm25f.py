import unittest
from unittest.mock import MagicMock
from typing import List, Dict
from mir.ir.document_info import DocumentInfo
from mir.ir.impls.bm25f_scoring import BM25FScoringFunction
from mir.ir.posting import Posting
from mir.ir.term import Term
import math


class TestBM25FScoringFunction(unittest.TestCase):
    def setUp(self):
        # Mock data
        self.document = DocumentInfo(id=1, lengths=[100, 200, 300])  # Example document with field lengths
        self.postings = [
            Posting(term_id=1, doc_id=1, occurrences={"title": 2, "body": 1}),
            Posting(term_id=2, doc_id=1, occurrences={"body": 2})
        ]
        self.query = [Term(term="term1", id=1, idf=2.0), Term(term="term2", id=2, idf=1.5)]
        
        # Mock index
        self.index_mock = MagicMock()
        self.index_mock.get_global_info.return_value = {
            "avg_field_lengths": {"title": 150, "body": 250, "author": 50}
        }
        
        # Initialize BM25F
        self.bm25f = BM25FScoringFunction(
            k1=1.2,
            b=0.8,
            field_weights={'title': 1.5, 'body': 1.0},
            index=self.index_mock
        )

    def test_bm25f_score(self):
        # Run BM25F scoring
        score = self.bm25f(self.document, self.postings, self.query)
        
        # Print intermediate values (optional, for debug)
        print(f"Final BM25F Score: {score}")
        
        # Expected result (replace with the actual expected value after computation)
        expected_score = 0.7445  # Replace with the correct score
        self.assertAlmostEqual(score, expected_score, places=4)

    def test_postings_dict_building(self):
        # Test if postings dictionary is built correctly
        self.bm25f._build_postings_dict(self.postings)
        self.assertIn(1, self.bm25f.postings_dict)
        self.assertIn(2, self.bm25f.postings_dict)
        self.assertEqual(len(self.bm25f.postings_dict[1]), 1)
        self.assertEqual(len(self.bm25f.postings_dict[2]), 1)


if __name__ == "__main__":
    unittest.main()

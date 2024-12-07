import unittest
from collections import OrderedDict
from unittest.mock import MagicMock
from mir.ir.document_info import DocumentInfo
from mir.ir.document_contents import DocumentContents
from mir.ir.serializable.posting_list import PostingList
from mir.ir.token_ir import Token, TokenLocation
from mir.ir.impls.core_index import CoreIndex
from mir.ir.tokenizer import Tokenizer
from mir.ir.posting import Posting
from mir.ir.term import Term

from mir.test.core_index_test_utils import setup_teardown_folder


class TestCoreIndex(unittest.TestCase):

    @setup_teardown_folder
    def test_index_document(self, test_folder):
        self.index = CoreIndex(test_folder)
        # Mock document
        doc = MagicMock(spec=DocumentContents)
        doc.doc_id = 0
        tokenizer = MagicMock(spec=Tokenizer)
        
        # Mock tokenized terms
        tokens = [
            Token("author_term", TokenLocation.AUTHOR, 0),
            Token("title_term", TokenLocation.TITLE, 0),
            Token("body_term", TokenLocation.BODY, 0),
        ]
        tokenizer.tokenize_document.return_value = tokens

        # Indicizza documento
        self.index.index_document(doc, tokenizer)

        # Test document_info e contents
        self.assertEqual(self.index.document_info.next_key(), 1)
        self.assertEqual(self.index.document_contents.next_key(), 1)

        # Test termini indicizzati
        self.assertEqual(self.index.terms.next_key(), 3)
        self.assertIn("author_term", self.index.term_lookup)
        self.assertIn("title_term", self.index.term_lookup)
        self.assertIn("body_term", self.index.term_lookup)

    @setup_teardown_folder
    def test_map_terms_to_ids(self, test_folder):
        self.index = CoreIndex(test_folder)

        # Mock tokens
        tokens = [
            Token("term1", TokenLocation.BODY, 0),
            Token("term2", TokenLocation.TITLE, 1),
            Token("term1", TokenLocation.AUTHOR, 2),
        ]

        # Map terms to IDs
        term_ids = self.index._map_terms_to_ids(tokens)

        # Test ID mapping
        self.assertEqual(self.index.terms.next_key(), 2)
        self.assertEqual(self.index.term_lookup["term1"], term_ids[0])
        self.assertEqual(self.index.term_lookup["term2"], term_ids[1])

    @setup_teardown_folder
    def test_compute_avg_field_lengths(self, test_folder):
        self.index = CoreIndex(test_folder)

        # Mock document info
        doc1 = DocumentInfo(id=0, lengths=[5, 10, 20])
        doc2 = DocumentInfo(id=1, lengths=[10, 15, 25])

        self.index.global_info["num_docs"] = 2
        self.index._sum_up_lengths(doc1.lengths)
        self.index._sum_up_lengths(doc2.lengths)

        # Compute averages
        avg_lengths = self.index._compute_avg_field_lengths()

        # Expected values
        expected = {
            "author": 7.5,  # (5+10)/2
            "title": 12.5,  # (10+15)/2
            "body": 22.5    # (20+25)/2
        }

        self.assertEqual(avg_lengths, expected)

    @setup_teardown_folder
    def test_get_postings(self, test_folder):
        self.index = CoreIndex(test_folder)
        
        # Mock postings
        posting1 = Posting(doc_id=0, term_id=0)
        posting2 = Posting(doc_id=1, term_id=0)
        posting_list = PostingList()
        posting_list[0] = posting1
        posting_list[1] = posting2
        self.index.postings.append(posting_list)

        # Test retrieval
        postings = list(self.index.get_postings(0))
        self.assertEqual(len(postings), 2)
        self.assertEqual(postings[0].doc_id, 0)
        self.assertEqual(postings[1].doc_id, 1)

    @setup_teardown_folder
    def test_get_term_id(self, test_folder):
        self.index = CoreIndex(test_folder)
        # Mock term lookup
        self.index.term_lookup["term1"] = 0
        self.index.term_lookup["term2"] = 1

        # Test term ID retrieval
        self.assertEqual(self.index.get_term_id("term1"), 0)
        self.assertEqual(self.index.get_term_id("term2"), 1)
        self.assertIsNone(self.index.get_term_id("term3"))

    @setup_teardown_folder
    def test_bulk_index_documents(self, test_folder):
        self.index = CoreIndex(test_folder)
        # Mock documents
        docs = [
            MagicMock(spec=DocumentContents),
            MagicMock(spec=DocumentContents)
        ]
        tokenizer = MagicMock(spec=Tokenizer)

        # Mock tokens for both documents
        tokens = [
            Token("term1", TokenLocation.AUTHOR, 0),
            Token("term2", TokenLocation.TITLE, 1),
            Token("term3", TokenLocation.BODY, 2),
        ]
        tokenizer.tokenize_document.side_effect = lambda doc: tokens

        # Bulk index documents
        self.index.bulk_index_documents(docs, tokenizer)

        # Test document count
        self.assertEqual(self.index.global_info['num_docs'], 2)

        # Test global info
        self.assertIn("avg_field_lengths", self.index.global_info)
        self.assertEqual(self.index.terms.next_key(), 3)

    @setup_teardown_folder
    def test_get_global_info(self, test_folder):
        self.index = CoreIndex(test_folder)
        # Mock global info
        self.index.global_info = {"avg_field_lengths": {"author": 5, "title": 10, "body": 15}}

        # Test retrieval
        global_info = self.index.get_global_info()
        self.assertIn("avg_field_lengths", global_info)
        self.assertEqual(global_info["avg_field_lengths"]["author"], 5)

    @setup_teardown_folder
    def test_exceptions_invalid_location(self, test_folder):
        self.index = CoreIndex(test_folder)
        # Mock invalid token location
        tokens = [Token("term1", "INVALID_LOCATION", 0)]

        # Test exception
        with self.assertRaises(ValueError):
            self.index._group_terms(tokens)


if __name__ == "__main__":
    unittest.main()

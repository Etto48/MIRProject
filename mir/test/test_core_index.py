import unittest
from collections import OrderedDict
from unittest.mock import MagicMock
from mir import DATA_DIR
from mir.ir.document_info import DocumentInfo
from mir.ir.document_contents import DocumentContents
from mir.ir.serializable.posting_list import PostingList
from mir.ir.token_ir import Token, TokenLocation
from mir.ir.impls.core_index import CoreIndex
from mir.ir.tokenizer import Tokenizer
from mir.ir.posting import Posting
from mir.ir.term import Term

import os
import shutil


class TestCoreIndex(unittest.TestCase):

    def setUp(self):
        self.test_folder = f"{DATA_DIR}/test/"
        # Ensure the test folder is clean before each test
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
        os.makedirs(self.test_folder)

    def tearDown(self):
        # Clean up the test folder after each test
        shutil.rmtree(self.test_folder)
        os.makedirs(self.test_folder)

    def test_index_document(self):
        index = CoreIndex(self.test_folder)
        # Mock document
        #doc = MagicMock(spec=DocumentContents)
        doc = DocumentContents('author', 'title', 'body')
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
        index.index_document(doc, tokenizer)

        # Test document_info e contents
        self.assertEqual(index.document_info.next_key(), 1)
        self.assertEqual(index.document_contents.next_key(), 1)

        # Test termini indicizzati
        self.assertEqual(index.terms.next_key(), 3)

    def test_map_terms_to_ids(self):
        index = CoreIndex(self.test_folder)

        # Mock tokens
        tokens = [
            Token("term1", TokenLocation.BODY, 0),
            Token("term2", TokenLocation.TITLE, 1),
            Token("term1", TokenLocation.AUTHOR, 2),
        ]

        # Map terms to IDs
        term_ids = index._map_terms_to_ids(tokens)

        # Test ID mapping
        self.assertEqual(index.terms.next_key(), 2)
        self.assertEqual(index.term_lookup["term1"], term_ids[0])
        self.assertEqual(index.term_lookup["term2"], term_ids[1])

    def test_get_postings(self):
        index = CoreIndex(self.test_folder)
        
        # Mock postings
        posting1 = Posting(doc_id=0, term_id=0)
        posting2 = Posting(doc_id=1, term_id=0)
        posting_list = PostingList()
        posting_list[0] = posting1
        posting_list[1] = posting2
        index.postings.append(posting_list)

        # Test retrieval
        postings = list(index.get_postings(0))
        self.assertEqual(len(postings), 2)
        self.assertEqual(postings[0].doc_id, 0)
        self.assertEqual(postings[1].doc_id, 1)

    def test_get_term_id(self):
        index = CoreIndex(self.test_folder)
        # Mock term lookup
        index.term_lookup["term1"] = 0
        index.term_lookup["term2"] = 1

        # Test term ID retrieval
        self.assertEqual(index.get_term_id("term1"), 0)
        self.assertEqual(index.get_term_id("term2"), 1)
        self.assertIsNone(index.get_term_id("term3"))

    def test_bulk_index_documents(self):
        index = CoreIndex(self.test_folder)
        # Mock documents
        docs = [
            DocumentContents('author1', 'title1', 'body1'),
            DocumentContents('author2', 'title2', 'body2'),
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
        index.bulk_index_documents(docs, tokenizer)

        # Test document count
        self.assertEqual(index.global_info['num_docs'], 2)

        # Test global info
        self.assertIn("field_lengths", index.global_info)
        self.assertEqual(index.terms.next_key(), 3)

    def test_get_global_info(self):
        index = CoreIndex(self.test_folder)
        # Mock global info
        index.global_info = {"field_lengths": {"author": 5, "title": 10, "body": 15}, "num_docs": 1}

        # Test retrieval
        global_info = index.get_global_info()
        self.assertIn("avg_field_lengths", global_info)
        self.assertEqual(global_info["avg_field_lengths"]["author"], 5)

    def test_exceptions_invalid_location(self):
        index = CoreIndex(self.test_folder)
        # Mock invalid token location
        tokens = [Token("term1", "INVALID_LOCATION", 0)]

        # Test exception
        with self.assertRaises(ValueError):
            index._group_terms(tokens)

    def test_save_load(self):
        index = CoreIndex(self.test_folder)
        # Mock index
        index.global_info["field_lengths"]= {"author": 5, "title": 10, "body": 15}
        index.global_info["num_docs"] = 1
        index.document_info.append(DocumentInfo(id=0, lengths=[5, 10, 15]))
        index.document_contents.append(DocumentContents('author', 'title', 'body'))
        index.terms.append(Term("term1", 0))
        index.term_lookup["term1"] = 0
        index.postings.append(PostingList())

        # Save index
        index.save()

        # Load index
        loaded_index = CoreIndex(self.test_folder)

        # Test loaded index
        self.assertEqual(loaded_index.global_info, index.global_info)
        self.assertEqual(loaded_index.document_info.next_key(), 1)
        self.assertEqual(loaded_index.document_contents.next_key(), 1)
        self.assertEqual(loaded_index.terms.next_key(), 1)
        self.assertEqual(loaded_index.term_lookup["term1"], 0)
        self.assertEqual(loaded_index.postings.next_key(), 1)


if __name__ == "__main__":
    unittest.main()

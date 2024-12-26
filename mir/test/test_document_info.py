import unittest
from mir.ir.document_info import DocumentInfo

class TestDocumentInfo(unittest.TestCase):
    def test_document_info_initialization(self):
        doc_info = DocumentInfo(1, [2, 3, 5])
        self.assertEqual(doc_info.id, 1)
        self.assertEqual(doc_info.lengths, [2, 3, 5])

    def test_document_info_invalid_lengths(self):
        with self.assertRaises(AssertionError):
            DocumentInfo(1, [2, 3])


if __name__ == '__main__':
    unittest.main()
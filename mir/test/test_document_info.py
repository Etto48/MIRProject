import unittest
from mir.ir.document_info import DOCUMENT_INFO_SERDE, DocumentInfo

class TestDocumentInfo(unittest.TestCase):
    def test_document_info_initialization(self):
        doc_info = DocumentInfo(1, [2, 3, 5])
        self.assertEqual(doc_info.id, 1)
        self.assertEqual(doc_info.lengths, [2, 3, 5])

    def test_document_info_invalid_lengths(self):
        with self.assertRaises(AssertionError):
            DocumentInfo(1, [2, 3])

    def test_serialization(self):
        doc_info = DocumentInfo(1, [2, 3, 5])
        serialized = doc_info.__ser__()
        deserialized = DocumentInfo.__deser__(serialized, 1)
        self.assertEqual(deserialized.id, doc_info.id)
        self.assertEqual(deserialized.lengths, doc_info.lengths)

    def test_serde(self):
        doc_info = DocumentInfo(1, [2, 3, 5])
        serialized = DOCUMENT_INFO_SERDE.serialize(doc_info)
        deserialized = DOCUMENT_INFO_SERDE.deserialize(serialized, doc_info.id)
        self.assertEqual(deserialized.id, doc_info.id)
        self.assertEqual(deserialized.lengths, doc_info.lengths)

if __name__ == '__main__':
    unittest.main()
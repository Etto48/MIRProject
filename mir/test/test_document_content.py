import unittest

from mir.ir.document_contents import DOCUMENT_CONTENTS_SERDE, DocumentContents

class TestDocumentContentSerialization(unittest.TestCase):

    def setUp(self):
        self.document_content = DocumentContents(
            'John Doe', 
            'Sample Document', 
            'This is a sample document for testing serialization.'
        )

    def test_document_content_serialization(self):
        serialized = self.document_content.__ser__()
        self.assertIsInstance(serialized, bytes)
    
    def test_document_content_deserialization(self):
        serialized = self.document_content.__ser__()
        deserialized = DocumentContents.__deser__(serialized)
        self.assertEqual(deserialized.title, self.document_content.title)
        self.assertEqual(deserialized.author, self.document_content.author)
        self.assertEqual(deserialized.body, self.document_content.body)

    def test_document_content_serde(self):
        serialized = DOCUMENT_CONTENTS_SERDE.serialize(self.document_content)
        deserialized = DOCUMENT_CONTENTS_SERDE.deserialize(serialized, 1)
        self.assertEqual(deserialized.title, self.document_content.title)
        self.assertEqual(deserialized.author, self.document_content.author)
        self.assertEqual(deserialized.body, self.document_content.body)

if __name__ == '__main__':
    unittest.main()
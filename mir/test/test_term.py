import unittest
from mir.ir.term import Term, TERM_SERDE

class TestTerm(unittest.TestCase):
    def setUp(self):
        self.term = Term("example", 1, idf=10)

    def test_term_initialization(self):
        self.assertEqual(self.term.term, "example")
        self.assertEqual(self.term.id, 1)
        self.assertEqual(self.term.info['idf'], 10)

    def test_term_serialization(self):
        serialized = self.term.__ser__()
        self.assertIsInstance(serialized, bytes)

    def test_term_deserialization(self):
        serialized = self.term.__ser__()
        deserialized = Term.__deser__(serialized, 1)
        self.assertEqual(deserialized.term, "example")
        self.assertEqual(deserialized.id, 1)
        self.assertEqual(deserialized.info['idf'], 10)

    def test_term_serde(self):
        serialized = TERM_SERDE.serialize(self.term)
        deserialized = TERM_SERDE.deserialize(serialized, 1)
        self.assertEqual(deserialized.term, "example")
        self.assertEqual(deserialized.id, 1)
        self.assertEqual(deserialized.info['idf'], 10)

if __name__ == '__main__':
    unittest.main()
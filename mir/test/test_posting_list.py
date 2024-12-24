import unittest
from mir.ir.serializable.posting_list import PostingList, POSTING_LIST_SERDE
from mir.ir.posting import Posting

class TestPostingList(unittest.TestCase):
    def setUp(self):
        self.posting_list = PostingList()
        self.posting_list[1] = Posting(term_id=1, doc_id=1)
        self.posting_list[2] = Posting(term_id=1, doc_id=2)
        self.posting_list[5] = Posting(term_id=1, doc_id=5)
        self.posting_list[6] = Posting(term_id=1, doc_id=6)

        self.posting_list[1].occurrences["author"] = 1
        self.posting_list[1].occurrences["title"] = 2
        self.posting_list[1].occurrences["body"] = 3

        self.posting_list[2].occurrences["author"] = 4
        self.posting_list[2].occurrences["title"] = 5
        self.posting_list[2].occurrences["body"] = 6

        self.posting_list[5].occurrences["author"] = 7
        self.posting_list[5].occurrences["title"] = 8
        self.posting_list[5].occurrences["body"] = 9

        self.posting_list[6].occurrences["author"] = 10
        self.posting_list[6].occurrences["title"] = 11
        self.posting_list[6].occurrences["body"] = 12

    def test_serialization(self):
        serialized_data = POSTING_LIST_SERDE.serialize(self.posting_list)
        self.assertIsInstance(serialized_data, bytes)

    def test_deserialization(self):
        serialized_data = POSTING_LIST_SERDE.serialize(self.posting_list)
        print(serialized_data)
        deserialized_posting_list = POSTING_LIST_SERDE.deserialize(serialized_data, term_id=1)
        self.assertEqual(len(deserialized_posting_list), len(self.posting_list))
        for doc_id, posting in self.posting_list.items():
            self.assertIn(doc_id, deserialized_posting_list)
            self.assertEqual(posting.term_id, deserialized_posting_list[doc_id].term_id)
            self.assertEqual(posting.doc_id, deserialized_posting_list[doc_id].doc_id)
            self.assertEqual(posting.occurrences, deserialized_posting_list[doc_id].occurrences)

if __name__ == '__main__':
    unittest.main()
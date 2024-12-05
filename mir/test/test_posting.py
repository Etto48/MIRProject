import unittest
from mir.ir.posting import Posting

class TestPosting(unittest.TestCase):
    def test_serde(self):
        posting = Posting(doc_id=1, term_id=2)
        posting.occurrences["author"] = [1, 2, 3]
        posting.occurrences["title"] = [4, 5]
        posting.occurrences["body"] = [6]

        serialized = posting.__ser__()
        deserialize,_ = Posting.__deser__(serialized, 2, 1)

        self.assertEqual(posting.occurrences, deserialize.occurrences)

if __name__ == '__main__':
    unittest.main()
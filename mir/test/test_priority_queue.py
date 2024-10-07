import unittest
import random

from mir.ir.priority_queue import PriorityQueue

class TestPriorityQueue(unittest.TestCase):       
    def test_priority_queue(self):
        pq = PriorityQueue(5)
        items = [(0, 0.0), (1, 0.1), (2, 0.2), (3, 0.3), (4, 0.4), (5, 0.5), (6, 0.6)]
        order = random.sample(range(len(items)), len(items))
        items.sort(key=lambda x: order[x[0]])
        for doc_id, score in items:
            pq.push(doc_id, score)
        items.sort(key=lambda x: -x[1])
        pq.finalise()
        for (true_doc_id, true_score), (score, doc_id) in zip(items[:5], pq):
            self.assertEqual((true_doc_id, true_score), (doc_id, score))
        self.assertEqual(len(pq), 5)

if __name__ == "__main__":
    unittest.main()
import unittest

import numpy as np
import argparse
from mir.utils.query_matching import find_best_path


class TestQueryMatching(unittest.TestCase): 
    def test_best_path(self) :
        posting_lists = [[2,5,7,13],[1,14,15],[10,12,17,23]]
        deltas = np.array([2,7])
        expected_result = np.array([13,15,23])
        self.assertEqual(find_best_path(posting_lists, deltas)[0].all(), expected_result.all())


if __name__ == '__main__':
   unittest.main()
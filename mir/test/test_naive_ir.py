import unittest

import pandas as pd

from mir.ir.impls.naive_ir import NaiveIr
from mir.utils.dataset import get_dataset, dataset_to_contents


class TestNaiveIr(unittest.TestCase):
    def test_naive_ir(self):
        ir = NaiveIr()
        if len(ir) == 0:
            dataset = get_dataset(verbose=True)
            ir.bulk_index_documents(dataset_to_contents(dataset), verbose=True)
        queries = [
            "i'll never gonna dance again",
            "i dub thee unforgiven",
            "on the boulevard of broken dreams",
            "i'm a creep",
            "karma police",
        ]

        queries_df = pd.DataFrame({
            "query_id": range(len(queries)),
            "text": queries
        })

        run = ir.get_run(queries_df, verbose=True)


import os
import unittest

import pandas as pd

from mir import DATA_DIR
from mir.ir.impls.default_index import DefaultIndex
from mir.ir.ir import Ir
from mir.utils.dataset import dataset_to_contents, get_subdataset


class TestNaiveIr(unittest.TestCase):
    def test_naive_ir(self):
        path = f"{DATA_DIR}/naive_ir.pkl"
        ir = Ir(index=DefaultIndex(path))
        amount = 100
        if len(ir) != amount:
            if os.path.exists(path):
                os.remove(path)
            ir = Ir(index=DefaultIndex(path))
            dataset = get_subdataset(verbose=False, amount=amount, seed=42)
            ir.bulk_index_documents(dataset_to_contents(dataset), verbose=False)
        queries = [
            "can't you feel it?",
            "check this out",
            "first broken heart",
            "spend the night",
        ]

        queries_df = pd.DataFrame({
            "query_id": range(len(queries)),
            "text": queries
        })

        run = ir.get_run(queries_df, verbose=False)


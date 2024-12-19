import os
import shutil
import unittest

import pandas as pd

from mir import DATA_DIR
from mir.ir.impls.core_index import CoreIndex
from mir.ir.ir import Ir
from mir.utils.dataset import dataset_to_contents, get_subdataset


class TestCoreIr(unittest.TestCase):

    def setUp(self):
        self.test_folder = f"{DATA_DIR}/test/"
        # Ensure the test folder is clean before each test
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
        os.makedirs(self.test_folder)

    def tearDown(self):
        # Clean up the test folder after each test
        shutil.rmtree(self.test_folder)
        os.makedirs(self.test_folder)

    def test_core_ir(self):
        ir = Ir(index=CoreIndex(self.test_folder))
        amount = 100
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


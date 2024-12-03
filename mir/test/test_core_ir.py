import os
import unittest

import pandas as pd

from mir import DATA_DIR
from mir.ir.document_info import DocumentInfo
from mir.ir.impls.core_index import CoreIndex
from mir.ir.ir import Ir
from mir.ir.tokenizer import Tokenizer
from mir.utils.dataset import dataset_to_contents, get_subdataset


class TestCoreIr(unittest.TestCase):
    def test_core_ir(self):
        index = CoreIndex()
        ir = Ir(index=index)
        amount = 1
        dataset = get_subdataset(verbose=False, amount=amount, seed=42)
        content = dataset_to_contents(dataset) 
        for doc in content:
            print(doc.title)
            print(doc.author)
            info = DocumentInfo.from_document_contents(None, doc, ir.tokenizer)
            print(info.lengths)
        ir.bulk_index_documents(dataset_to_contents(dataset), verbose=False)

        index = ir.index

        print(type(index))

        print(len(index.terms))
        for i, term in enumerate(index.terms):
            print(i, term.term, end=" ")
        print('')
        
        print(len(index.postings))
        for posting in index.postings:
            print(posting)

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


import os
import re
import pyterrier as pt
from pyterrier import IndexFactory
import pandas as pd
from tqdm.auto import tqdm

from mir import DATA_DIR
from mir.ir.impls.bm25f_scoring import BM25FScoringFunction
from mir.ir.impls.core_index import CoreIndex
from mir.ir.impls.neural_scoring_function import NeuralScoringFunction
from mir.ir.impls.sqlite_index import SqliteIndex
from mir.ir.ir import Ir
from mir.utils.dataset import get_msmarco_dataset, test_dataset_to_contents


def test_pyterrier():
    get_msmarco_dataset()
    dataset_csv = f"{DATA_DIR}/msmarco/collection.tsv"
    indexer = pt.terrier.IterDictIndexer(f"{DATA_DIR}/msmarco-pyterrier-index")
    index_path = f"{DATA_DIR}/msmarco-pyterrier-index/data.properties"
    if not os.path.exists(index_path):
        dataset = pd.read_csv(dataset_csv, sep='\t', header=None, names=['docno', 'text'], dtype={'docno': str, 'text': str})
        indexref = indexer.index(tqdm(dataset.to_dict(orient='records'), desc="Indexing"))
        del dataset
    else:
        indexref = pt.IndexRef.of(index_path)
    index = IndexFactory.of(indexref)
    bm25 = pt.terrier.Retriever(index, wmodel="BM25")
    pl2 = pt.terrier.Retriever(index, wmodel="PL2")
    pipeline = (bm25 % 100) >> pl2
    
    topics_path = f"{DATA_DIR}/msmarco/msmarco-test2020-queries.tsv"
    qrels_path = f"{DATA_DIR}/msmarco/2020qrels-pass.txt"
    topics = pd.read_csv(topics_path, sep='\t', header=None, names=['qid', 'query'], dtype={'qid': str, 'query': str})
    qrels = pd.read_csv(qrels_path, sep=' ', header=None, names=['qid', 'Q0', 'docno', 'relevance'], dtype={'qid': str, 'Q0': str, 'docno': str, 'relevance': int})
    
    def preprocess_query(query):
        query = re.sub(r'[^\w\s]', '', query)
        query = query.lower()
        return query

    # Preprocess the 'query' column
    topics['query'] = topics['query'].apply(preprocess_query)


    my_ir = Ir(SqliteIndex(f"{DATA_DIR}/msmarco-sqlite-index.db"), scoring_functions=[
        (10, BM25FScoringFunction()),
        (10, NeuralScoringFunction())
    ])
    if len(my_ir.index) == 0:
        dataset = pd.read_csv(dataset_csv, sep='\t', header=None, names=['docno', 'text'], dtype={'docno': str, 'text': str})
        sized_generator = test_dataset_to_contents(dataset)
        my_ir.bulk_index_documents(sized_generator, verbose=True)

    my_topics = pd.read_csv(topics_path, sep='\t', header=None, names=['query_id', 'text'], dtype={'query_id': int, 'text': str})
    my_run = my_ir.get_run(my_topics, verbose=True)
    print(my_run)

    pt_run = pipeline.transform(topics)
    print(pt_run)
    

if __name__ == "__main__":
    test_pyterrier()
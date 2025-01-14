import argparse
import os
import re
from typing import Literal
import pyterrier as pt
from pyterrier import IndexFactory
import pandas as pd
from tqdm.auto import tqdm

from mir import DATA_DIR
from mir.ir.impls.bm25f_scoring import BM25FScoringFunction
from mir.ir.impls.neural_scoring_function import NeuralScoringFunction
from mir.ir.impls.sqlite_index import SqliteIndex
from mir.ir.ir import Ir
from mir.utils.dataset import get_msmarco_dataset, msmarco_dataset_to_contents


def evaluate_ir(mode: Literal["validation", "test"] = "validation"):
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
    
    if mode == "validation":
        topics_path = f"{DATA_DIR}/msmarco/msmarco-test2019-queries.tsv"
        qrels_path = f"{DATA_DIR}/msmarco/2019qrels-pass.txt"
    else:
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


    my_index = SqliteIndex(f"{DATA_DIR}/msmarco-sqlite-index.db")
    if len(my_index) == 0:
        dataset = pd.read_csv(dataset_csv, sep='\t', header=None, names=['docno', 'text'], dtype={'docno': str, 'text': str})
        sized_generator = msmarco_dataset_to_contents(dataset)
        my_index.bulk_index_documents(sized_generator, verbose=True)

    my_bm25 = Ir(my_index, scoring_functions=[
        (100, BM25FScoringFunction(1.2, 0.8))
    ])

    my_neural_scoring = Ir(my_index, scoring_functions=[
        (100, BM25FScoringFunction(1.2, 0.8)),
        (10, NeuralScoringFunction())
    ])

    my_topics = pd.read_csv(topics_path, sep='\t', header=None, names=['query_id', 'text'], dtype={'query_id': int, 'text': str})
    my_bm25_run = my_bm25.get_run(my_topics, verbose=True, pyterrier_compatible=True)
    my_neural_scoring_run = my_neural_scoring.get_run(my_topics, verbose=True, pyterrier_compatible=True)
    print(my_bm25_run)
    print(my_neural_scoring_run)

    bm25 = pt.terrier.Retriever(index, wmodel="BM25")
    dfree = pt.terrier.Retriever(index, wmodel="DFRee")
    pyterrier_models = {
        "BM25": bm25 % 100,
        "BM25+DFRee": (bm25 % 100) >> dfree
    }
    pyterrier_runs = {}
    for model_name, model in pyterrier_models.items():
        print(f"Running PyTerrier {model_name}")
        pyterrier_runs[model_name] = model.transform(topics)
        print(pyterrier_runs[model_name])

    test_runs = [my_bm25_run, my_neural_scoring_run, *pyterrier_runs.values()]
    names = ["Our BM25", "Our BM25+LtR", *pyterrier_models.keys()]

    metrics = ["map", "ndcg", "recip_rank", "P.10", "recall.10", ]
    res = pt.Experiment(test_runs, topics, qrels, metrics, names=names)
    print(res)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="validation", choices=["validation", "test"])
    args = parser.parse_args()
    evaluate_ir(args.mode)
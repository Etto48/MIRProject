import os
import re
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
from mir.utils.download_and_extract import download_and_extract


get_msmarco_dataset(verbose=True)
dataset_csv = f"{DATA_DIR}/msmarco/collection.tsv"
index_path = f"{DATA_DIR}/msmarco-pyterrier-index/data.properties"
msmarco_pyterrier_index_url = "https://huggingface.co/Etto48/MIRProject/resolve/main/msmarco-pyterrier-index.tar.gz"
msmarco_sqlite_index_url = "https://huggingface.co/Etto48/MIRProject/resolve/main/msmarco-sqlite-index.db.tar.gz"
# download pyterrier index
download_and_extract(msmarco_pyterrier_index_url, f"{DATA_DIR}/msmarco-pyterrier-index", desc="PyTerrier Index")
# download sqlite index
download_and_extract(msmarco_sqlite_index_url, f"{DATA_DIR}/msmarco-sqlite-index.db", desc="SQLite Index")

indexer = pt.terrier.IterDictIndexer(f"{DATA_DIR}/msmarco-pyterrier-index")
if not os.path.exists(index_path):
    dataset = pd.read_csv(dataset_csv, sep='\t', header=None, names=['docno', 'text'], dtype={'docno': str, 'text': str})
    indexref = indexer.index(tqdm(dataset.to_dict(orient='records'), desc="Indexing"))
    del dataset
else:
    indexref = pt.IndexRef.of(index_path)
index = IndexFactory.of(indexref)


topics_path = f"{DATA_DIR}/msmarco/msmarco-test2020-queries.tsv"
qrels_path = f"{DATA_DIR}/msmarco/2020qrels-pass.txt"

topics = pd.read_csv(topics_path, sep='\t', header=None, names=['qid', 'query'], dtype={'qid': str, 'query': str})
qrels = pd.read_csv(qrels_path, sep=' ', header=None, names=['qid', 'Q0', 'docno', 'relevance'], dtype={'qid': str, 'Q0': str, 'docno': str, 'relevance': int})

def preprocess_query(query):
    query = re.sub(r'[^\w\s]', '', query)
    query = query.lower()
    return query

topics['query'] = topics['query'].apply(preprocess_query)

my_ir = Ir(SqliteIndex(f"{DATA_DIR}/msmarco-sqlite-index.db"), scoring_functions=[
    (100, BM25FScoringFunction(1.2, 0.8)),
    (10, NeuralScoringFunction())
])
if len(my_ir.index) == 0:
    dataset = pd.read_csv(dataset_csv, sep='\t', header=None, names=['docno', 'text'], dtype={'docno': str, 'text': str})
    sized_generator = msmarco_dataset_to_contents(dataset)
    my_ir.bulk_index_documents(sized_generator, verbose=True)

my_topics = pd.read_csv(topics_path, sep='\t', header=None, names=['query_id', 'text'], dtype={'query_id': int, 'text': str})

# reduce the number of topics to 10
n = 10
topics = topics.head(n)
qids = topics['qid']
my_topics = my_topics[my_topics['query_id'].isin(qids)]
qrels = qrels[qrels['qid'].isin(qids)]

my_run = my_ir.get_run(my_topics, verbose=True, pyterrier_compatible=True)

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

test_runs = [my_run, *pyterrier_runs.values()]
names = ["MyIR", *pyterrier_models.keys()]

metrics = ["map", "ndcg", "recip_rank", "P.10", "recall.10", ]
res = pt.Experiment(test_runs, topics, qrels, metrics, names=names)
print(res)
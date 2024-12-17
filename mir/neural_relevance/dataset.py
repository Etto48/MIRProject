from typing import Literal
import torch
from torch import nn
import pandas as pd
from tqdm.auto import tqdm

from mir import DATA_DIR

class MSMarcoDataset(torch.utils.data.Dataset):
    def __init__(self, collection_path: str, queries_path: str, qrels_path: str):
        self.collection = self.load_collection(collection_path)
        self.queries = self.load_queries(queries_path)
        self.qrels = self.load_qrels(qrels_path)

    @staticmethod
    def load(mode: Literal["train", "valid", "test"]):
        collection_path = f"{DATA_DIR}/msmarco/collection.tsv"
        match mode:
            case "train":
                queries_path = f"{DATA_DIR}/msmarco/queries.train.tsv"
                qrels_path = f"{DATA_DIR}/msmarco/qrels.train.tsv"
            case "valid":
                queries_path = f"{DATA_DIR}/msmarco/msmarco-test2019-queries.tsv"
                qrels_path = f"{DATA_DIR}/msmarco/2019qrels-pass.txt"
            case "test":
                raise NotImplementedError(f"Mode {mode} not implemented.")
            case _:
                raise ValueError(f"Invalid mode {mode}.")
        return MSMarcoDataset(collection_path, queries_path, qrels_path)

    def load_collection(self, collection_path: str):
        collection = pd.read_csv(collection_path, sep='\t', header=None, names=['docid', 'text'], index_col='docid')
        return collection
    
    def load_queries(self, queries_path: str):
        queries = pd.read_csv(queries_path, sep='\t', header=None, names=['qid', 'text'], index_col='qid')
        return queries
    
    def load_qrels(self, qrels_path: str):
        sep = ' ' if qrels_path.endswith(".txt") else '\t'
        qrels = pd.read_csv(qrels_path, sep=sep, header=None, names=['qid', 'Q0', 'docid', 'relevance'])
        return qrels
    
    def __len__(self):
        return len(self.qrels)
    
    def __getitem__(self, idx):
        qid = self.qrels.iloc[idx]['qid']
        docid = self.qrels.iloc[idx]['docid']
        relevance = self.qrels.iloc[idx]['relevance']
        query = self.queries.loc[qid]['text']
        doc = self.collection.loc[docid]['text']
        return query, doc, relevance
    
    @staticmethod
    def collate_fn(batch):
        queries, docs, relevances = zip(*batch)
        return queries, docs, torch.tensor(relevances, dtype=torch.float32)
    
if __name__ == "__main__":
    train = MSMarcoDataset.load("train")
    for i in tqdm(range(len(train))):
        queries, docs, relevances = train[i]
    
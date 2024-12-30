from collections.abc import Generator
import gzip
import tarfile
import numpy as np
import requests
from mir import DATA_DIR, COLAB
import pandas as pd
import os
import json
import unidecode
from tqdm.auto import tqdm

from mir.ir.document_contents import DocumentContents
from mir.utils.sized_generator import SizedGenerator

def get_msmarco_dataset(verbose: bool = False):
    """
    Downloads the MS MARCO dataset to the data directory.
    """
    corpus = "https://msmarco.z22.web.core.windows.net/msmarcoranking/collection.tar.gz"
    queries = "https://msmarco.z22.web.core.windows.net/msmarcoranking/queries.tar.gz"
    queries_valid = "https://msmarco.z22.web.core.windows.net/msmarcoranking/msmarco-test2019-queries.tsv.gz"
    queries_test = "https://msmarco.z22.web.core.windows.net/msmarcoranking/msmarco-test2020-queries.tsv.gz"
    qrels_train = "https://msmarco.z22.web.core.windows.net/msmarcoranking/qrels.train.tsv"
    qrels_valid = "https://trec.nist.gov/data/deep/2019qrels-pass.txt"
    qrels_test = "https://trec.nist.gov/data/deep/2020qrels-pass.txt"
    
    urls = [corpus, queries, queries_valid, queries_test, qrels_train, qrels_valid, qrels_test]
    dataset_dir = f"{DATA_DIR}/msmarco"
    os.makedirs(dataset_dir, exist_ok=True)
    for url in urls:
        file_name = url.split("/")[-1]
        path = f"{dataset_dir}/{file_name}"
        if not os.path.exists(path):
            response = requests.get(url, stream=True)
            response.raise_for_status()
            file_size = int(response.headers.get("content-length", 0))
            block_size = 1024
            try:
                with tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Downloading {file_name}", disable=not verbose) as pbar:
                    with open(path, "wb") as f:
                        for data in response.iter_content(block_size):
                            f.write(data)
                            pbar.update(len(data))
            except (KeyboardInterrupt, Exception) as e:
                os.remove(path)
                raise e
        decompressed_path = path.replace(".tar.gz", "")
        decompressed_path = decompressed_path.replace(".gz", "")
        if file_name.endswith(".tar.gz") and not os.path.exists(f"{decompressed_path}.tsv"):
            if verbose:
                print(f"Decompressing {file_name}...")
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(dataset_dir, filter="fully_trusted")
        elif not file_name.endswith(".tar.gz") and \
                file_name.endswith(".gz") and \
                not os.path.exists(decompressed_path):
            if verbose:
                print(f"Decompressing {file_name}...")
            with gzip.open(path, "rb") as f_in:
                with open(decompressed_path, "wb") as f_out:
                    f_out.write(f_in.read())

def msmarco_dataset_to_contents(corpus: pd.DataFrame, verbose: bool = False) -> SizedGenerator[DocumentContents, None, None]:
    """
    Returns the number of documents and a generator of DocumentContents from the test corpus.
    """
    def inner() -> Generator[DocumentContents, None, None]:
        for _, row in corpus.iterrows():
            yield DocumentContents(author="", title="", body=row['text'], doc_id=int(row['docno']))
    return SizedGenerator(inner(), len(corpus))


if __name__ == "__main__":
    #df = get_dataset(verbose=True)
    get_msmarco_dataset(verbose=True)

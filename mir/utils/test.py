import pyterrier as pt
from pyterrier import IndexFactory
import pandas as pd
from tqdm.auto import tqdm

from mir import DATA_DIR
from mir.utils.dataset import get_msmarco_dataset


def test_pyterrier():
    get_msmarco_dataset()
    dataset_csv = f"{DATA_DIR}/msmarco/collection.tsv"
    dataset = pd.read_csv(dataset_csv, sep='\t', header=None, names=['docno', 'text'], dtype={'docno': str, 'text': str})
    indexer = pt.terrier.IterDictIndexer(f"{DATA_DIR}/msmarco-pyterrier-index")
    indexref = indexer.index(tqdm(dataset.to_dict(orient='records'), desc="Indexing"))
    index = IndexFactory.of(indexref)
    bm25 = pt.terrier.Retiever(index, wmodel="BM25")

    print(index.getCollectionStatistics())


if __name__ == "__main__":
    test_pyterrier()
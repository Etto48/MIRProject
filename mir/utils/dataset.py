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


def get_dataset(verbose=False) -> pd.DataFrame:
    """
    Downloads or loads the dataset from the data directory.
    Languages other than English are filtered out.
    """
    filtered_df_path = f"{DATA_DIR}/filtered-lyrics-data.csv"

    if not os.path.exists(filtered_df_path):
        if not os.path.exists(f"{DATA_DIR}/lyrics-data.csv"):
            if verbose:
                print("Downloading dataset...")
            kaggle_handle = "neisse/scrapped-lyrics-from-6-genres"
            if COLAB:
                from google.colab import userdata  # type: ignore
                kaggle_data = json.loads(userdata.get("kaggle"))
            else:
                if not os.path.exists(f"{DATA_DIR}/kaggle.json"):
                    if os.getenv("KAGGLE_USERNAME") is None or os.getenv("KAGGLE_KEY") is None:
                        raise FileNotFoundError(
                            "Kaggle API credentials not found. Please add kaggle.json to the data directory.")
                    else:
                        kaggle_data = {
                            "username": os.getenv("KAGGLE_USERNAME"),
                            "key": os.getenv("KAGGLE_KEY")
                        }
                else:
                    with open(f"{DATA_DIR}/kaggle.json") as f:
                        kaggle_data = json.load(f)
            os.environ["KAGGLE_USERNAME"] = kaggle_data["username"]
            os.environ["KAGGLE_KEY"] = kaggle_data["key"]
            import kaggle
            kaggle.api.dataset_download_files(
                kaggle_handle,
                path=DATA_DIR,
                unzip=True,
                quiet=not verbose
            )
        if verbose:
            print("Filtering dataset...")
        df = pd.read_csv(f"{DATA_DIR}/lyrics-data.csv")
        df.dropna(inplace=True)
        filtered_df = df[df.loc[:, 'language'] == 'en']
        filtered_df.rename(
            columns={"ALink": "artist", "SName": "song", "Lyric": "lyrics"}, inplace=True)
        filtered_df.drop(columns=["language", "SLink"], inplace=True)

        def fix_name(name: str):
            return " ".join([
                name_part
                .capitalize()
                for name_part in
                name[1:-1]
                .replace("-", " ")
                .split()
            ])

        def fix_song(song: str):
            return unidecode.unidecode(song)

        def fix_lyrics(lyrics: str):
            return unidecode.unidecode(lyrics).replace("\n", " ")

        filtered_df.loc[:, 'artist'] = filtered_df['artist'].map(fix_name)
        filtered_df.loc[:, 'song'] = filtered_df['song'].map(fix_song)
        filtered_df.loc[:, 'lyrics'] = filtered_df['lyrics'].map(fix_lyrics)
        filtered_df.reset_index(drop=True, inplace=True)
        filtered_df.to_csv(filtered_df_path, index=False)
        os.remove(f"{DATA_DIR}/lyrics-data.csv")
        os.remove(f"{DATA_DIR}/artists-data.csv")
    else:
        if verbose:
            print("Loading dataset...")
        filtered_df = pd.read_csv(filtered_df_path)
    if verbose:
        print("Dataset loaded.")
    return filtered_df

def get_subdataset(verbose: bool = False, amount: int = 100, seed: int = None) -> pd.DataFrame:
    """
    Returns a random subset of the dataset.

    Parameters:
    - verbose (bool): Whether to show progress bars.
    - amount (int): The number of documents to return.
    """
    if seed is not None:
        np.random.seed(seed)
    ret = get_dataset(verbose)
    indices = np.random.choice(range(len(ret)), amount)
    return ret.iloc[indices]

def dataset_to_contents(df: pd.DataFrame) -> SizedGenerator[DocumentContents, None, None]:
    """
    Returns the number of documents and a generator of DocumentContents from the dataset.
    """
    def inner() -> Generator[DocumentContents, None, None]:
        for _, row in df.iterrows():
            yield DocumentContents(author=row['artist'], title=row['song'], body=row['lyrics'])
    return SizedGenerator(inner(), len(df))


def get_msmarco_dataset(verbose: bool = False) -> tuple[
    tuple[pd.DataFrame, str],
    tuple[pd.DataFrame, str],
    tuple[pd.DataFrame, str]
]:
    """
    Downloads the MS MARCO dataset from the data directory.
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

def test_dataset_to_contents(corpus: pd.DataFrame, verbose: bool = False) -> SizedGenerator[DocumentContents, None, None]:
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

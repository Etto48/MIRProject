from collections.abc import Generator
import gzip
import tarfile
import requests
from mir import DATA_DIR, COLAB
import pandas as pd
import os
import json
import unidecode
from tqdm.auto import tqdm

from mir.ir.document_contents import DocumentContents
from mir.utils.types import SizedGenerator


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


def dataset_to_contents(df: pd.DataFrame) -> SizedGenerator[DocumentContents, None, None]:
    """
    Returns the number of documents and a generator of DocumentContents from the dataset.
    """
    def inner() -> Generator[DocumentContents, None, None]:
        for _, row in df.iterrows():
            yield DocumentContents(author=row['artist'], title=row['song'], body=row['lyrics'])
    return SizedGenerator(inner(), len(df))


def get_test_dataset(verbose: bool = False) -> tuple[
    tuple[pd.DataFrame, str],
    tuple[pd.DataFrame, str],
    tuple[pd.DataFrame, str]
]:
    """
    Downloads and loads the test dataset, returning the corpus, queries, and qrels
    both as DataFrames and file paths.
    """
    test_corpus_url = "https://msmarco.z22.web.core.windows.net/msmarcoranking/collection.tar.gz"
    test_queries_url = "https://msmarco.z22.web.core.windows.net/msmarcoranking/msmarco-test2020-queries.tsv.gz"
    test_qrels_url = "https://trec.nist.gov/data/deep/2020qrels-pass.txt"
    urls = [test_corpus_url, test_queries_url, test_qrels_url]
    test_dir = f"{DATA_DIR}/test"
    os.makedirs(test_dir, exist_ok=True)
    for url in urls:
        file_name = url.split("/")[-1]
        path = f"{test_dir}/{file_name}"
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
                tar.extractall(test_dir, filter="fully_trusted")
        elif not file_name.endswith(".tar.gz") and \
                file_name.endswith(".gz") and \
                not os.path.exists(decompressed_path):
            if verbose:
                print(f"Decompressing {file_name}...")
            with gzip.open(path, "rb") as f_in:
                with open(decompressed_path, "wb") as f_out:
                    f_out.write(f_in.read())

    if verbose:
        print("Loading test dataset...")
    corpus_path = f"{test_dir}/collection.tsv"
    queries_path = f"{test_dir}/msmarco-test2020-queries.tsv"
    qrels_path = f"{test_dir}/2020qrels-pass.txt"
    corpus = pd.read_csv(
        corpus_path,
        sep="\t",
        header=None,
        names=["doc_id", "text"],
        dtype={"doc_id": str})
    queries = pd.read_csv(
        queries_path,
        sep="\t",
        header=None,
        names=["query_id", "text"],
        dtype={"query_id": str})
    qrels = pd.read_csv(
        qrels_path,
        sep=" ",
        header=None,
        names=["query_id", "0", "doc_id", "relevance"],
        dtype={"query_id": str, "doc_id": str})
    if verbose:
        print("Test dataset loaded.")
    return (
        (corpus, corpus_path),
        (queries, queries_path),
        (qrels, qrels_path),
    )


def test_dataset_to_contents(corpus: pd.DataFrame, verbose: bool = False) -> SizedGenerator[DocumentContents, None, None]:
    """
    Returns the number of documents and a generator of DocumentContents from the test corpus.
    """
    def inner() -> Generator[DocumentContents, None, None]:
        for _, row in corpus.iterrows():
            yield DocumentContents(row['doc_id'], row['text'])
    return SizedGenerator(inner(), len(corpus))


if __name__ == "__main__":
    df = get_dataset(verbose=True)
    corpus, queries, qrels = get_test_dataset(verbose=True)

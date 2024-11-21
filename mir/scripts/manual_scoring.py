import os
import numpy as np
import pandas as pd

import pyterrier as pt
from mir import DATA_DIR
from mir.utils.dataset import get_dataset

word_list = []

def generate_query(dataset: pd.DataFrame) -> str:
    cols = ["artist", "song", "lyrics"]
    query_for = np.random.choice(cols, p=[0.2, 0.2, 0.6])
    doc_id = np.random.randint(len(dataset))
    full_text: str = dataset[query_for][doc_id]
    full_text = full_text.lower()
    full_text = "".join([c for c in full_text if c.isalnum() or c.isspace()])
    tokens = full_text.split()
    if len(tokens) == 0:
        raise ValueError(f"Empty text for doc_id {doc_id} and query_for {query_for}")
    query_length = np.random.randint(1, min(len(tokens) + 1, 10))
    query_start = np.random.randint(len(tokens) - query_length + 1)

    query_tokens = tokens[query_start:query_start + query_length]
    do_random_discard = np.random.choice([True, False], p=[0.2, 0.8]) if len(query_tokens) > 1 else False
    if do_random_discard:
        discard_idx = np.random.randint(len(query_tokens))
        query_tokens.pop(discard_idx)
    
    query = " ".join(query_tokens)
    return query

def print_highlighted(text: str, tokens: set[str]):
    for token in text.split():
        preprocessed_token = "".join([c for c in token if c.isalnum()]).lower()
        if preprocessed_token in tokens:
            print(f"\033[1;31m{token}\033[0m", end=" ")
        else:
            print(token, end=" ")
    print()

if __name__ == "__main__":
    np.random.seed(42)
    dataset = get_dataset(verbose=True)
    query_count = 1000
    top_k = 10

    if not os.path.exists(f"{DATA_DIR}/manual_test/queries.csv"):
        queries = [generate_query(dataset) for _ in range(query_count)]
        queries = pd.DataFrame(queries, columns=["query"])
        os.makedirs(f"{DATA_DIR}/manual_test", exist_ok=True)
        queries.to_csv(f"{DATA_DIR}/manual_test/queries.csv", index=True)
    else:
        queries = pd.read_csv(f"{DATA_DIR}/manual_test/queries.csv")

    index_location = f"{DATA_DIR}/manual_test/index"
    if not os.path.exists(index_location):
        pt_dataset = {
            "docno": [str(i) for i in range(len(dataset))],
            "text": [f"{row['artist']} {row['song']} {row['lyrics']}" for _, row in dataset.iterrows()]
        }
        pt_dataset = pd.DataFrame(pt_dataset)
        indexer = pt.terrier.IterDictIndexer(index_location)
        indexer_ref = indexer.index(pt_dataset.to_dict(orient="records"))
    else:
        indexer_ref = pt.terrier.IndexFactory.of(index_location)
    
    state_of_the_art = pt.terrier.Retriever(indexer_ref, wmodel="BM25")

    
    if not os.path.exists(f"{DATA_DIR}/manual_test/scores.csv"):
        scores = pd.DataFrame(columns=["qid", "docno", "score"])
    else:
        scores = pd.read_csv(f"{DATA_DIR}/manual_test/scores.csv")    
    
    already_scored = set((row["qid"], row["docno"]) for _, row in scores.iterrows())
    stop = False
    for qid, query in enumerate(queries["query"]):
        if stop:
            break
        query_tokens = set(query.split())
        results = state_of_the_art.search(query)
        results = results.head(top_k)
        docnos = results["docno"].values
        docs = dataset.iloc[docnos]
        for docno, doc in docs.iterrows():
            if (qid, docno) in already_scored:
                continue
            
            print(f"Query: \033[1;32m{query}\033[0m")
            print(f"Artist: ", end="")
            print_highlighted(doc["artist"], query_tokens)
            print(f"Song: ", end="")
            print_highlighted(doc["song"], query_tokens)
            print()
            print(f"Lyrics: ")
            print_highlighted(doc["lyrics"], query_tokens)
            print()
            score = input("Score (0-5): ")
            if "q" in score:
                stop = True
                break
            score = int(score)
            scores.loc[len(scores)] = [qid, docno, score]
    
    scores.to_csv(f"{DATA_DIR}/manual_test/scores.csv", index=False, header=False)
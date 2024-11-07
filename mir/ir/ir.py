from collections.abc import Generator
from typing import Optional

import pandas as pd
from tqdm.auto import tqdm
from more_itertools import peekable

from mir.ir.document_contents import DocumentContents
from mir.ir.impls.default_index import DefaultIndex
from mir.ir.impls.count_scoring_function import CountScoringFunction
from mir.ir.impls.default_tokenizers import DefaultTokenizer
from mir.ir.index import Index
from mir.ir.priority_queue import PriorityQueue
from mir.ir.scoring_function import ScoringFunction
from mir.ir.tokenizer import Tokenizer
from mir.utils.types import SizedGenerator

class Ir:
    def __init__(self, index: Optional[Index] = None, tokenizer: Optional[Tokenizer] = None, scoring_functions: Optional[list[tuple[int, ScoringFunction]]] = None):
        """
        Create an IR system.

        # Parameters
        - index (Index): The index to use. If None, a DefaultIndex is used.
        - tokenizer (Tokenizer): The tokenizer to use. If None, a DefaultTokenizer is used.
        - scoring_functions (Optional[list[tuple[int, ScoringFunction]]]): A list of scoring functions to use, with their respective top_k results to keep.
        If None CountScoringFunction is used.
        """
        self.index = index or DefaultIndex()
        self.tokenizer = tokenizer or DefaultTokenizer()
        self.scoring_functions = scoring_functions or [
            (1000, CountScoringFunction())
        ]



    def __len__(self) -> int:
        """
        Get the number of documents in the index.
        """
        return len(self.index)

    def index_document(self, doc: DocumentContents) -> None:
        """
        Index a document.

        # Parameters
        - doc (DocumentContents): The document to index.
        """
        self.index.index_document(doc, self.tokenizer)

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], verbose: bool = False) -> None:
        """
        Bulk index documents.

        # Parameters
        - docs (SizedGenerator[DocumentContents, None, None]): A generator of documents to index.
        - verbose (bool): Whether to show a progress bar.
        """
        self.index.bulk_index_documents(docs, self.tokenizer, verbose)

    def search(self, query: str) -> Generator[DocumentContents, None, None]:
        """
        Search for documents based on a query.
        Uses document-at-a-time scoring.

        # Parameters
        - query (str): The query to search for.
        - scoring_functions (list[ScoringFunction]): A list of scoring functions to use.

        # Yields
        - DocumentContents: A document that matches the query. In decreasing order of score.
        It also has a score attribute with the score of the document.
        """

        assert len(self.scoring_functions) > 0, "At least one scoring function must be provided"

        ks, scoring_functions = zip(*self.scoring_functions)
        scoring_functions = list(scoring_functions)
        ks = list(ks)[::-1]

        
        terms = self.tokenizer.tokenize_query(query)
        term_ids = [term_id for term in terms if (
            term_id := self.index.get_term_id(term.token)) is not None]
        terms = [self.index.get_term(term_id) for term_id in term_ids]
        posting_generators = [
            peekable(self.index.get_postings(term_id)) for term_id in term_ids]

        priority_queue = PriorityQueue(ks[-1])
        first_scoring_function = scoring_functions[0]
        postings_cache = {}

        while True:
            # find the lowest doc_id among all the posting lists
            # doing this avoids having to iterate over all the doc_ids
            # we only take into account the doc_ids that are present in the posting lists
            lowest_doc_id = None
            empty_posting_lists = []
            for i, posting in enumerate(posting_generators):
                try:
                    doc_id = posting.peek().doc_id
                    if lowest_doc_id is None or doc_id < lowest_doc_id:
                        lowest_doc_id = doc_id
                except StopIteration:
                    empty_posting_lists.append(i)
            # all the posting lists are empty
            if lowest_doc_id is None:
                break

            # remove the empty posting lists
            for i in reversed(empty_posting_lists):
                posting_generators.pop(i)
                term_ids.pop(i)

            postings = []
            # get all the postings with the current doc_id, and advance their iterators
            for i, posting in enumerate(posting_generators):
                if posting.peek().doc_id == lowest_doc_id:
                    next_posting = next(posting)
                    next_posting.set_attribute("term_id", term_ids[i])
                    postings.append(next_posting)
            postings_cache[lowest_doc_id] = postings
            # now that we have all the info about the current document, we can score it
            score = first_scoring_function(self.index.get_document_info(lowest_doc_id), postings, terms)
            # we add the score and doc_id to the priority queue
            priority_queue.push(lowest_doc_id, score)

        for scoring_function in scoring_functions[1:]:
            ks.pop()
            new_priority_queue = PriorityQueue(ks[-1])
            for score, doc_id in priority_queue:
                postings = postings_cache[doc_id]
                new_score = scoring_function(self.index.get_document(doc_id), postings, terms)
                new_priority_queue.push(doc_id, new_score)
            priority_queue = new_priority_queue
        
        priority_queue.finalise()

        for score, doc_id in priority_queue:
            ret = self.index.get_document_contents(doc_id)
            ret.set_score(score)
            yield ret

    def get_run(self, queries: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
        """
        Generate a run file for the given queries in the form of a pandas DataFrame.
        You can encode it to a file using a tab separator and the to_csv method.

        # Parameters
        - queries (pd.DataFrame): A DataFrame with the queries to run. 
        It must have the columns "query_id" and "text".
        - verbose (bool): Whether to show a progress bar.

        # Returns
        - pd.DataFrame: The run file. It has the columns 
        "query_id", "Q0", "document_no", "rank", "score", "run_id".
        """
        run = pd.DataFrame(
            columns=["query_id", "Q0", "document_no", "rank", "score", "run_id"])
        for _, query_row in tqdm(queries.iterrows(), desc="Running queries", disable=not verbose, total=len(queries)):
            query_id = query_row["query_id"]
            query = query_row["text"]
            for rank, doc in enumerate(self.search(query), start=1):
                run.loc[len(run)] = [
                    query_id, "Q0",
                    doc.title, rank, doc.score, self.__class__.__name__]
        run.reset_index(drop=True, inplace=True)
        return run


if __name__ == "__main__":
    from mir.utils.dataset import dataset_to_contents
    from mir.utils.dataset import get_dataset
    from mir.utils.decorators import profile

    impls = [
        Ir()
    ]
    ds = get_dataset(verbose=True)

    for impl in impls:
        ir = impl

        @profile
        def index():
            docs = dataset_to_contents(ds)
            ir.bulk_index_documents(docs, verbose=True)

        (_, index_time) = index()

        @profile
        def run():
            queries = pd.DataFrame({
                "query_id": [0, 1, 2, 3, 4, 5],
                "text": [
                    "never gonna give you up",
                    "i'll never gonna dance again",
                    "wake me up",
                    "i was made for loving you",
                    "take on me",
                    "i want to break free",
                ]
            })
            return ir.get_run(queries, verbose=True)

        (run_file, run_rime) = run()

        print(
            f"{impl.__name__} index time: "
            f"{index_time:.3f}s, run time: {run_rime:.3f}s")

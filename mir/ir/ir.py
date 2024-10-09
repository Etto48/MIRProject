from abc import abstractmethod
from collections.abc import Generator
from typing import Optional, Protocol

import pandas as pd
from tqdm.auto import tqdm
from more_itertools import peekable

from mir.ir.document import Document
from mir.ir.document_contents import DocumentContents
from mir.ir.posting import Posting
from mir.ir.priority_queue import PriorityQueue
from mir.ir.term import Term
from mir.utils.types import SizedGenerator


class Ir(Protocol):
    @abstractmethod
    def get_postings(self, term_id: int) -> Generator[Posting, None, None]:
        """
        Get a generator of postings for a term_id.
        MUST be sorted by doc_id.

        # Parameters
        - term_id (int): The term_id.

        # Yields
        - Posting: A posting from the posting list related to the term_id.
        """

    @abstractmethod
    def get_document(self, doc_id: int) -> Document:
        """
        Get document info from a doc_id.

        # Parameters
        - doc_id (int): The doc_id.

        # Returns
        - Document: The document related to the doc_id.
        """

    @abstractmethod
    def get_term(self, term_id: int) -> Term:
        """
        Get term info from a term_id.

        # Parameters
        - term_id (int): The term_id.

        # Returns
        - Term: The term related to the term_id.
        """

    @abstractmethod
    def get_term_id(self, term: str) -> Optional[int]:
        """
        Get term_id from a term in string format.
        Returns None if the term is not in the index.

        # Parameters
        - term (str): The term in string format.

        # Returns
        - Optional[int]: The term_id related to the term or None if the term is not in the index.
        """

    @abstractmethod
    def process_document(self, doc: DocumentContents) -> list[str]:
        """
        Process a document and return a list of term strings.

        # Parameters
        - doc (DocumentContents): The document to process.

        # Returns
        - list[str]: A list of term strings.
        """

    @abstractmethod
    def process_query(self, query: str) -> list[str]:
        """
        Process a query and return a list of term strings.

        # Parameters
        - query (str): The query to process.

        # Returns
        - list[str]: A list of term strings.
        """

    @abstractmethod
    def score(self, document: Document, postings: list[Posting], query: list[Term]) -> float:
        """
        Score a document based on the postings and the query.

        # Parameters
        - document (Document): The document to score.
        - postings (list[Posting]): The postings related to the document and the query.
        - query (list[Term]): The query terms.

        # Returns
        - float: The score of the document.
        """

    @abstractmethod
    def index_document(self, doc: DocumentContents) -> None:
        """
        Add a document to the index.

        # Parameters
        - doc (DocumentContents): The document to add to the index.
        """

    def search(self, query: str, top_k: int = 1000) -> Generator[DocumentContents, None, None]:
        """
        Search for documents based on a query.
        Uses document-at-a-time scoring.

        # Parameters
        - query (str): The query to search for.
        - top_k (int): The number of documents to return.

        # Yields
        - DocumentContents: A document that matches the query. In decreasing order of score.
        It also has a score attribute with the score of the document.
        """

        terms = self.process_query(query)
        term_ids = [term_id for term in terms if (
            term_id := self.get_term_id(term)) is not None]
        terms = [self.get_term(term_id) for term_id in term_ids]
        posting_generators = [
            peekable(self.get_postings(term_id)) for term_id in term_ids]

        priority_queue = PriorityQueue(top_k)

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
            # now that we have all the info about the current document, we can score it
            score = self.score(self.get_document(
                lowest_doc_id), postings, terms)
            # we add the score and doc_id to the priority queue
            priority_queue.push(lowest_doc_id, score)

        priority_queue.finalise()

        # yield the documents in decreasing order of score
        for score, doc_id in priority_queue:
            contents = self.get_document(doc_id).contents
            contents.set_score(score)
            yield contents

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], verbose: bool = False) -> None:
        """
        Add multiple documents to the index, this calls index_document for each document.

        # Parameters
        - docs (SizedGenerator[DocumentContents, None, None]): A generator of documents to add to the index.
        - verbose (bool): Whether to show a progress bar.
        """
        for doc in tqdm(docs, desc="Indexing documents", disable=not verbose, total=len(docs)):
            self.index_document(doc)

    def get_run(self, queries: pd.DataFrame, top_k: int, verbose: bool = False) -> pd.DataFrame:
        """
        Generate a run file for the given queries in the form of a pandas DataFrame.
        You can encode it to a file using a tab separator and the to_csv method.

        # Parameters
        - queries (pd.DataFrame): A DataFrame with the queries to run. 
        It must have the columns "query_id" and "text".
        - top_k (int): The number of documents to return for each query.
        - verbose (bool): Whether to show a progress bar.

        # Returns
        - pd.DataFrame: The run file. It has the columns 
        "query_id", "Q0", "document_no", "rank", "score", "run_id".
        """
        run = pd.DataFrame(
            columns=["query_id", "Q0", "document_no", "rank", "score", "run_id"])
        for _, query_row in tqdm(queries.iterrows(), desc="Running queries", disable=not verbose):
            query_id = query_row["query_id"]
            query = query_row["text"]
            for rank, doc in enumerate(self.search(query, top_k), start=1):
                run.loc[len(run)] = [
                    query_id, "Q0",
                    doc.title, rank, doc.score, self.__class__.__name__]
                if rank == top_k:
                    break
        run.reset_index(drop=True, inplace=True)
        return run


if __name__ == "__main__":
    from mir.utils.dataset import dataset_to_contents
    from mir.utils.dataset import get_dataset
    from mir.utils.decorators import profile
    from mir.ir.impls.naive_ir import NaiveIr

    impls = [NaiveIr]
    ds = get_dataset(verbose=True)

    for impl in impls:
        ir = impl()

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
            return ir.get_run(queries, top_k=1000, verbose=True)

        (run_file, run_rime) = run()

        print(
            f"{impl.__name__} index time: "
            f"{index_time:.3f}s, run time: {run_rime:.3f}s")

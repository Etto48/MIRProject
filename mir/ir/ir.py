from collections.abc import Generator, Iterable
from typing import Optional

import pandas as pd
from tqdm import tqdm
from more_itertools import peekable

from mir.ir.document import Document
from mir.ir.document_contents import DocumentContents
from mir.ir.posting import Posting
from mir.ir.priority_queue.impls import HeapPQ
from mir.ir.priority_queue.priority_queue import PriorityQueue
from mir.ir.term import Term


class SortableDocument:
    def __init__(self, doc_id: int, score: float):
        self.doc_id = doc_id
        self.score = score

    def __lt__(self, other: "SortableDocument"):
        return self.score < other.score

    def __eq__(self, other: "SortableDocument"):
        return self.score == other.score

    def __gt__(self, other: "SortableDocument"):
        return self.score > other.score

    def __le__(self, other: "SortableDocument"):
        return self.score <= other.score

    def __ge__(self, other: "SortableDocument"):
        return self.score >= other.score

    def __ne__(self, other: "SortableDocument"):
        return self.score != other.score


class Ir:
    def get_postings(self, term_id: int) -> Generator[Posting, None, None]:
        """
        Get a generator of postings for a term_id.
        MUST be sorted by doc_id.
        """
        raise NotImplementedError()

    def get_document(self, doc_id: int) -> Document:
        """
        Get document info from a doc_id.
        """
        raise NotImplementedError()

    def get_term(self, term_id: int) -> Term:
        """
        Get term info from a term_id.
        """
        raise NotImplementedError()

    def get_term_id(self, term: str) -> Optional[int]:
        """
        Get term_id from a term in string format.
        Returns None if the term is not in the index.
        """
        raise NotImplementedError()

    def process_document(self, doc: DocumentContents) -> list[str]:
        """
        Process a document and return a list of term strings.
        """
        raise NotImplementedError()

    def process_query(self, query: str) -> list[str]:
        """
        Process a query and return a list of term strings.
        """
        raise NotImplementedError()

    def score(self, document: Document, postings: list[Posting], query: list[Term]) -> float:
        """
        Score a document based on the postings and the query.
        """
        raise NotImplementedError()

    def index_document(self, doc: DocumentContents) -> None:
        """
        Add a document to the index.
        """
        raise NotImplementedError()

    def search(self, query: str) -> Generator[DocumentContents, None, None]:
        """
        Search for documents based on a query.
        Uses document-at-a-time scoring.
        """

        terms = self.process_query(query)
        term_ids = [term_id for term in terms if (term_id:=self.get_term_id(term)) is not None]
        terms = [self.get_term(term_id) for term_id in term_ids]
        posting_generators = [
            peekable(self.get_postings(term_id)) for term_id in term_ids]

        priority_queue: PriorityQueue = HeapPQ()

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

            postings = []
            # get all the postings with the current doc_id, and advance their iterators
            for posting in posting_generators:
                if posting.peek().doc_id == lowest_doc_id:
                    postings.append(next(posting))
            # now that we have all the info about the current document, we can score it
            score = self.score(self.get_document(
                lowest_doc_id), postings, terms)
            # we add the score and doc_id to the priority queue
            priority_queue.push(SortableDocument(lowest_doc_id, -score))

        priority_queue.finalise()

        # yield the documents in decreasing order of score
        while len(priority_queue) != 0:
            sd: SortableDocument = priority_queue.pop()
            doc_id = sd.doc_id
            neg_score = sd.score
            contents = self.get_document(doc_id).contents
            contents.set_score(-neg_score)
            yield contents

    def bulk_index_documents(self, docs: Iterable[DocumentContents], verbose: bool = False) -> None:
        """
        Add multiple documents to the index, this calls index_document for each document.
        """
        for doc in tqdm(docs, desc="Indexing documents", disable=not verbose):
            self.index_document(doc)

    def get_run(self, queries: dict[int, str], top_k: int, verbose: bool = False) -> pd.DataFrame:
        """
        Generate a run file for the given queries in the form of a pandas DataFrame.
        You can encode it to a file using a tab separator and the to_csv method.
        """
        run = pd.DataFrame(
            columns=["query_id", "Q0", "document_no", "rank", "score", "run_id"])
        for query_id, query in tqdm(queries.items(), desc="Running queries", disable=not verbose):
            for rank, doc in enumerate(self.search(query), start=1):
                run.loc[len(run)] = [
                    query_id, "Q0",
                    doc.title, rank, doc.score, self.__class__.__name__]
                if rank == top_k:
                    break
        run.reset_index(drop=True, inplace=True)
        return run


if __name__ == "__main__":
    from mir.dataset import dataset_to_contents
    from mir.dataset import get_dataset
    from mir.utils.decorators import profile
    from mir.ir.impls.naive_ir import NaiveIr

    impls = [NaiveIr]
    ds = get_dataset(verbose=True)

    for impl in impls:
        ir = impl()

        @profile
        def index():
            ir.bulk_index_documents(dataset_to_contents(ds), verbose=True)

        (_, index_time) = index()

        @profile
        def run():
            return ir.get_run({
                0: "love",
                1: "hate",
                2: "war",
                3: "peace",
                4: "death",
                5: "life",
            }, top_k=10, verbose=True)

        (run_file, run_rime) = run()

        print(f"{impl.__name__} index time: {\
              index_time:.3f}s, run time: {run_rime:.3f}s")
        print(run_file)

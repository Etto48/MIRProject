from collections.abc import Generator, Iterable
import heapq

import pandas as pd
from tqdm import tqdm
from more_itertools import peekable

from mir.ir.document import Document
from mir.ir.document_contents import DocumentContents
from mir.ir.posting import Posting
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

    def get_term_id(self, term: str) -> int:
        """
        Get term_id from a term in string format.
        """
        raise NotImplementedError()

    def process_document(self, doc: DocumentContents) -> list[int]:
        """
        Process a document and return a list of term_ids.
        """
        raise NotImplementedError()

    def process_query(self, query: str) -> list[int]:
        """
        Process a query and return a list of term_ids.
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

        term_ids = self.process_query(query)
        terms = [self.get_term(term_id) for term_id in term_ids]
        posting_generators = [
            peekable(self.get_postings(term_id)) for term_id in term_ids]

        priority_queue = []

        while True:
            # find the lowest doc_id among all the posting lists
            # doing this avoids having to iterate over all the doc_ids
            # we only take into account the doc_ids that are present in the posting lists
            lowest_doc_id = min((doc_id for posting in posting_generators if (
                doc_id := posting.peek().doc_id) is not None), default=None)
            # all the posting lists are empty
            if lowest_doc_id is None:
                break
            postings = []
            # get all the postings with the current doc_id, and advance their iterators
            for posting in posting_generators:
                if posting.peek().doc_id == lowest_doc_id:
                    postings.append(next(posting))
            # now that we have all the info about the current document, we can score it
            score = self.score(self.get_document(
                lowest_doc_id), postings, terms)
            # we add the score and doc_id to the priority queue
            heapq.heappush(priority_queue, SortableDocument(
                lowest_doc_id, -score))

        # yield the documents in decreasing order of score
        while len(priority_queue) != 0:
            sd: SortableDocument = heapq.heappop(priority_queue)
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
                run[len(run)] = [query_id, "Q0",
                                 doc.title, rank, doc.score, "MIR"]
                if rank == top_k:
                    break
        return run

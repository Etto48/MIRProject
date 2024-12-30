from collections.abc import Generator
import string
import time
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
from mir.utils.sized_generator import SizedGenerator

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
        self.index: Index = index if index is not None else DefaultIndex()
        self.tokenizer: Tokenizer = tokenizer if tokenizer is not None else DefaultTokenizer()
        self.scoring_functions: list[tuple[int, ScoringFunction]] = scoring_functions if scoring_functions is not None else [
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
        scoring_functions: list[ScoringFunction] = list(scoring_functions)
        ks: list[int] = list(ks)[::-1]
        
        terms = self.tokenizer.tokenize_query(query)
        term_ids = [term_id for term in terms if (
            term_id := self.index.get_term_id(term.text)) is not None]
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
                    postings.append(next_posting)
            postings_cache[lowest_doc_id] = postings
            # now that we have all the info about the current document, we can score it
            global_info = self.index.get_global_info()
            document_info = self.index.get_document_info(lowest_doc_id)
            score = first_scoring_function(document_info, postings, terms, **global_info)
            # we add the score and doc_id to the priority queue
            popped_doc_id = priority_queue.push(lowest_doc_id, score)
            # if the priority queue is full, we remove the lowest score
            if popped_doc_id is not None:
                del postings_cache[popped_doc_id]
        
        priority_queue.finalise()

        for scoring_function in scoring_functions[1:]:
            ks.pop()
            resorted_documents = []
            if scoring_function.batched_call is not None:
                scores: list[float] = scoring_function.batched_call(
                    [self.index.get_document_contents(doc_id).body for _, doc_id in priority_queue.heap[:ks[-1]]],
                    query
                )
                for i, (score, doc_id) in enumerate(priority_queue.heap[:ks[-1]]):
                    new_score = scores[i]
                    resorted_documents.append((new_score + score, doc_id))
            else:
                for score, doc_id in priority_queue.heap[:ks[-1]]:
                    postings = postings_cache[doc_id]
                    global_info = self.index.get_global_info()
                    global_info["document_content"] = self.index.get_document_contents(doc_id).body
                    global_info["query_content"] = query
                    new_score = scoring_function(self.index.get_document_info(doc_id), postings, terms, **global_info)
                    # we add the old score to maintain monotonicity
                    resorted_documents.append((new_score + score, doc_id))
            
            resorted_documents.sort(key=lambda x: x[0], reverse=True)
            priority_queue.heap = resorted_documents + priority_queue.heap[ks[-1]:]

        for score, doc_id in priority_queue:
            ret = self.index.get_document_contents(doc_id)
            ret.add_field("id", doc_id)
            ret.set_score(score)
            yield ret

    def get_run(self, queries: pd.DataFrame, verbose: bool = False, pyterrier_compatible: bool = False) -> pd.DataFrame:
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
        If pyterrier_compatible is True, the columns are "qid", "docid", "docno", "rank", "score", "query".
        """
        
        run = []
        for _, query_row in tqdm(queries.iterrows(), desc="Running queries", disable=not verbose, total=len(queries)):
            query_id = query_row["query_id"]
            query = query_row["text"]
            for rank, doc in enumerate(self.search(query), start=0):
                if pyterrier_compatible:
                    run.append(
                        {"qid": query_id, "docid": doc.id, "docno": doc.id, "rank": rank, "score": doc.score, "query": query})
                else:
                    run.append(
                        {"query_id": query_id, "Q0": "Q0", "doc_id": doc.id, "rank": rank, "score": doc.score, "run_id": self.__class__.__name__})

        run = pd.DataFrame(run)
        return run

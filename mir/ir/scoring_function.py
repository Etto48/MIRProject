from typing import Protocol

from mir.ir.document import Document
from mir.ir.posting import Posting
from mir.ir.term import Term


class ScoringFunction(Protocol):
    def __call__(self, document: Document, postings: list[Posting], query: list[Term]) -> float:
        """
        Score a document based on the postings and the query.

        # Parameters
        - document (Document): The document to score.
        - postings (list[Posting]): The postings related to the document and the query.
        - query (list[Term]): The query terms.

        # Returns
        - float: The score of the document.
        """
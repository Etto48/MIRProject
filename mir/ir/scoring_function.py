from typing import Any, Protocol

from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.term import Term


class ScoringFunction(Protocol):
    def __call__(self, document_info: DocumentInfo, postings: list[Posting], query: list[Term], **kwargs: dict[str, Any]) -> float:
        """
        Score a document based on the postings and the query.

        # Parameters
        - document_info (DocumentInfo): The document info relative to the document to score.
        - postings (list[Posting]): The postings related to the document and the query.
        - query (list[Term]): The query terms.
        - **kwargs (dict[str, Any]): Additional arguments for the scoring function.

        # Returns
        - float: The score of the document.
        """
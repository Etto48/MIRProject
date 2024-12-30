from typing import Any, Callable, Optional, Protocol

from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.term import Term


class ScoringFunction(Protocol):
    batched_call: Optional[Callable[["ScoringFunction",list[str],str], list[float]]] = None
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
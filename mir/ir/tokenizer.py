from abc import abstractmethod
from typing import Protocol

from mir.ir.document_contents import DocumentContents
from mir.ir.token_ir import Token


class Tokenizer(Protocol):
    @abstractmethod
    def tokenize_query(self, query: str) -> list[Token]:
        """
        Tokenize a query.

        # Parameters
        - query (str): The query to tokenize.

        # Returns
        - list[Token]: The tokens of the query.
        """
    @abstractmethod
    def tokenize_document(self, doc: DocumentContents) -> list[Token]:
        """
        Tokenize a document.

        # Parameters
        - doc (DocumentContents): The document to tokenize.

        # Returns
        - list[Token]: The tokens of the document.
        """
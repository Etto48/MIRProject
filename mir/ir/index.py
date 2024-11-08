from abc import abstractmethod
from collections.abc import Generator
from typing import Any, Optional, Protocol
from tqdm.auto import tqdm

from mir.ir.document_info import DocumentInfo
from mir.ir.document_contents import DocumentContents
from mir.ir.posting import Posting
from mir.ir.term import Term
from mir.ir.tokenizer import Tokenizer
from mir.utils.sized_generator import SizedGenerator


class Index(Protocol):
    def get_global_info(self) -> dict[str, Any]:
        """
        Get global info from the index.

        # Returns
        - dict[str, int]: A dictionary with global info.
        """
        return {}

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
    def get_document_info(self, doc_id: int) -> DocumentInfo:
        """
        Get document info from a doc_id.

        # Parameters
        - doc_id (int): The doc_id.

        # Returns
        - DocumentInfo: The document info related to the doc_id.
        """
    
    def get_document_contents(self, doc_id: int) -> DocumentContents:
        """
        Get document contents from a doc_id.

        # Parameters
        - doc_id (int): The doc_id.

        # Returns
        - DocumentContents: The document contents related to the doc_id.
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
    def __len__(self) -> int:
        """
        Get the number of documents in the index.

        # Returns
        - int: The number of documents in the index.
        """

    @abstractmethod
    def index_document(self, doc: DocumentContents, tokenizer: Tokenizer) -> None:
        """
        Add a document to the index.

        # Parameters
        - doc (DocumentContents): The document to add to the index.
        - tokenizer (Tokenizer): The tokenizer to use to tokenize the document.
        """

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], tokenizer: Tokenizer, verbose: bool = False) -> None:
        """
        Add multiple documents to the index, this calls index_document for each document.

        # Parameters
        - docs (SizedGenerator[DocumentContents, None, None]): A generator of documents to add to the index.
        - tokenizer (Tokenizer): The tokenizer to use to tokenize the documents.
        - verbose (bool): Whether to show a progress bar.
        """
        for doc in tqdm(docs, desc="Indexing documents", disable=not verbose, total=len(docs)):
            self.index_document(doc, tokenizer)
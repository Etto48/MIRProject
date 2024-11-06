from collections import OrderedDict
from collections.abc import Generator
import os
import pickle
from typing import Optional
from mir import DATA_DIR
from mir.ir.document import Document
from mir.ir.document_contents import DocumentContents
from mir.ir.index import Index
from mir.ir.posting import Posting
from mir.ir.term import Term
from mir.ir.tokenizer import Tokenizer
from mir.utils.types import SizedGenerator


class DefaultIndex(Index):
    def __init__(self, path: Optional[str] = None):
        super().__init__()
        self.postings: list[OrderedDict[Posting]] = []
        self.documents: list[Document] = []
        self.terms: list[Term] = []
        self.term_lookup: dict[str, int] = {}
        self.path = None
        if path is not None:
            self.path = path
            if os.path.exists(path):
                with open(path, "rb") as f:
                    self.postings, self.documents, self.terms, self.term_lookup = pickle.load(f)
    
    def get_postings(self, term_id: int) -> Generator[Posting, None, None]:
        for doc_id, posting in self.postings[term_id].items():
            yield posting

    def get_document(self, doc_id: int) -> Document:
        return self.documents[doc_id]

    def get_term(self, term_id: int) -> Term:
        return self.terms[term_id]

    def get_term_id(self, term: str) -> Optional[int]:
        return self.term_lookup.get(term)

    def __len__(self) -> int:
        return len(self.documents)

    def index_document(self, doc: DocumentContents, tokenizer: Tokenizer) -> None:
        terms = tokenizer.tokenize_document(doc)
        term_ids = []
        for term in terms:
            if term.token not in self.term_lookup:
                term_id = len(self.terms)
                self.terms.append(Term(term.token, term_id))
                self.term_lookup[term.token] = term_id
            else:
                term_id = self.term_lookup[term.token]
            term_ids.append(term_id)
        doc_id = len(self.documents)
        self.documents.append(Document(doc, doc_id))
        for term_id in term_ids:
            if term_id >= len(self.postings):
                self.postings.append(OrderedDict())
            self.postings[term_id][doc_id] = Posting(doc_id)

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], tokenizer: Tokenizer, verbose: bool = False) -> None:
        super().bulk_index_documents(docs, tokenizer, verbose)
        if self.path is not None:
            with open(self.path, "wb") as f:
                pickle.dump((self.postings, self.documents, self.terms, self.term_lookup), f)
from collections import OrderedDict
import os
import pickle
from typing import Optional
import nltk
from collections.abc import Generator
from mir import DATA_DIR
from mir.ir.document import Document
from mir.ir.document_contents import DocumentContents
from mir.ir.ir import Ir
from mir.ir.posting import Posting
from mir.ir.term import Term
from mir.utils.types import SizedGenerator


class NaiveIr(Ir):
    def __init__(self):
        super().__init__()
        self.postings: list[OrderedDict[Posting]] = []
        self.documents: list[Document] = []
        self.terms: list[Term] = []
        self.term_lookup: dict[str, int] = {}

        if os.path.exists(f"{DATA_DIR}/naive_ir.pkl"):
            with open(f"{DATA_DIR}/naive_ir.pkl", "rb") as f:
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

    def index_document(self, doc: DocumentContents) -> None:
        terms = self.tokenizer.tokenize_document(doc)
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

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], verbose: bool = False) -> None:
        ret = super().bulk_index_documents(docs, verbose)
        with open(f"{DATA_DIR}/naive_ir.pkl", "wb") as f:
            pickle.dump((self.postings, self.documents, self.terms, self.term_lookup), f)


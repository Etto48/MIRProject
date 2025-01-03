from collections import OrderedDict
from collections.abc import Generator
import os
import pickle
from typing import Any, Optional
from mir.ir.document_info import DocumentInfo
from mir.ir.document_contents import DocumentContents
from mir.ir.index import Index
from mir.ir.posting import Posting
from mir.ir.term import Term
from mir.ir.token_ir import TokenLocation
from mir.ir.tokenizer import Tokenizer
from mir.utils.sized_generator import SizedGenerator


class DefaultIndex(Index):
    def __init__(self, path: Optional[str] = None):
        super().__init__()
        self.postings: list[OrderedDict[Posting]] = []
        self.document_info: list[DocumentInfo] = []
        self.document_contents: list[DocumentContents] = []
        self.terms: list[Term] = []
        self.term_lookup: dict[str, int] = {}
        self.path = None
        self.total_field_lengths = {
            "author": 0,
            "title": 0,
            "body": 0
        }
        if path is not None:
            self.path = path
            if os.path.exists(path):
                self.load()
    
    def get_postings(self, term_id: int) -> Generator[Posting, None, None]:
        for doc_id, posting in self.postings[term_id].items():
            yield posting

    def get_document_info(self, doc_id: int) -> DocumentInfo:
        return self.document_info[doc_id]
    
    def get_document_contents(self, doc_id: int) -> DocumentContents:
        return self.document_contents[doc_id]

    def get_term(self, term_id: int) -> Term:
        return self.terms[term_id]

    def get_term_id(self, term: str) -> Optional[int]:
        return self.term_lookup.get(term)
    
    def get_global_info(self) -> dict[str, Any]:
        return {
            "avg_field_lengths": {
                "author": self.total_field_lengths["author"] / len(self.document_info),
                "title": self.total_field_lengths["title"] / len(self.document_info),
                "body": self.total_field_lengths["body"] / len(self.document_info)
            },
            "num_docs": len(self.document_info)
        }

    def __len__(self) -> int:
        return len(self.document_info)

    def index_document(self, doc: DocumentContents, tokenizer: Tokenizer) -> None:
        terms = tokenizer.tokenize_document(doc)
        author_length = sum(1 for term in terms if term.location == TokenLocation.AUTHOR)
        title_length = sum(1 for term in terms if term.location == TokenLocation.TITLE)
        body_length = sum(1 for term in terms if term.location == TokenLocation.BODY)
        self.total_field_lengths["author"] += author_length
        self.total_field_lengths["title"] += title_length
        self.total_field_lengths["body"] += body_length
        term_ids = []
        for term in terms:
            if term.text not in self.term_lookup:
                term_id = len(self.terms)
                self.terms.append(Term(term.text, term_id))
                self.term_lookup[term.text] = term_id
            else:
                term_id = self.term_lookup[term.text]
            term_ids.append(term_id)
        doc_id = len(self.document_info)
        self.document_info.append(DocumentInfo.from_document_contents(doc_id, doc, tokenizer))
        self.document_contents.append(doc)
        for term_id in term_ids:
            if term_id >= len(self.postings):
                self.postings.append(OrderedDict())
            self.postings[term_id][doc_id] = Posting(doc_id, term_id)

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], tokenizer: Tokenizer, verbose: bool = False) -> None:
        super().bulk_index_documents(docs, tokenizer, verbose)
        if self.path is not None:
            self.save()

    def load(self):
        if self.path is not None:
            try:
                with open(self.path, "rb") as f:
                    postings, document_info, document_contents, terms, term_lookup = pickle.load(f)
                assert isinstance(postings, list)
                assert isinstance(document_info, list)
                assert isinstance(document_contents, list)
                assert isinstance(terms, list)
                assert isinstance(term_lookup, dict)
            except Exception as e:
                pass
            else:
                self.postings = postings
                self.document_info = document_info
                self.document_contents = document_contents
                self.terms = terms
                self.term_lookup = term_lookup
        else:
            raise ValueError("Path not set for index.")

    def save(self):
        if self.path is not None:
            with open(self.path, "wb") as f:
                pickle.dump((self.postings, self.document_info, self.document_contents, self.terms, self.term_lookup), f)
        else:
            raise ValueError("Path not set for index.")
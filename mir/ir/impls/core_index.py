from collections import OrderedDict
from collections.abc import Generator
import math
from typing import Any, Optional, Tuple
from mir.ir.document_contents import DocumentContents
from mir.ir.document_info import DocumentInfo
from mir.ir.index import Index
from mir.ir.posting import Posting
from mir.ir.term import Term
from mir.ir.token_ir import Token, TokenLocation
from mir.ir.tokenizer import Tokenizer
from mir.utils.sized_generator import SizedGenerator


class CoreIndex(Index):
    def __init__(self) :
        super().__init__()
        self.postings: list[OrderedDict[int,Posting]] = []
        self.document_info: list[DocumentInfo] = []
        self.document_contents: list[DocumentContents] = []
        self.terms: list[Term] = []
        self.term_lookup: dict[str, int] = {}
        self.global_info: dict[str, Any] = {}

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
        return self.global_info

    def __len__(self) -> int:
        return len(self.document_info)
    
    def _map_terms_to_ids(self, terms: list[Token]) -> list[int]:
        term_ids = []
        for term in terms:
            if term.token not in self.term_lookup:
                term_id = len(self.terms)
                self.terms.append(Term(term.token, term_id))
                self.term_lookup[term.token] = term_id
            else:
                term_id = self.term_lookup[term.token]
            term_ids.append(term_id)
        
        return term_ids
    
    def _update_postings(self, term_ids: list[int], term_list: list[Token], doc_id: int, field: str) -> None:
        for term_id, token in zip(term_ids, term_list):
            if term_id >= len(self.postings):
                self.postings.append(OrderedDict())
            # Se la posting per il documento non esiste, creala
            if doc_id not in self.postings[term_id]:
                self.postings[term_id][doc_id] = Posting(doc_id, term_id)
            posting = self.postings[term_id][doc_id]
            posting.occurrences[field].append(token.position)

    def _group_terms(self, terms: list[Token]) -> Tuple[list[Token], list[Token], list[Token]]:
        author_terms:list[Token] = []
        title_terms : list[Token] = []
        body_terms : list[Token] = []
        for term in terms:
            match term.where:
                case TokenLocation.AUTHOR:
                    author_terms.append(term)
                case TokenLocation.TITLE:
                    title_terms.append(term)
                case TokenLocation.BODY:
                    body_terms.append(term)
                case _:
                    raise ValueError(f"Invalid token location {term.where}")
        return author_terms, title_terms, body_terms

    def index_document(self, doc: DocumentContents, tokenizer: Tokenizer) -> None:
        terms = tokenizer.tokenize_document(doc)

        author_terms, title_terms, body_terms = self._group_terms(terms)

        author_term_ids = self._map_terms_to_ids(author_terms)
        title_term_ids = self._map_terms_to_ids(title_terms)
        body_term_ids = self._map_terms_to_ids(body_terms)
        
        doc_id = len(self.document_info)
        self.document_info.append(DocumentInfo.from_document_contents(doc_id, doc, tokenizer))
        self.document_contents.append(doc)

        self._update_postings(author_term_ids, author_terms, doc_id, 'author')
        self._update_postings(title_term_ids, title_terms, doc_id, 'title')
        self._update_postings(body_term_ids, body_terms, doc_id, 'body')

    def _compute_avg_field_lengths(self) -> dict[str, float]:
        avg_author_length, avg_title_length, avg_body_length = 0, 0, 0
        for doc in self.document_info:
            avg_author_length += doc.lengths[0]
            avg_title_length += doc.lengths[1]
            avg_body_length += doc.lengths[2]
        avg_author_length /= len(self.document_info)
        avg_title_length /= len(self.document_info)
        avg_body_length /= len(self.document_info)

        avg_filed_lengths = {
            "author": avg_author_length,
            "title": avg_title_length,
            "body": avg_body_length
        }

        return avg_filed_lengths

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], tokenizer: Tokenizer, verbose: bool = False) -> None:
        print("Bulk indexing documents")
        super().bulk_index_documents(docs, tokenizer, verbose)
        self.global_info["avg_field_lengths"] = self._compute_avg_field_lengths()
        N = len(self.document_contents)
        for term_id, postings in enumerate(self.postings):
            self.terms[term_id].info['idf'] = (N/len(postings))
from collections import OrderedDict
from collections.abc import Generator
import math
import os
from typing import Any, Optional, Tuple
from mir.fs_collections.cached_hmap import CachedHMap
from mir.fs_collections.cached_list import CachedList
from mir.fs_collections.file_hmap import FileHMap
from mir.fs_collections.file_list import FileList
from mir.fs_collections.hashable_key.impls.str_hk import StrHK
from mir.fs_collections.serde import INT_SERDE
from mir.ir.document_contents import DOCUMENT_CONTENTS_SERDE, DocumentContents
from mir.ir.document_info import DOCUMENT_INFO_SERDE, DocumentInfo
from mir.ir.serializable.posting_list import POSTING_LIST_SERDE, PostingList
from mir.ir.index import Index
from mir.ir.posting import Posting
from mir.ir.term import TERM_SERDE, Term
from mir.ir.token_ir import Token, TokenLocation
from mir.ir.tokenizer import Tokenizer
from mir.utils.sized_generator import SizedGenerator

from mir import DATA_DIR
import json

class CoreIndex(Index):
    def __init__(self, folder: str = None):
        super().__init__()

        self.basedir = folder if folder is not None else DATA_DIR

        cache_size = 1024

        postings_file = FileList(os.path.join(self.basedir,"postings.index"), os.path.join(self.basedir,"postings.data"))
        self.postings = CachedList(postings_file, cache_size, POSTING_LIST_SERDE)

        document_info_file = FileList(os.path.join(self.basedir,"document_info.index"), os.path.join(self.basedir,"document_info.data"))
        self.document_info = CachedList(document_info_file, cache_size, DOCUMENT_INFO_SERDE)

        document_contents_file = FileList(os.path.join(self.basedir,"document_contents.index"), os.path.join(self.basedir,"document_contents.data"))
        self.document_contents = CachedList(document_contents_file, cache_size, DOCUMENT_CONTENTS_SERDE)

        terms_file = FileList(os.path.join(self.basedir,"terms.index"), os.path.join(self.basedir,"terms.data"))
        self.terms = CachedList(terms_file, cache_size, TERM_SERDE)
        
        term_lookup_file = FileHMap(os.path.join(self.basedir,"term_lookup.index"), os.path.join(self.basedir,"term_lookup.data"))
        self.term_lookup = CachedHMap(term_lookup_file, cache_size, INT_SERDE)
        
        self.global_info: dict[str, Any] = {} # serializzazione json
        # posting lenghts: dict[int, int] 
        self.global_info["posting_lengths"] = {}
        self.global_info["avg_field_lengths"] = {
            "author": 0,
            "title": 0,
            "body": 0
        }
        self.global_info["num_docs"] = 0


    def get_postings(self, term_id: int) -> Generator[Posting, None, None]:
        for _, posting in self.postings[term_id].items():
            yield posting

    def get_document_info(self, doc_id: int) -> DocumentInfo:
        return self.document_info[doc_id]
    
    def get_document_contents(self, doc_id: int) -> DocumentContents:
        return self.document_contents[doc_id]

    def get_term(self, term_id: int) -> Term:
        return self.terms[term_id]

    def get_term_id(self, term: str) -> Optional[int]:
        return self.term_lookup[StrHK(term)]
    
    def get_global_info(self) -> dict[str, Any]:
        return self.global_info

    def __len__(self) -> int:
        return self.global_info["num_docs"]
    
    def _map_terms_to_ids(self, terms: list[Token]) -> list[int]:
        term_ids = []
        for term in terms:
            match self.term_lookup[StrHK(term.token)]:
                case None:
                    term_id = self.terms.next_key()
                    self.terms.append(Term(term.token, term_id))
                    self.term_lookup[StrHK(term.token)] = term_id
                    self.global_info["posting_lengths"][term_id] = 0
                case already_mapped:
                    term_id = already_mapped
            term_ids.append(term_id)
        
        return term_ids
    
    def _update_postings(self, term_ids: list[int], term_list: list[Token], doc_id: int, field: str) -> None:
        for term_id, token in zip(term_ids, term_list):
            if term_id >= self.postings.next_key():
                self.postings.append(PostingList())
            # Se la posting per il documento non esiste, creala
            if doc_id not in self.postings[term_id]:
                self.postings[term_id][doc_id] = Posting(doc_id, term_id)
                term_pll = self.terms[term_id].info.get('posting_list_len', 0) 
                term_pll += 1
                self.terms[term_id].info['posting_list_len'] = term_pll
            posting = self.postings[term_id][doc_id]
            # OCCURENCES NON é UNA LISTA DI OFFSETS, MA UN NUMERO DI OCCORRENZE
            # posting.occurrences[field].append(token.position)
            posting.occurrences[field] += 1

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

        self.global_info["num_docs"] += 1

        author_terms, title_terms, body_terms = self._group_terms(terms)

        author_term_ids = self._map_terms_to_ids(author_terms)
        title_term_ids = self._map_terms_to_ids(title_terms)
        body_term_ids = self._map_terms_to_ids(body_terms)
        
        doc_id = self.document_info.next_key()
        if doc.__dict__.get("doc_id") is not None:
            assert doc_id == doc.doc_id, f"Indexing document with id {doc.doc_id} but expected {doc_id}, document ids out of order or duplicated"
        doc_info = DocumentInfo.from_document_contents(doc_id, doc, tokenizer)
        self.document_info.append(doc_info)
        self.document_contents.append(doc)

        self._sum_up_lengths(doc_info.lengths)

        self._update_postings(author_term_ids, author_terms, doc_id, 'author')
        self._update_postings(title_term_ids, title_terms, doc_id, 'title')
        self._update_postings(body_term_ids, body_terms, doc_id, 'body')


    def _sum_up_lengths(self, lengths: list[int]) -> None:
        avg_author_length = self.global_info["avg_field_lengths"]["author"]
        avg_title_length = self.global_info["avg_field_lengths"]["title"]
        avg_body_length = self.global_info["avg_field_lengths"]["body"]

        avg_author_length += lengths[0]
        avg_title_length += lengths[1]
        avg_body_length += lengths[2]

        self.global_info["avg_field_lengths"]["author"] = avg_author_length
        self.global_info["avg_field_lengths"]["title"] = avg_title_length
        self.global_info["avg_field_lengths"]["body"] = avg_body_length


    def _compute_avg_field_lengths(self) -> dict[str, float]:
        avg_author_length = self.global_info["avg_field_lengths"]["author"]
        avg_title_length = self.global_info["avg_field_lengths"]["title"]
        avg_body_length = self.global_info["avg_field_lengths"]["body"]
        
        avg_author_length /= self.global_info["num_docs"]
        avg_title_length /= self.global_info["num_docs"]
        avg_body_length /= self.global_info["num_docs"]

        avg_filed_lengths = {
            "author": avg_author_length,
            "title": avg_title_length,
            "body": avg_body_length
        }

        return avg_filed_lengths

    def bulk_index_documents(self, docs: SizedGenerator[DocumentContents, None, None], tokenizer: Tokenizer, verbose: bool = False) -> None:
        super().bulk_index_documents(docs, tokenizer, verbose)
        self.global_info["avg_field_lengths"] = self._compute_avg_field_lengths()


    def save(self) -> None:
        with open(os.path.join(self.basedir, "global_info.json"), "w") as f:
            del self.global_info["posting_lengths"]
            json.dump(self.global_info, f)

        self.postings.write()
        self.document_info.write()
        self.document_contents.write()
        self.terms.write()
        self.term_lookup.write()


    @staticmethod
    def load(folder: str = None) -> 'CoreIndex':
        index = CoreIndex(folder)
        global_info_path = os.path.join(index.basedir, "global_info.json")
        if os.path.exists(global_info_path):
            with open(global_info_path, "r") as f:
                index.global_info = json.load(f)
        return index
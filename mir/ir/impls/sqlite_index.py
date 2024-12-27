from collections import OrderedDict
from collections.abc import Generator
import os
import sqlite3
from typing import Any, Optional
from mir.ir.document_info import DocumentInfo
from mir.ir.document_contents import DocumentContents
from mir.ir.impls.default_tokenizers import DefaultTokenizer
from mir.ir.index import Index
from mir.ir.posting import Posting
from mir.ir.term import Term
from mir.ir.token_ir import TokenLocation
from mir.ir.tokenizer import Tokenizer


class SqliteIndex(Index):
    def __init__(self, path: Optional[str] = None):
        super().__init__()

        self.connection = sqlite3.connect(path if path is not None else ":memory:", autocommit=False)
        
        self.connection.autocommit = True

        self.connection.execute("pragma synchronous = off")
        self.connection.execute(f"pragma threads = {os.cpu_count()}")
        self.connection.execute("pragma journal_mode = WAL")
        self.connection.execute(f"pragma cache_size = -{1024*1024}")
        self.connection.execute(f"pragma mmap_size = {1024*1024*1024}")
        self.connection.execute("pragma temp_store = memory")

        self.connection.autocommit = False

        self.connection.execute(
            "create table if not exists postings "
            "(term_id integer references terms(term_id) not null, "
            "doc_id integer references document_info(doc_id) not null, "
            "occurrences_author integer not null, "
            "occurrences_title integer not null, "
            "occurrences_body integer not null, "
            "primary key (term_id, doc_id))")
        self.connection.execute(
            "create table if not exists document_info "
            "(doc_id integer not null primary key autoincrement, "
            "author_len integer not null, "
            "title_len integer not null, "
            "body_len integer not null)")
        self.connection.execute(
            "create table if not exists document_contents "
            "(doc_id integer not null primary key references document_info(doc_id), "
            "author text, "
            "title text, "
            "body text)")
        self.connection.execute(
            "create table if not exists terms "
            "(term_id integer not null primary key autoincrement, "
            "term text unique not null, "
            "posting_list_len integer not null)")
        
        self.connection.execute("create table if not exists global_info (key text not null primary key, value integer)")
        # add global info default values if not present
        self.connection.execute("insert or ignore into global_info values ('total_author_len', 0)")
        self.connection.execute("insert or ignore into global_info values ('total_title_len', 0)")
        self.connection.execute("insert or ignore into global_info values ('total_body_len', 0)")
        self.connection.execute("insert or ignore into global_info values ('num_docs', 0)")

        self.connection.execute("pragma optimize")

        self.connection.commit()
        self.global_info_dirty = True 
        self.cached_global_info = None
    
    def get_postings(self, term_id: int) -> Generator[Posting, None, None]:
        cursor = self.connection.cursor()
        cursor.execute(
            "select doc_id, occurrences_author, occurrences_title, occurrences_body from postings where term_id = ? "
            "order by doc_id", (term_id,))
        def row_factory(_cursor, row):
            return Posting(row[0], term_id, {"author": row[1], "title": row[2], "body": row[3]})
        cursor.row_factory = row_factory
        yield from cursor

    def get_document_info(self, doc_id: int) -> DocumentInfo:
        cursor = self.connection.cursor()
        cursor.execute("select author_len, title_len, body_len from document_info where doc_id = ?", (doc_id,))
        author_len, title_len, body_len = cursor.fetchone()
        return DocumentInfo(doc_id, [author_len, title_len, body_len])
    
    def get_document_contents(self, doc_id: int) -> DocumentContents:
        cursor = self.connection.cursor()
        cursor.execute("select author, title, body from document_contents where doc_id = ?", (doc_id,))
        author, title, body = cursor.fetchone()
        return DocumentContents(author, title, body)

    def get_term(self, term_id: int) -> Term:
        cursor = self.connection.cursor()
        cursor.execute("select term, posting_list_len from terms where term_id = ?", (term_id,))
        term, posting_list_len = cursor.fetchone()
        return Term(term, term_id, posting_list_len=posting_list_len)

    def get_term_id(self, term: str) -> Optional[int]:
        cursor = self.connection.cursor()
        cursor.execute("select term_id from terms where term = ?", (term,))
        result = cursor.fetchone()
        return result[0] if result is not None else None
    
    def get_global_info(self) -> dict[str, Any]:
        if self.global_info_dirty:
            cursor = self.connection.cursor()
            cursor.execute("select key, value from global_info")
            global_info = cursor.fetchall()
            global_info = {key: value for key, value in global_info}
            self.cached_global_info = {
                "avg_field_lengths": {
                    "author": global_info["total_author_len"] / global_info["num_docs"],
                    "title": global_info["total_title_len"] / global_info["num_docs"],
                    "body": global_info["total_body_len"] / global_info["num_docs"]
                },
                "num_docs": global_info["num_docs"]
            }
            self.global_info_dirty = False
        return self.cached_global_info

    def __len__(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute("select value from global_info where key = 'num_docs'")
        return cursor.fetchone()[0]

    def _increment_field_lengths(self, author_len: int, title_len: int, body_len: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute("update global_info set value = value + ? where key = 'total_author_len'", (author_len,))
        cursor.execute("update global_info set value = value + ? where key = 'total_title_len'", (title_len,))
        cursor.execute("update global_info set value = value + ? where key = 'total_body_len'", (body_len,))

    def _create_or_get_term_id(self, term: str) -> int:
        cursor = self.connection.cursor()
        cursor.execute("insert or ignore into terms(term, posting_list_len) values (?, 0)", (term,))
        cursor.execute("select term_id from terms where term = ?", (term,))
        return cursor.fetchone()[0]

    def _new_document(self, doc: DocumentContents, author_len: int, title_len: int, body_len: int) -> int:
        cursor = self.connection.cursor()
        if doc.__dict__.get("doc_id") is not None:
            cursor.execute("insert into document_info(doc_id, author_len, title_len, body_len) values (?, ?, ?, ?)", (doc.doc_id, author_len, title_len, body_len))
        else:
            cursor.execute("insert into document_info(author_len, title_len, body_len) values (?, ?, ?)", (author_len, title_len, body_len))
        doc_id = cursor.lastrowid
        cursor.execute("insert into document_contents(doc_id, author, title, body) values (?, ?, ?, ?)", (doc_id, doc.author, doc.title, doc.body))
        cursor.execute("update global_info set value = value + 1 where key = 'num_docs'")
        return doc_id

    def _update_postings(self, term_id: int, doc_id: int, location: TokenLocation) -> None:
        increments = {
            "author": 1 if location == TokenLocation.AUTHOR else 0, 
            "title": 1 if location == TokenLocation.TITLE else 0, 
            "body": 1 if location == TokenLocation.BODY else 0
        }
        cursor = self.connection.cursor()
        cursor.execute("select occurrences_author, occurrences_title, occurrences_body from postings where term_id = ? and doc_id = ?", (term_id, doc_id))
        result = cursor.fetchone()
        if result is None:
            cursor.execute(
                "insert into postings(term_id, doc_id, occurrences_author, occurrences_title, occurrences_body) "
                "values (?, ?, ?, ?, ?)", (term_id, doc_id, increments["author"], increments["title"], increments["body"]))
        else:
            cursor.execute(
                "update postings set occurrences_author = occurrences_author + ?, occurrences_title = occurrences_title + ?, "
                "occurrences_body = occurrences_body + ? where term_id = ? and doc_id = ?",
                (increments["author"], increments["title"], increments["body"], term_id, doc_id))

    def _contains_document(self, doc_id: int) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("select count(*) from document_info where doc_id = ?", (doc_id,))
        ret = cursor.fetchone()[0]
        return ret > 0

    def _increment_posting_list_len(self, term_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute("update terms set posting_list_len = posting_list_len + 1 where term_id = ?", (term_id,))

    def index_document(self, doc: DocumentContents, tokenizer: Tokenizer) -> None:

        if doc.__dict__.get("doc_id") is not None:
            if self._contains_document(doc.doc_id):
                return
        self.global_info_dirty = True

        terms = tokenizer.tokenize_document(doc)
        author_length = sum(1 for term in terms if term.where == TokenLocation.AUTHOR)
        title_length = sum(1 for term in terms if term.where == TokenLocation.TITLE)
        body_length = sum(1 for term in terms if term.where == TokenLocation.BODY)
        
        self._increment_field_lengths(author_length, title_length, body_length)

        encountered_terms = set()
        term_ids_and_locations = []
        for term in terms:
            term_id = self._create_or_get_term_id(term.token)
            if term_id not in encountered_terms:
                self._increment_posting_list_len(term_id)
            encountered_terms.add(term_id)
            term_ids_and_locations.append((term_id, term.where))
        doc_id = self._new_document(doc, author_length, title_length, body_length)
        for term_id, location in term_ids_and_locations:
            self._update_postings(term_id, doc_id, location)
        self.connection.commit()

    def bulk_index_documents(self, docs, tokenizer, verbose = False):
        super().bulk_index_documents(docs, tokenizer, verbose)
        self.connection.execute("pragma optimize")
        self.connection.commit()

if __name__ == "__main__":
    index = SqliteIndex()
    tokenizer = DefaultTokenizer()
    docs = [
        DocumentContents("author1", "title1", "token1 token2 token3"),
        DocumentContents("author2", "title2", "token4 token5 token6"),
        DocumentContents("author3", "title3", "token2 token4 token6"),
        DocumentContents("author4", "title4", "token1 token3 token5"),
        DocumentContents("author5", "title5", "token1 token2 token6"),
        DocumentContents("author6", "title6", "token3 token4 token5")
    ]
    for doc in docs:
        index.index_document(doc, tokenizer)

    print(index.get_global_info())

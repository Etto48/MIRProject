from collections import OrderedDict
from typing import Optional
import string
import nltk
from nltk.stem import StemmerI
from collections.abc import Generator
from mir.ir.document import Document
from mir.ir.document_contents import DocumentContents
from mir.ir.ir import Ir
from mir.ir.posting import Posting
from mir.ir.term import Term
from mir.ir.token import Token


class TokenizerIr(Ir):
    def __init__(self):
        self.postings: list[OrderedDict[Posting]] = []
        self.documents: list[Document] = []
        self.terms: list[Term] = []
        self.term_lookup: dict[str, int] = {}
        self.stopwords = set(nltk.corpus.stopwords.words("english"))
        self.stemmer = nltk.SnowballStemmer("english")
    
    def get_postings(self, term_id: int) -> Generator[Posting, None, None]:
        for doc_id, posting in self.postings[term_id].items():
            yield posting

    def get_document(self, doc_id: int) -> Document:
        return self.documents[doc_id]

    def get_term(self, term_id: int) -> Term:
        return self.terms[term_id]

    def get_term_id(self, term: str) -> Optional[int]:
        return self.term_lookup.get(term)

    def process_document(self, document_content: DocumentContents) -> list:
        
        # 1 - Token creation 
        title_list = document_content.title.translate(str.maketrans('','', string.punctuation)).lower().split()
        body_list = document_content.body.translate(str.maketrans('','', string.punctuation)).lower().split()
        
        token_list = []


        # 2 - Processing Title
        for idx, tword in enumerate(title_list) :

            # 2a - Stemming title words 
            tword = self.stemmer.stem(tword)

            # No Stopwords removal for title
            if not tword in self.stopwords : 
                token_list.append(Token(tword, True, idx))


        # 3 - Processing Body    
        for idx, bword in enumerate(body_list) :

            # 3a - Stemming body words
            bword = self.stemmer.stem(bword)

            # 3b - If clause removes Stopwords in Body
            if not bword in self.stopwords : 
                token_list.append(Token(bword, False, idx))

        # Returns list of tokens
        return token_list


    def process_query(self, query: str) -> list[str]:
        query_tokens = query.lower().split()
        return [token for token in query_tokens if token not in self.stopwords]

    def score(self, document: Document, postings: list[Posting], query: list[Term]) -> float:
        return float(len(postings))

    def index_document(self, doc: DocumentContents) -> None:
        terms = self.process_document(doc)
        term_ids = []
        for term in terms:
            if term not in self.term_lookup:
                term_id = len(self.terms)
                self.terms.append(Term(term, term_id))
                self.term_lookup[term] = term_id
            else:
                term_id = self.term_lookup[term]
            term_ids.append(term_id)
        doc_id = len(self.documents)
        self.documents.append(Document(doc, doc_id))
        for term_id in term_ids:
            if term_id >= len(self.postings):
                self.postings.append(OrderedDict())
            self.postings[term_id][doc_id] = Posting(doc_id)

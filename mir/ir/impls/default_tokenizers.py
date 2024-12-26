import string
import nltk
import nltk.corpus
from mir import DATA_DIR
from mir.ir.document_contents import DocumentContents
from mir.ir.tokenizer import Tokenizer
from mir.ir.token_ir import Token, TokenLocation


class DefaultTokenizer(Tokenizer):
    def __init__(self):
        download_dir = f"{DATA_DIR}/nltk_data"
        nltk.download("stopwords", quiet=True, download_dir=download_dir,)
        stopwords_from_path = nltk.data.find("corpora/stopwords/english", [download_dir])
        with open(stopwords_from_path) as f:
            self.stopwords = frozenset(f.read().splitlines())
        
        self.stemmer = nltk.SnowballStemmer("english")
        self.remove_punctuation = str.maketrans('','', string.punctuation)

    def tokenize_query(self, query: str) -> list[Token]:
        query_list = query.translate(self.remove_punctuation).lower().split()
        token_list = []

        for idx, word in enumerate(query_list) :
            # No stopwords removal for query
            word = self.stemmer.stem(word)
            token_list.append(Token(word, TokenLocation.QUERY, idx)) 
        
        return token_list

    def tokenize_document(self, doc: DocumentContents) -> list[Token]:
        author_list = doc.author.translate(self.remove_punctuation).lower().split()
        title_list = doc.title.translate(self.remove_punctuation).lower().split()
        body_list = doc.body.translate(self.remove_punctuation).lower().split()
        
        token_list = []

        for idx, aword in enumerate(author_list):
            # No Stopwords removal for author
            aword = self.stemmer.stem(aword)
            token_list.append(Token(aword, TokenLocation.AUTHOR, idx))

        for idx, tword in enumerate(title_list):
            # No Stopwords removal for title
            tword = self.stemmer.stem(tword)
            token_list.append(Token(tword, TokenLocation.TITLE, idx))

        for idx, bword in enumerate(body_list):
            if bword not in self.stopwords: 
                bword = self.stemmer.stem(bword)
                token_list.append(Token(bword, TokenLocation.BODY, idx))
        
        return token_list
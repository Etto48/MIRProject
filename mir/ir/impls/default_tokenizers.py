import string
import nltk
import nltk.corpus
import unidecode
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
        self.remove_punctuation = str.maketrans(string.punctuation, " " * len(string.punctuation))
        self.separate_numbers = str.maketrans({key: f" {key} " for key in string.digits})
    
    def preprocess(self, text: str):
        # normalize unicode
        text = unidecode.unidecode(text, errors="replace", replace_str=" ")
        # replace punctuation with space
        text = text.translate(self.remove_punctuation).lower()
        # separate numbers with a space
        text = text.translate(self.separate_numbers)
        # split text into words
        words = text.split()
        # remove stopwords
        words = [word for word in words if word not in self.stopwords]
        # stem words
        words: list[str] = [self.stemmer.stem(word) for word in words]
        return words


    def tokenize_query(self, query: str) -> list[Token]:
        query_list = self.preprocess(query)
        token_list = [Token(word, TokenLocation.QUERY) for word in query_list]
        
        return token_list

    def tokenize_document(self, doc: DocumentContents) -> list[Token]:
        author_list = self.preprocess(doc.author)
        title_list = self.preprocess(doc.title)
        body_list = self.preprocess(doc.body)
        
        token_list = \
            [Token(aword, TokenLocation.AUTHOR) for aword in author_list] + \
            [Token(tword, TokenLocation.TITLE) for tword in title_list] + \
            [Token(bword, TokenLocation.BODY) for bword in body_list]
        
        return token_list
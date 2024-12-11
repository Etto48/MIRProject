import json
import warnings
import sentence_transformers

from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.scoring_function import ScoringFunction
from mir.ir.term import Term


class NeuralScoringFunction(ScoringFunction):
    def __init__(self):
        # Load the model
        model_name = "sentence-transformers/all-MiniLM-L12-v2"
        self.model = sentence_transformers.SentenceTransformer(model_name)

    def __call__(self, document: DocumentInfo, postings: list[Posting], query: list[Term], document_content: str, query_content: str, **kwargs) -> float:
        
        query_embedding = self.model.encode(query_content) 
        document_embedding = self.model.encode(document_content)
        score = self.model.similarity(query_embedding, document_embedding).item()
        return score
    
if __name__ == "__main__":
    scoring_function = NeuralScoringFunction()
    
    queries = [
        "What is the capital of France?",
        "Who is the president of the United States?"
    ]

    documents = [
        "The capital of France is Paris.",
        "The president of the United States is Joe Biden.",
        "The capital of Italy is Rome.",
        "The president of France is Emmanuel Macron.",
        "The capital of the United States is Washington, D.C.",
        "The president of Italy is Sergio Mattarella.",
        "Cookies are made with flour, sugar, and eggs.",
    ]

    for query in queries:
        for document in documents:
            score = scoring_function(None, None, None, document, query)
            print(f"Query: {query}\nDocument: {document}\nScore: {score}\n")


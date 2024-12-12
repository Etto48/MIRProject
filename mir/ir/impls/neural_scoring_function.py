import json
import warnings
import sentence_transformers
from tqdm.auto import tqdm

from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.scoring_function import ScoringFunction
from mir.ir.term import Term
from mir.neural_relevance.dataset import MSMarcoDataset


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
    valid = MSMarcoDataset.load("valid")
    scoring_function = NeuralScoringFunction()

    squared_error_sum = 0
    items = tqdm(range(len(valid)), "Computing scores")
    for i in items:
            query, document, relevance = valid[i]
            relevance = relevance.item()/5
            score = scoring_function(None, None, None, document, query)
            squared_error_sum += (relevance - score) ** 2
            items.set_postfix(mse=squared_error_sum / (i + 1))
    mse = squared_error_sum / len(valid)
    print(f"Mean squared error: {mse}") # Mean squared error: 0.12194208412600611


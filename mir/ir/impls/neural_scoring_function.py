import numpy as np
import torch
from tqdm.auto import tqdm

from mir import DATA_DIR
from mir.neural_relevance.model import NeuralRelevance
from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.scoring_function import ScoringFunction
from mir.ir.term import Term
from mir.neural_relevance.dataset import MSMarcoDataset


class NeuralScoringFunction(ScoringFunction):
    def __init__(self):
        # Load the model
        self.model = NeuralRelevance.load(f"{DATA_DIR}/neural_relevance.pth")
        self.model.eval()

    def __call__(self, document: DocumentInfo, postings: list[Posting], query: list[Term], *, document_content: str, query_content: str, **kwargs) -> float:
        if len(document_content) == 0 or len(query_content) == 0:
            return 0.0
        with torch.no_grad():
            score = self.model.forward_queries_and_documents([query_content], [document_content])
        return score.item()
    
if __name__ == "__main__":
    valid = MSMarcoDataset.load("valid")
    scoring_function = NeuralScoringFunction()

    squared_error_sum = 0
    bce = 0
    items = tqdm(range(len(valid)), "Computing scores")
    for i in items:
            query, document, relevance = valid[i]
            relevance = relevance.item()/5
            score = scoring_function(None, None, None, document, query)
            squared_error_sum += (relevance - score) ** 2
            bce += - relevance * np.log(score) - (1 - relevance) * np.log(1 - score)
            items.set_postfix(mse=squared_error_sum / (i + 1), bce=bce / (i + 1))
    mse = squared_error_sum / len(valid)
    bce /= len(valid)
    print(f"Mean squared error: {mse}")
    print(f"Binary cross-entropy: {bce}")

    # Mean squared error: 0.34285212729908354
    # Binary cross-entropy: 1.1249619396399861

    # Mean squared error: 0.043635161485957745
    # Binary cross-entropy: 0.44627394001071446


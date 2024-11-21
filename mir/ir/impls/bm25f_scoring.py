from typing import List, Dict
from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.term import Term
import math


class BM25FScoringFunction:
    def __init__(self, k1: float = 1.5, b: float = 0.75, field_weights: Dict[str, float] = None):
        """
        BM25F scoring function initialization.

        # Parameters
        - k1 (float): Term frequency saturation parameter.
        - b (float): Length normalization parameter.
        - field_weights (Dict[str, float]): Dictionary specifying weights for different fields.
        """
        self.k1 = k1
        self.b = b
        # Set default field weights if none are provided
        self.field_weights = field_weights or {'title': 2.0, 'body': 1.0,'author': 0.5}

    def __call__(self, document: DocumentInfo, postings: List[Posting], query: List[Term], **kwargs) -> float:
        """
        Calculate the BM25F score for a document with multiple fields.

        # Parameters
        - document (DocumentInfo): The document to score.
        - postings (List[Posting]): List of postings containing term frequencies for each field.
        - query (List[Term]): The query terms.

        # Returns
        - float: The BM25F score of the document.
        """
        score = 0.0
        avg_field_lengths = kwargs['avgdfl']  # Assume document provides average field lengths


        for term in query:
            weighted_tf = 0.0

            # Sum the weighted term frequencies across all fields
            for field, weight in self.field_weights.items():
                # Assume each posting has a method to get term frequency for a given field
                # ( I have to look for the posting corresponding to the term)
                # the term frequency 

                tf = 
                field_length = document.get_field_length(field)
                avg_length = avg_field_lengths.get(field, 1)  # Default to 1 if no avg length is found

                # BM25F field-specific term frequency component
                normalized_tf = tf / (1 + self.k1 * ((1 - self.b) + self.b * (field_length / avg_length)))
                weighted_tf += weight * normalized_tf

            # Add term contribution to the total score
            score += term.idf * weighted_tf * (self.k1 + 1) / (weighted_tf + self.k1)

        return score



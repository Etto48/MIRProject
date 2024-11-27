from typing import List, Dict
from mir.ir.document_info import DocumentInfo
from mir.ir.posting import Posting
from mir.ir.term import Term
import math


class BM25FScoringFunction:
    def __init__(self, k1: float = 1.5, b: float = 0.75, field_weights: Dict[str, float] = None, index = None):
        """
        BM25F scoring function initialization.

        # Parameters
        - k1 (float): Term frequency saturation parameter.
        - b (float): Length normalization parameter.
        - field_weights (Dict[str, float]): Dictionary specifying weights for different fields.
        """
        self.k1 = k1
        self.b = b
        self.index = index
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
        score = 0.0 #RSV


        for term in query:
           score += self._rsv(term,document,postings)

        return score

    def _rsv(self,term,document,postings):
        tfd = self._wtf(term,document,postings)
        score = (tfd/(self.k1+tfd))*math.log(term.idf)
        return score


    def _wtf(self,term,document,postings):
        tfd = 0
        for field, weight in self.field_weights.items():
            avg_dlf = self.index.get_global_info()['avg_field_lengths'][field]
            bb = 1-self.b+self.b*document.get_field_length(field)/avg_dlf
            # questo e sbagliato perche non e piena la lista di posting, ma e sparsa.
            # quindi costruisci un dizionario {term.id: Posting for term in query}
            # la costruzione del dizionario deve essere fatta nel costruttore.
            # poi questa funzione dovrebbe essere corretta.
            tf = len(postings[term.id].occurrences[field])
            tfd += weight*tf/bb
        return tfd
    
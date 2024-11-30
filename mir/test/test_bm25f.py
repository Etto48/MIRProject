import math
from typing import List, Dict
from mir.ir.document_info import DocumentInfo
from mir.ir.impls.bm25f_scoring import BM25FScoringFunction
from mir.ir.posting import Posting
from mir.ir.term import Term


# Mock Index class to provide global info (e.g., average field lengths)
class MockIndex:
    def get_global_info(self):
        # Return mock data for average field lengths
        return {
            'avg_field_lengths': {
                'title': 5.0,  # average length of the title field
                'body': 100.0,  #g average length of the body field
                'author': 2.0  # average length of the author field
            }
        }


# Define a mock DocumentInfo for the document we're scoring
doc_info = DocumentInfo(id=1, lengths=[2, 3, 100])

# Define mock terms
term1 = Term(term="example", id=0, field="title", frequency=2)
term2 = Term(term="document", id=1)

# Create mock postings (simplified for the test)
postings = [
    Posting(doc_id=1, term_id=0),  # term1 'example' in document 1
    Posting(doc_id=1, term_id=1)   # term2 'document' in document 1
]

# Add occurrences for the mock postings (simplified)
postings[0].occurrences["title"].append(1)  # term1 occurs in the title
postings[1].occurrences["body"].append(10)   # term2 occurs in the body

# Create a BM25F scoring function
bm25f = BM25FScoringFunction(k1=1.5, b=0.75, field_weights={'title': 2.0, 'body': 1.0, 'author': 0.5}, index=MockIndex())

# Define a query with terms (example query: ["example", "document"])
query = [term1, term2]

# Calculate the BM25F score for the document
score = bm25f(doc_info, postings, query)

print(f"BM25F score: {score}")

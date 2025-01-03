<!-- module: mir.ir.scoring_function -->

## Scoring Function

The ScoringFunction class defines the interface for scoring documents based on postings and the query, supporting reranking in the system. 

It includes a \_\_call\_\_ method for scoring and an optional batched_call function for processing multiple documents at once, mainly for neural networks' efficiency.


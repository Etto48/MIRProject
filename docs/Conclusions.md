<!-- order: 1000 -->
## Conclusions

Below, we present the benchmark results on the test set:

|   |       name |      map |     ndcg | recip_rank |     P.10 | recall.10 |
|:--|-----------:|---------:|---------:|-----------:|---------:|----------:|
| 0 |       MyIR | 0.310039 | 0.481937 |   0.800661 | 0.566667 |  0.170578 |
| 1 |       BM25 | 0.314385 | 0.492467 |   0.802359 | 0.575926 |  0.176116 |
| 2 | BM25+DFRee | 0.309455 | 0.491289 |   0.842813 | 0.542593 |  0.174679 |

Our Information Retrieval (IR) system demonstrates performance comparable to BM25 provided by PyTerrier. This validates the effectiveness of our approach in addressing large-scale learning-to-rank tasks.

A key strength of our system lies in its highly modular architecture. We prioritized designing a flexible and extendable codebase, enabling future enhancements and integration of advanced scoring functions, indexing mechanisms, or re-ranking techniques.

### Limitations and Challenges

Despite the promising results, our system's inference time lags significantly behind state-of-the-art solutions. This limitation stems from the reliance on less-optimized technologies for handling large datasets and the constrained time frame that limited further optimizations.

The primary bottleneck resides in the retrieval of postings and document info from the index implemented with SQL-based technology. While SQL provides robust handling for structured data, it is not optimized for high-throughput IR tasks.

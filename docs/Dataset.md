<!-- module: mir.utils.dataset -->

## Dataset

This code provides functions for downloading and processing the MS MARCO dataset:

1. **`get_msmarco_dataset`**:
   - Downloads various components of the MS MARCO dataset (such as the corpus, queries, and relevance judgments) to a specified directory.
   - Handles downloading, file extraction (both `.tar.gz` and `.gz` formats), and ensures that files are only downloaded once.

2. **`msmarco_dataset_to_contents`**:
   - Converts the corpus from the MS MARCO dataset (stored in a pandas DataFrame) into a generator of `DocumentContents` objects, which includes the document text (`body`) and document ID (`doc_id`).

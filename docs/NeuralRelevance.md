<!-- module: mir.neural_relevance.model -->

## BERT Learning-to-Rank

The `NeuralRelevance` class uses a pre-trained BERT model for learning-to-rank tasks, where the BERT model's weights are frozen, and only a "similarity head" is fine-tuned. 

The model is trained with a binary cross-entropy loss function, which measures the discrepancy between predicted and actual relevance scores for queries and documents.

The input is preprocessed and encoded as follows:
`[CLS] Query [SEP] Document [SEP]`

Key features:
- Training is performed on the MSMarco dataset with early stopping to prevent overfitting.
- Model saving, loading, and the ability to download pre-trained weights from a URL are included.

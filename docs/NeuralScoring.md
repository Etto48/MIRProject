<!-- module: mir.ir.impls.neural_scoring_function -->

## Neural Scoring Function

The `NeuralScoringFunction` class utilizes the pre-trained `NeuralRelevance` model to compute relevance scores between queries and documents. 

It provides two methods: the `__call__()` method calculates the score for a single document-query pair, while the `batched_call()` method processes multiple documents against a single query in batch mode. 

The model is used in evaluation mode, with gradients disabled to enhance performance. 
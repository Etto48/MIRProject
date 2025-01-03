<!-- module: mir.neural_relevance.dataset -->

## MSMarco Dataset

For this project, we chose the MSMarco dataset due to its large volume of data, which is ideal for fine-tuning a learning-to-rank model. 

Additionally, the dataset already includes predefined splits for training, validation, and testing, making it particularly well-suited for our needs.

The following class automates data loading, preparing it for use with PyTorch in a learning-to-rank model.
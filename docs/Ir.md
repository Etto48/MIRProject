<!-- module: mir.ir.ir -->

## IR System

The **IR** class serves as the backbone of the project, integrating all necessary components to create a fully functional instance. It orchestrates indexing and search operations by leveraging these components.

### Initialization
During the initialization of the IR System, a **scoring function pipeline** can be provided. This pipeline consists of a list of tuples in the format:  

**`(number of documents, scoring function)`**

- The **first element** specifies the total number of final results to be returned.  
- The **subsequent elements** define how many documents should be re-ranked by each scoring function in the pipeline.  

This flexible design enables efficient ranking and re-ranking workflows tailored to various information retrieval tasks.
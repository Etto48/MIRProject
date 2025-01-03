<!-- module: mir.ir.index -->
## Index

The Index class defines the interface for document indexing systems, holding the inverted index and providing methods for interacting with it. 

It includes functions to retrieve document and term information, index individual and bulk documents, and access global statistics. Key methods include `get_postings()` for term postings, `get_document_info()` and `get_document_contents()` for document metadata and content, and `get_term()` and `get_term_id()` for term details. 

This class serves as a foundation for implementing specific index types in search systems.
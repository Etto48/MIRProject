<!-- module: mir.ir.impls.sqlite_index -->

## SQLite Index 

The `SqliteIndex` class is an implementation of an inverted index based on SQLite, designed to manage the indexing of documents in a search system. The index stores various information in its database, including postings, terms, documents, and document metadata.

SQLite was chosen for its efficient disk management, enabling asynchronous writes, multi-threading, and effective caching, which allows handling large amounts of data efficiently.

The `global_info` table is continuously updated during the indexing process. This information is used to compute the average length of various fields, which plays a crucial role in optimizing search efficiency.

The class includes methods to retrieve this global data, efficiently caching it to enhance performance during searches.

<!-- module: mir.ir.posting -->

## Posting

The Posting class represents a term's occurrence in a document, storing its doc_id, term_id, and a dictionary of term frequencies across author, title, and body fields. 

If no frequencies are provided, it defaults to 0 for each field. The \_\_repr\_\_ method returns a string representation of the posting.
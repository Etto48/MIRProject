from typing import Optional

class Posting:
    def __init__(self, doc_id: int, term_id: int, occurrences: Optional[dict[str, int]] = None):
        self.term_id = term_id
        self.doc_id = doc_id
        self.occurrences = occurrences if occurrences is not None else {"author": 0, "title": 0, "body": 0}

    def __repr__(self) -> str:
        return f"Posting(doc_id={self.doc_id}, term_id={self.term_id}, occurrences={self.occurrences})"

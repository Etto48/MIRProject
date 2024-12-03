class Posting:
    def __init__(self, doc_id: int, term_id: int, occurrences: dict[str, list[int]] = None):
        self.term_id = term_id
        self.doc_id = doc_id
        # If no occurrences are passed, use empty lists
        self.occurrences = occurrences or {
            "author": [],
            "title": [],
            "body": []
        }

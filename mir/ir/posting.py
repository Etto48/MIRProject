class Posting:
    def __init__(self, doc_id: int, **kwargs):
        self.doc_id = doc_id
        self.__dict__.update(kwargs)
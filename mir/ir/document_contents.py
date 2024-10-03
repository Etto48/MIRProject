class DocumentContents:
    def __init__(self, title: str, body: str, **kwargs):
        self.title = title
        self.body = body
        self.__dict__.update(kwargs)
        
    def add_field(self, field: str, value: str):
        self.__dict__[field] = value
        
    def set_score(self, score: float):
        self.score = score
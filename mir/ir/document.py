from mir.ir.document_contents import DocumentContents


class Document:
    def __init__(self, contents: DocumentContents, id: int):
        self.contents = contents
        self.id = id
        self.info = contents.compute_info()
    
    
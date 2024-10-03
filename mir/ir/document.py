from collections.abc import Callable
from mir.ir.document_contents import DocumentContents


class Document:
    def __init__(self, contents: DocumentContents, id: int, get_info: Callable[[DocumentContents], dict] = None):
        self.contents = contents
        self.id = id
        self.info = get_info(contents) if get_info is not None else {}
    
    
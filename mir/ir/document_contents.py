import struct

from mir.fs_collections.serde import Serde


class DocumentContents:
    def __init__(self, author: str, title: str, body: str, **kwargs):
        self.author = author
        self.title = title
        self.body = body
        self.__dict__.update(kwargs)
        
    def add_field(self, field: str, value: str):
        self.__dict__[field] = value
        
    def set_score(self, score: float):
        self.score = score

    def __ser__(self) -> bytes:
        author_bytes = self.author.encode('utf-8')
        title_bytes = self.title.encode('utf-8')
        body_bytes = self.body.encode('utf-8')
        author_len = len(author_bytes)
        title_len = len(title_bytes)
        body_len = len(body_bytes)
        pack = struct.pack(f'3i{author_len}s{title_len}s{body_len}s', author_len, title_len, body_len, author_bytes, title_bytes, body_bytes)
        return pack
    
    @staticmethod
    def __deser__(data: bytes) -> "DocumentContents":
        author_len = struct.unpack('i', data[:4])[0]
        data = data[4:]
        title_len = struct.unpack('i', data[:4])[0]
        data = data[4:]
        body_len = struct.unpack('i', data[:4])[0]
        data = data[4:]
        author = struct.unpack(f'{author_len}s', data[:author_len])[0]
        author = author.decode('utf-8')
        data = data[author_len:]
        title = struct.unpack(f'{title_len}s', data[:title_len])[0]
        title = title.decode('utf-8')
        data = data[title_len:]
        body = struct.unpack(f'{body_len}s', data[:body_len])[0]
        body = body.decode('utf-8')
        return DocumentContents(author, title, body)
    

DOCUMENT_CONTENTS_SERDE = Serde[DocumentContents](
    serialize=lambda doc: doc.__ser__(),
    deserialize=lambda data, key: DocumentContents.__deser__(data)
)
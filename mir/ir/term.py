import struct

from mir.fs_collections.serde import Serde


class Term:
    def __init__(self, term: str, id: int, **kwargs):
        self.term = term
        self.id = id
        self.info = kwargs

    def __ser__(self) -> bytes:
        # [len, string, id, idf]
        term_bytes = self.term.encode('utf-8')
        term_len = len(term_bytes)
        idf = self.info['idf']
        pack = struct.pack(f'i{term_len}si', term_len, term_bytes, idf)
        return pack
    
    @staticmethod
    def __deser__(data: bytes, id:int) -> "Term":
        print(data, len(data))
        term_len = struct.unpack('i', data[:4])[0]
        data = data[4:]
        term = struct.unpack(f'{term_len}s', data[:term_len])[0]
        term = term.decode('utf-8')
        data = data[term_len+1:] # +1 for the null byte
        idf = struct.unpack('i', data[:4])[0]
        return Term(term, id, idf=idf)
    

TERM_SERDE = Serde[Term](
    serialize=lambda term: term.__ser__(),
    deserialize=lambda data, key: Term.__deser__(data, key)
)

    
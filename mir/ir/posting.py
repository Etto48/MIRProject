import struct
from typing import Optional

class Posting:
    def __init__(self, doc_id: int, term_id: int, occurrences: Optional[dict[str, int]] = None):
        self.term_id = term_id
        self.doc_id = doc_id
        self.occurrences = occurrences if occurrences is not None else {"author": 0, "title": 0, "body": 0}

    def __repr__(self) -> str:
        return f"Posting(doc_id={self.doc_id}, term_id={self.term_id}, occurrences={self.occurrences})"
    
    def __ser__(self) -> bytes:
        """
        Serializza il Posting in formato binario ottimizzato.
        """

        packed_data = struct.pack("III", 
                                  self.occurrences['author'], 
                                  self.occurrences['title'],
                                  self.occurrences['body'])

        return packed_data
    
    @staticmethod
    def __deser__(data: bytes, term_id: int, doc_id: int):
        """
        Deserializza il Posting da un buffer di byte.
        """
        occ_author, occ_title, occ_body = struct.unpack("III", data[:12])

        return Posting(doc_id, term_id, {"author": occ_author, "title": occ_title, "body": occ_body}), 12

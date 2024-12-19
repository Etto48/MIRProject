import struct

class Posting:
    def __init__(self, doc_id: int, term_id: int, occurrences: dict[str, int] = {"author": 0, "title": 0, "body": 0}):
        self.term_id = term_id
        self.doc_id = doc_id
        self.occurrences = occurrences

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
    def __deser__(or_data: bytes, term_id: int, doc_id: int):
        """
        Deserializza il Posting da un buffer di byte.
        """
        data = or_data
        posting = Posting(doc_id, term_id)
        occ_author, occ_title, occ_body = struct.unpack("III", data[:12])

        posting.occurrences["author"] = occ_author
        posting.occurrences["title"] = occ_title
        posting.occurrences["body"] = occ_body

        return posting, 12
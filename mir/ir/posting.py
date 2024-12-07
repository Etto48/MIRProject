import struct


class Posting:
    def __init__(self, doc_id: int, term_id: int, **kwargs):
        self.term_id = term_id
        self.doc_id = doc_id
        self.occurrences: dict[str, list[int]] = {
            "author": [],
            "title": [],
            "body": []
        }

    def __repr__(self) -> str:
        return f"Posting(doc_id={self.doc_id}, term_id={self.term_id}, occurrences={self.occurrences})"
    
    def __ser__(self) -> bytes:
        """
        Serializza il Posting in formato binario ottimizzato.
        """
        len_author = len(self.occurrences["author"])
        len_title = len(self.occurrences["title"])
        len_body = len(self.occurrences["body"])

        packed_data = struct.pack("III", len_author, len_title, len_body)

        # COMPRIMI LE OCCORRENZE

        auth_occ = self.occurrences["author"]
        title_occ = self.occurrences["title"]
        body_occ = self.occurrences["body"]

        packed_data += struct.pack(f"{len_author}I", *auth_occ)
        packed_data += struct.pack(f"{len_title}I", *title_occ)
        packed_data += struct.pack(f"{len_body}I", *body_occ)

        return packed_data
    
    @staticmethod
    def __deser__(or_data: bytes, term_id: int, doc_id: int):
        """
        Deserializza il Posting da un buffer di byte.
        """
        data = or_data
        posting = Posting(doc_id, term_id)
        len_author, len_title, len_body = struct.unpack("III", data[:12])
        data = data[12:]

        # DECOMPRIMI LE OCCORRENZE

        auth_occ = struct.unpack(f"{len_author}I", data[:4*len_author])
        data = data[4*len_author:]
        title_occ = struct.unpack(f"{len_title}I", data[:4*len_title])
        data = data[4*len_title:]
        body_occ = struct.unpack(f"{len_body}I", data[:4*len_body])

        posting.occurrences["author"] = list(auth_occ)
        posting.occurrences["title"] = list(title_occ)
        posting.occurrences["body"] = list(body_occ)

        return posting, 12 + 4*(len_author + len_title + len_body)
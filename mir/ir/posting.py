import struct

from mir.utils.compression import from_dgaps, into_dgaps, ints_from_vbc, ints_to_vbc


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

        comp_occ= {
            "author": ints_to_vbc(into_dgaps(self.occurrences["author"])),
            "title": ints_to_vbc(into_dgaps(self.occurrences["title"])),
            "body": ints_to_vbc(into_dgaps(self.occurrences["body"]))
        }

        len_author = len(comp_occ["author"])
        len_title = len(comp_occ["title"])
        len_body = len(comp_occ["body"])

        packed_data = struct.pack("III", len_author, len_title, len_body)

        packed_data += comp_occ["author"]
        packed_data += comp_occ["title"]
        packed_data += comp_occ["body"]


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

        author_occ = from_dgaps(ints_from_vbc(data[:len_author]))
        data = data[len_author:]
        title_occ = from_dgaps(ints_from_vbc(data[:len_title]))
        data = data[len_title:]
        body_occ = from_dgaps(ints_from_vbc(data[:len_body]))


        posting.occurrences["author"] = list(author_occ)
        posting.occurrences["title"] = list(title_occ)
        posting.occurrences["body"] = list(body_occ)

        return posting, 12 + (len_author + len_title + len_body)
from collections import OrderedDict
import struct

from mir.fs_collections.serde import Serde
from mir.ir.posting import Posting
from mir.utils.compression import from_dgaps, into_dgaps, ints_from_vbc, ints_to_vbc

class PostingList(OrderedDict[int, Posting]):
    def __init__(self):
        super().__init__()

    def __ser__(self) -> bytes:
        """
        Serializza la PostingList in formato binario ottimizzato.
        """
        # Numero di posting
        doc_id_list = [posting.doc_id for posting in self.values()]
        # COMPRESSIONE
        doc_list_bytes = ints_to_vbc(into_dgaps(doc_id_list))

        packed_data = struct.pack("I", len(doc_list_bytes))
        packed_data += doc_list_bytes

        for posting in self.values():
            packed_data += posting.__ser__()

        # Serializzazione dei Posting
        return packed_data
    
    @staticmethod
    def __deser__(data: bytes, term_id: int) -> "PostingList":
        """
        Deserializza la PostingList da un buffer di byte.
        """
        posting_list = PostingList()
        # Numero di posting: lenght of compressed doc_list in bytes
        doc_ids_size = struct.unpack("I", data[:4])[0]
        data = data[4:]
        doc_list_bytes = data[:doc_ids_size]
        doc_list = from_dgaps(ints_from_vbc(doc_list_bytes))
        
        data = data[doc_ids_size:]

        for doc_id in doc_list:
            posting, data_read = Posting.__deser__(data, term_id, doc_id)
            posting_list[doc_id] = posting
            data = data[data_read:]

        return posting_list
    
POSTING_LIST_SERDE = Serde[PostingList](
    serialize=lambda posting_list: posting_list.__ser__(),
    deserialize=lambda data, term_id: PostingList.__deser__(data, term_id)
)

from collections import OrderedDict
import struct

from mir.fs_collections.serde import Serde
from mir.ir.posting import Posting

class PostingList(OrderedDict[int, Posting]):
    def __init__(self):
        super().__init__()

    def __ser__(self) -> bytes:
        """
        Serializza la PostingList in formato binario ottimizzato.
        """
        # Numero di posting
        doc_list = [docid for docid in self.keys()]
        # COMPRESSIONE
        packed_data = struct.pack("I", len(doc_list))
        packed_data += struct.pack(f"{len(doc_list)}I", *doc_list)

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
        # Numero di posting
        num_posting = struct.unpack("I", data[:4])[0]
        data = data[4:]
        doc_list = struct.unpack(f"{num_posting}I", data[:4*num_posting])
        data = data[4*num_posting:]

        # DECOMPRIMI doc_list

        for doc_id in doc_list:
            posting, data_read = Posting.__deser__(data, term_id, doc_id)
            posting_list[doc_id] = posting
            data = data[data_read:]

        return posting_list
    
POSTING_LIST_SERDE = Serde[PostingList](
    serialize=lambda posting_list: posting_list.__ser__(),
    deserialize=lambda data, term_id: PostingList.__deser__(data, term_id)
)

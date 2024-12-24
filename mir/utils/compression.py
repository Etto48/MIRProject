def into_dgaps(doc_ids: list[int]) -> list[int]:
    current_id = 0
    doc_ids_dgaps = [0]*len(doc_ids)
    for i, doc_id in enumerate(doc_ids):
        doc_ids_dgaps[i] = doc_id - current_id
        assert doc_ids_dgaps[i] >= 0, f"Negative gap, {doc_id} - {current_id}"
        current_id = doc_id
    return doc_ids_dgaps

def from_dgaps(doc_ids_dgaps: list[int]) -> list[int]:
    current_id = 0
    doc_ids = [0]*len(doc_ids_dgaps)
    for i, doc_id_dgap in enumerate(doc_ids_dgaps):
        doc_ids[i] = doc_id_dgap + current_id
        current_id = doc_ids[i]
    return doc_ids

def int_to_vbc(i: int) -> bytes:
    ret = b""
    while True:
        has_next = i >= 128
        byte = i % 128
        if has_next:
            byte |= 0b1000_0000
        ret += byte.to_bytes(1)
        if not has_next:
            break
        i >>= 7
    return ret

def ints_to_vbc(ints: list[int]) -> bytes:
    return b"".join(int_to_vbc(i) for i in ints)

def ints_from_vbc(b: bytes) -> list[int]:
    ret = []
    current_int = 0
    current_shift = 0
    for byte in b:
        has_next = byte & 0b1000_0000
        current_int = current_int + ((byte & 0b0111_1111) << current_shift)
        if not has_next:
            ret.append(current_int)
            current_int = 0
            current_shift = 0
        else:
            current_shift += 7
    if current_int != 0:
        raise ValueError("Invalid VB code")
    return ret

def int_from_vbc(b: bytes) -> int:
    current_int = 0
    current_shift = 0
    for byte in b:
        has_next = byte & 0b1000_0000
        current_int = current_int + ((byte & 0b0111_1111) << current_shift)
        if not has_next:
            return current_int
        current_shift += 7
    raise ValueError("Invalid VB code")
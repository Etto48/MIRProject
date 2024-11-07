from mir.ir.document_contents import DocumentContents
from mir.ir.token_ir import TokenLocation
from mir.ir.tokenizer import Tokenizer


class DocumentInfo:
    def __init__(self, id: int, lengths: list[int]):
        assert len(lengths) == 3, "Lengths must have 3 elements, [author, title, body]"
        self.id = id
        self.lengths = lengths

    @staticmethod
    def from_document_contents(id: int, doc: DocumentContents, tokenizer: Tokenizer) -> "DocumentInfo":
        tokens = tokenizer.tokenize_document(doc)
        tokens_for_field = [0,0,0]
        for token in tokens:
            match token.where:
                case TokenLocation.AUTHOR:
                    field_offset = 0
                case TokenLocation.TITLE:
                    field_offset = 1
                case TokenLocation.BODY:
                    field_offset = 2
                case _:
                    raise ValueError(f"Invalid token location {token.where}")
            tokens_for_field[field_offset] += 1
        return DocumentInfo(id, tokens_for_field)
                    

    
    
from dataclasses import dataclass

"""
Token class is just a dataclass to keep track of the
position of the word in a given document and wether it's
present in the title or in the body (lyrics) of the song
"""

@dataclass
class Token:
    token: str
    is_in_title: bool
    position: int
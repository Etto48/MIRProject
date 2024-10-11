from dataclasses import dataclass
from enum import Enum


class TokenLocation(Enum) :
    QUERY = 0
    AUTHOR_NAME = 1
    TITLE = 2
    BODY = 3

@dataclass
class Token:
    """
    Token class is just a dataclass to keep track of the
    position of the word in a given document and wether it's
    present in the author's name, title or in the 
    body (lyrics) of the song
    """
    token: str
    where: TokenLocation
    position: int



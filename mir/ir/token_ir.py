from dataclasses import dataclass
from enum import Enum


class TokenLocation(Enum) :
    QUERY = 0
    AUTHOR = 1
    TITLE = 2
    BODY = 3

@dataclass
class Token:
    text: str
    location: TokenLocation

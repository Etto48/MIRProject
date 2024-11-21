from collections.abc import Generator, Sized
from typing import TypeVar, Generic

T = TypeVar('T')
P = TypeVar('P')
Q = TypeVar('Q')


class SizedGenerator(Generic[T, P, Q], Generator[T, P, Q], Sized):
    def __init__(self, generator: Generator[T, P, Q], length: int):
        self.generator = generator
        self.length = length

    def __iter__(self):
        return self.generator

    def __len__(self):
        return self.length

    def send(self, value):
        return self.generator.send(value)

    def throw(self, typ, val=None, tb=None):
        return self.generator.throw(typ, val, tb)

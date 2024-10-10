from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Protocol, TypeVar

T = TypeVar('T')


@dataclass
class Serde(Generic[T]):
    serialize: Callable[[T], bytes]
    deserialize: Callable[[bytes], T]


INT_SERDE = Serde[int](
    serialize=lambda x: x.to_bytes(8, 'big'),
    deserialize=lambda x: int.from_bytes(x[:8], 'big')
)

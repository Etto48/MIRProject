from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar

T = TypeVar('T')


@dataclass
class Serde(Generic[T]):
    serialize: Callable[[T], bytes]
    deserialize: Callable[[bytes, int | str], T]


INT_SERDE = Serde[int](
    serialize=lambda x: x.to_bytes(8, 'big'),
    deserialize=lambda x, key: int.from_bytes(x[:8], 'big')
)

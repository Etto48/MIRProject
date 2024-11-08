from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar

from mir.fs_collections.hashable_key.hashable_key import HashableKey

T = TypeVar('T')


@dataclass
class Serde(Generic[T]):
    serialize: Callable[[T], bytes]
    deserialize: Callable[[bytes, int | HashableKey], T]


INT_SERDE = Serde[int](
    serialize=lambda x: x.to_bytes(8, 'big'),
    deserialize=lambda x, key: int.from_bytes(x[:8], 'big')
)

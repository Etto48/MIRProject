from abc import abstractmethod
from typing import Protocol


class Serde(Protocol):
    @abstractmethod
    def serialize(self) -> bytes:
        ...
        
    @staticmethod
    def deserialize(data: bytes) -> 'Serde':
        ...
        
    def __eq__(self, other: 'Serde') -> bool:
        return self.serialize() == other.serialize()
        
class IntSerde(Serde):
    def __init__(self, value: int):
        self.value = value
        
    def serialize(self) -> bytes:
        return self.value.to_bytes(8, 'big')
        
    @staticmethod
    def deserialize(data: bytes) -> 'IntSerde':
        return IntSerde(int.from_bytes(data[:8], 'big'))
    
    def __eq__(self, other: 'IntSerde') -> bool:
        return self.value == other.value
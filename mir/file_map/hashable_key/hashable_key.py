from abc import abstractmethod
from collections.abc import Hashable
from typing import Protocol


class HashableKey(Protocol, Hashable):
    """
    This abstract class is used to define the interface for a hashable key.
    An hashable key is an object that can be used as a key in a FileHMap.
    """
    
    @abstractmethod
    def __bytes__(self):
        ...
        
    def __hash__(self):
        return hash(self.__bytes__())
        
    def __eq__(self, other):
        return self.__bytes__() == other.__bytes__()
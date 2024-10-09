from abc import ABC, abstractmethod
from collections.abc import Hashable


class HashableKey(ABC, Hashable):
    """
    This abstract class is used to define the interface for a hashable key.
    An hashable key is an object that can be used as a key in a FileHMap.
    The object must implement the __hash__ and __bytes__ methods.
    Also two HashableKey objects with the same __bytes__ must
    produce the same hash.
    """
    
    @abstractmethod
    def __hash__(self):
        ...
    
    @abstractmethod
    def __bytes__(self):
        ...
        
    def __eq__(self, other):
        return self.__bytes__() == other.__bytes__()
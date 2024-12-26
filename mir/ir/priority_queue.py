import heapq
from typing import Iterable, Optional, Sized

class PriorityQueue(Iterable[tuple[float, int]], Sized):
    def __init__(self, max_size: int):
        """
        Create a priority queue with a maximum size.
        """
        self.heap = []
        self.finalised = False
        self.max_size = max_size
    
    def push(self, doc_id: int, score: float) -> Optional[int]:
        """
        Add an item with a given score to the priority queue

        Returns the doc_id of the item that was popped, if any. If the new item was not added returns its doc_id.
        """
        if len(self) == self.max_size:
            if score > self.heap[0][0]:
                popped = heapq.heappushpop(self.heap, (score, doc_id))
                return popped[1]
            else:
                return doc_id
        else:
            heapq.heappush(self.heap, (score, doc_id))
            return None
    
    def finalise(self):
        """
        Call this after all items have been pushed to the priority queue.
        """
        self.heap.sort(reverse=True)
        self.finalised = True
    
    def __iter__(self) -> Iterable[tuple[float, int]]:
        """
        Iterate over the items in the priority queue.
        """
        if not self.finalised:
            raise ValueError("Priority queue must be finalised before iterating")
        return iter(self.heap)
    
    def __len__(self) -> int:
        """
        Get the number of items in the priority queue.
        """
        return len(self.heap)
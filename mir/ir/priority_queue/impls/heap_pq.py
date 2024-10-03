import heapq
from mir.ir.priority_queue.priority_queue import PriorityQueue


class HeapPQ(PriorityQueue):
    def __init__(self):
        self.heap = []
    def push(self, item):
        heapq.heappush(self.heap, item)
    def finalise(self):
        pass
    def pop(self):
        return heapq.heappop(self.heap)
    def __len__(self):
        return len(self.heap)
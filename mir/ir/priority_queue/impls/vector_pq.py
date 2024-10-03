from mir.ir.priority_queue.priority_queue import PriorityQueue


class VectorPQ(PriorityQueue):
    def __init__(self):
        self.finalised = False
        self.inner = []
    def push(self, item):
        self.finalised = False
        self.inner.append(item)
    def finalise(self):
        self.inner.sort()
        self.finalised = True
    def pop(self):
        assert self.finalised, "Must call finalise before pop"
        return self.inner.pop(0)
    def __len__(self):
        return len(self.inner)
class PriorityQueue:
    def push(self, item):
        """
        Add an item to the priority queue.
        """
        raise NotImplementedError()
    def finalise(self):
        """
        Call this after all items have been pushed to the priority queue.
        """
        raise NotImplementedError()
    def pop(self):
        """
        Pop the item with the highest priority.
        Must be called after finalise.
        """
        raise NotImplementedError()
    def __len__(self):
        """
        Get the number of items in the priority queue.
        """
        raise NotImplementedError()
    
if __name__ == "__main__":
    import random
    import time
    
    from mir.ir.priority_queue.impls import HeapPQ
    from mir.ir.priority_queue.impls import VectorPQ
    
    impls = [VectorPQ, HeapPQ]
    impl_times = {}
    for impl in impls:
        times = []
        for i in range(100):
            pq: PriorityQueue = impl()
            start_time = time.time()
            items = [random.random() for _ in range(10000)]
            for item in items:
                pq.push(item)
            pq.finalise()
            while len(pq) != 0:
                pq.pop()
            times.append(time.time() - start_time)
        impl_times[impl.__name__] = sum(times) / len(times)
    reference_time = impl_times[impls[0].__name__]
    for impl, secs in impl_times.items():
        print(f"{impl}: {secs:.6f}s ({secs / reference_time:.2f}x {impls[0].__name__})")
        
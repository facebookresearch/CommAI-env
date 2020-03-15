from collections import Counter
from sampler import Sampler

class Multiset(object):
    def __init__(self, N):
        self.item2id = {}
        self.id2item = []
        self.item_count = Counter()
        self.max_size = N
        self.sampler = Sampler(N, N, 1)
        self.count = 0

    def __contains__(self, item):
        return item in self.item2id

    def has_all(self, items):
        items = Counter(items)
        return all(items[x] <= self.item_count[x] for x in items)

    def count_missing(self, items):
        items = Counter(items)
        return {x: items[x] - self.item_count[x]
                    for x in items 
                    if items[x] - self.item_count[x] > 0}

    def __getitem__(self, item):
        return self.item_count[item]

    def __iter__(self):
        for item, c in self.item_count.items():
            for i in range(c):
                yield item

    def items(self):
        return self.item_count.items()

    def unique(self):
        return iter(self.id2item)
                
    def __len__(self):
        return self.count

    def grow_capacity(self, n):
        new_sampler = Sampler(self.max_size + n, self.max_size + n, 1)
        for item, count in self.items():
            item_id = self.item2id[item]
            new_sampler.add(item_id, count)
        self.sampler = new_sampler
        self.max_size += n

    def add(self, item, item_count=1):
        assert self.count < self.max_size
        if not item in self:
            item_id = len(self.id2item)
            self.item2id[item] = item_id
            self.id2item.append(item)
            self.item_count[item] = item_count
            self.sampler.add(item_id, item_count)
        else:
            item_id = self.item2id[item]
            c = self.item_count[item]
            self.item_count[item] += item_count
            self.sampler.remove(item_id, c)
            self.sampler.add(item_id, c + item_count)
        self.count += item_count

    def remove_all(self, item):
        #FIXME: make efficient
        while item in self:
            self.remove(item)

    def add_many(self, item, copies):
        for i in range(copies):
            self.add(item)

    def remove(self, item):
        assert item in self, item
        item_id = self.item2id[item]
        c = self.item_count[item]
        self.sampler.remove(item_id, c)
        if c == 1:
            del self.item_count[item]
            del self.item2id[item]
            # move another item to this id
            last_item = self.id2item.pop()
            last_item_id = len(self.id2item) 
            # unless this was the last item
            if last_item_id != item_id:
                self.id2item[item_id] = last_item
                self.item2id[last_item] = item_id
                last_item_count = self.item_count[last_item]
                self.sampler.remove(last_item_id, last_item_count)
                self.sampler.add(item_id, last_item_count)
        else:
            self.item_count[item] -= 1
            self.sampler.add(item_id, c - 1)
        self.count -= 1


    def sample(self):
        assert self.count == self.sampler.total_weight
        item_id = self.sampler.sample()
        return self.id2item[item_id]

    def sample_without_replacement(self, n):
        ret = []
        while n > 0:
            ret.append(self.sample())
            n -= 1
            if n > 0:
                self.remove(ret[-1])
        for x in ret[:-1]:
            self.add(x)
        return ret


# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from collections import Counter
import itertools
import bisect
import random

class Multiset(object):
    def __init__(self, N):
        self.item_count = Counter()
        self.max_size = N
        self.count = 0

    def __contains__(self, item):
        return item in self.item_count

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
        return self.item_count.keys()
                
    def __len__(self):
        return self.count

    def grow_capacity(self, n):
        self.max_size += n

    def add(self, item, item_count=1):
        assert self.count < self.max_size
        if not item in self:
            self.item_count[item] = item_count
        else:
            c = self.item_count[item]
            self.item_count[item] += item_count
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
        c = self.item_count[item]
        if c == 1:
            del self.item_count[item]
        else:
            self.item_count[item] -= 1
        self.count -= 1


    def sample(self):
        choices, weights = zip(*self.item_count.items())
        cumdist = list(itertools.accumulate(weights))
        x = random.random() * cumdist[-1]
        return choices[bisect.bisect(cumdist, x)]

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


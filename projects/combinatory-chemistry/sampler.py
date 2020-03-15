
import numbers
from numpy import *

class Sampler:
    
    def __init__(self, max_entries, max_value=100, min_value=1):
        self.nentries = 0
        self.max_entries = max_entries
        self.max_value = max_value
        self.min_value = min_value
        self.top_level = int(ceil(log2(max_value)))
        self.bottom_level = int(ceil(log2(min_value)))
        self.nlevels = 1 + self.top_level - self.bottom_level
        
        self.total_weight = 0
        self.weights = zeros(max_entries, dtype='d')
        

        self.level_weights = zeros(self.nlevels, dtype='d')
        self.level_buckets = [[] for i in range(self.nlevels)]
        self.level_max = [pow(2, self.top_level-i)  for i in range(self.nlevels)]
    
    def add(self, idx, weight):
        if weight > self.max_value or weight < self.min_value:
            raise Exception("Weight out of range: %1.2e" % weight)

        if idx < 0 or idx >= self.max_entries or not isinstance(idx, numbers.Integral):
            raise Exception("Bad index: %s", idx)

        self.nentries += 1
        self.total_weight += weight
        
        self.weights[idx] = weight
        
        raw_level = int(ceil(log2(weight)))
        level = self.top_level - raw_level
        
        self.level_weights[level] += weight
        self.level_buckets[level].append(idx)
        
    def remove(self, idx, weight):
        if weight > self.max_value or weight < self.min_value:
            raise Exception("Weight out of range: %1.2e" % weight)

        if idx < 0 or idx >= self.max_entries or not isinstance(idx, numbers.Integral):
            raise Exception("Bad index: %s", idx)

        raw_level = int(ceil(log2(weight)))
        level = self.top_level - raw_level

        for idx_in_level in range(len(self.level_buckets[level])):
            if self.level_buckets[level][idx_in_level] == idx:
                break
        else:
            raise Exception("Index not found: ", idx)
        
        self.weights[idx] = 0.0
        self.total_weight -= weight
        self.level_weights[level] -= weight
        # Swap with last element for efficent delete
        swap_idx = self.level_buckets[level].pop()
        if idx != swap_idx:
            self.level_buckets[level][idx_in_level] = swap_idx
        self.nentries -= 1

    def _sample(self):
        
        u = random.uniform(high=self.total_weight)
        
        # Sample a level using the CDF method
        cumulative_weight = 0
        for i in range(self.nlevels):
            cumulative_weight += self.level_weights[i]
            level = i
            if u < cumulative_weight:
                break
            
        # Now sample within the level using rejection sampling
        level_size = len(self.level_buckets[level])
        level_max =  self.level_max[level]
        reject = True
        while reject:
            idx_in_level = random.randint(0, level_size)
            idx = self.level_buckets[level][idx_in_level]
            idx_weight = self.weights[idx]
            u_lvl = random.uniform(high=level_max)
            if u_lvl <= idx_weight:
                reject = False
                
        return (idx, level, idx_in_level, idx_weight)

    def sample(self):
        return self._sample()[0]
        
    def sampleAndRemove(self):
        (idx, level, idx_in_level, weight) = self._sample()
        
        # Remove it
        self.weights[idx] = 0.0
        self.total_weight -= weight
        self.level_weights[level] -= weight
        # Swap with last element for efficent delete
        swap_idx = self.level_buckets[level].pop()
        self.level_buckets[level][idx_in_level] = swap_idx
        self.nentries -= 1
        
        return (idx, weight)

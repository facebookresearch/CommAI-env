# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from multiset import Multiset
from observable import Observable
import tqdm
from expression import Expression
from collections import Counter


class BasePool(object):
    def __init__(self, N, food_size):
        self.reaction_computed = Observable()
        self.step_computed = Observable()
        self.generation_computed = Observable()
        self.expressions = Multiset(N)
        self.tmp_removed_expressions = []
        self.food_size = food_size

    def register_step_observer(self, obs):
        self.step_computed.register(obs.on_step_computed)

    def register_reaction_observer(self, obs):
        self.reaction_computed.register(obs.on_reaction_computed)

    def deregister_observers(self):
        self.reaction_computed.deregister_all()
        self.step_computed.deregister_all()

    def pop_reactive(self):
        assert len(self.expressions) > 0
        t =  self.expressions.sample()
        self.tmp_remove(t)
        return t

    def rollback(self, t):
        self.tmp_removed_expressions.remove(t)
        self.append(t)

    def get_total_size(self):
        return sum(len(expr) for expr in self.expressions) + \
                sum(len(expr) for expr in self.tmp_removed_expressions)

    def __len__(self):
        return len(self.expressions) + len(self.tmp_removed_expressions)

    def __iter__(self):
        return iter(self.expressions)

    def unique(self):
        return self.expressions.unique()

    def __contains__(self, t):
        return t in self.expressions or self.can_make(t)

    def load(self, fn):
        raise NotImplementedError()

    def append(self, t):
        self.expressions.add(t)

    def tmp_remove(self, t):
        self.tmp_removed_expressions.append(t)
        self.expressions.remove(t)

    def remove(self, t):
        if t in self.tmp_removed_expressions:
            self.tmp_removed_expressions.remove(t)
            return True
        else:
            if t in self.expressions:
                self.expressions.remove(t)
                return True
            else:
                return False
        #if t == Expression.parse('SII'):
        #    print('food# ' ,self.get_multiplicity(t))

    def remove_all(self, ts):
        for t in ts:
            if not self.remove(t):
                return False
        return True

    def apply_reaction(self, reaction):
        if self.has_or_make_reactives(reaction):
            for r in reaction.reactives:
                self.remove(r)
            for p in reaction.products:
                self.append(p)
            self.reaction_computed(self, reaction)
            return True
        else:
            return False
    
    def has_or_make_reactives(self, reaction):
        reactives = reaction.reactives
        missing = self.count_missing(reactives)
        if any(r not in self and r not in self.tmp_removed_expressions
                for r in reactives):
            assert missing[r] > 0
        #if missing:
        #    print(reaction, {str(k): v for k,v in missing.items()})
        for compound, count in missing.items():
            if count > 0:
                made = self.make(compound, count)
                #NOTE: a compound can be made before noticing than another
                # cannot be made, but it should never happen with these 
                # binary reactions.
                if not made:
                    return False
        return True

    def count_missing(self, reactives):
        missing = Counter(self.expressions.count_missing(reactives))
        in_tmp = Counter(self.tmp_removed_expressions)
        return Counter({k:v-in_tmp[k] for k,v in missing.items()})

    def make(self, compound, count):
        for i in range(count):
            if not self.can_make(compound):
                return False
            if self.remove_all(compound.atoms()):
                self.append(compound)
        return True

    def can_make(self, ts):
        if self.food_size is None or len(ts) > self.food_size:
            return False
        return self.expressions.has_all(ts.atoms())

    def get_multiplicity(self, t):
        return self.expressions[t] - self.tmp_removed_expressions.count(t)

    def __getitem__(self, t):
        return self.get_multiplicity(t)

    def __str__(self):
        pool_strs = []
        for k in sorted(set(self.expressions), key=lambda k: self.expressions[k]):
            pool_strs.append(f"{k} {self.expressions[k]}")
        return "\n".join(pool_strs)


    def serializable(self):
        return {x.serializable(): self[x] for x in self.unique()}

    def evolve(self, num_reactions, timeout_time=1):
        for i in range(num_reactions):
                #with timeout(timeout_time):
                self.step()
                self.step_computed(self, i)

    def evolve_generations(self, num_generations):
        tick = 0
        for i in range(num_generations):
            for j in range(len(self)):
                self.step()
                self.step_computed(self, tick)
                tick += 1
            self.generation_computed(i)



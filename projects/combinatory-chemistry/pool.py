from base_pool import BasePool
import random
import numpy as np
from collections import Counter
from expression import Expression, atomic_factory
from contextlib import contextmanager
from reaction import Reaction
import pickle
import signal
from math import isclose
import tqdm

primitives = 'IKS'
#primitives = 'IKSBCW'

class Pool(BasePool):
    def __init__(self, N, p_reduce, p_combine, p_break, 
            max_sample_reductions = 250,
            break_position = 'top',
            reduce_regime =  'random',
            food_size = None,
            combination_method = 'consense',
            proportions = {c: 1./len(primitives) for c in primitives}):
        super(Pool, self).__init__(N, food_size)
        assert isclose(p_reduce + p_combine + p_break, 1)
        self.p_reduce = p_reduce
        self.p_combine = p_combine
        self.p_break = p_break
        if reduce_regime == 'priority':
            self.set_p_reduce(0)
        self.ticks = 0
        self.proportions = [proportions[t] for t in primitives]
        self.max_sample_reductions = max_sample_reductions 
        self.break_position = break_position
        self.reduce_regime = reduce_regime
        self.combination_partner = None
        self.combination_method = combination_method
        self._add_random_atoms(N)

    def grow(self, n):
        self._grow_capacity(n)
        self._add_random_atoms(n)

    def _grow_capacity(self, n):
        self.expressions.grow_capacity(n)

    def _add_random_atoms(self, n):
        coin_outcomes = np.random.choice(len(primitives), n, p=self.proportions)
        coin_counts = Counter(coin_outcomes)
        for i, count in coin_counts.items():
            term = atomic_factory(primitives[i])
            self.expressions.add(term, count)

    def _random_term(self):
        coin = np.random.choice(len(primitives), p=self.proportions)
        return atomic_factory(primitives[coin])

    def load(self, fn):
        state = pickle.load(open(fn, 'rb'))
        if isinstance(state, Pool):
            self.expressions = state.expressions
        else:
            self.expressions = state

    def save(self, fn):
        pickle.dump(self.expressions, open(fn, 'wb'))

    def step(self):
        if self.reduce_regime == 'random':
            self.step_random_reduce()
        elif self.reduce_regime == 'priority':
            self.step_priority_reduce()

    def step_random_reduce(self):
        t = self.pop_reactive()
        action = self.pick_action()
        if action == 'reduce':
            self.tape_reduce_or_rollback(t)
        elif action == 'combine':
            self.tape_combine_or_rollback(t)
        elif action == 'break':
            self.tape_break_or_rollback(t)
        else:
            assert action == 'none'

    def step_priority_reduce(self):
        t = self.pop_reactive()
        if not self.tape_reduce(t):
            action = self.pick_action()
            if action == 'combine':
                self.tape_combine_or_rollback(t)
            elif action == 'break':
                self.tape_break_or_rollback(t)
            else:
                raise RuntimeError('Invalid action ' + action)

    def tape_combine_or_rollback(self, t):
        if len(self) >= 2:
            if self.combination_method == 'consense':
                if self.has_combination_partner():
                    t2 = self.pop_combination_partner()
                    self.tape_combine(t, t2)
                else:
                    self.set_combination_partner(t)
            elif self.combination_method == 'unilateral':
                t2 = self.pop_reactive()
                self.tape_combine(t, t2)
        else:
            self.rollback(t)

    def tape_reduce_or_rollback(self, t):
        if not self.tape_reduce(t):
            self.rollback(t)

    def tape_break_or_rollback(self, t):
        if not self.tape_break(t):
            self.rollback(t)

    def has_combination_partner(self):
        return self.combination_partner is not None

    def pop_combination_partner(self):
        x = self.combination_partner
        self.combination_partner = None
        return x

    def set_combination_partner(self, x):
        self.combination_partner = x

    def pick_action(self):
        r = random.random()
        if r < self.p_reduce:
            return 'reduce'
        r -= self.p_reduce
        if r < self.p_combine:
            return 'combine'
        r -= self.p_combine
        if r < self.p_break:
            return 'break'
        r -= self.p_break
        assert False, f'Invalid reminder {r:.2f} (>0)'
        return 'none'


    def tape_reduce(self, t):
        if t.is_reducible(self):
            reduced, reactives, biproducts = t.sreduce(self, self.max_sample_reductions)
            reaction = Reaction((reduced, *biproducts), 'reduce', 
                    (t, *reactives))
            return self.apply_reaction(reaction)
        else:
            return False

    def tape_combine(self, term_left, term_right):
        combined = term_left.apply(term_right)
        reaction = Reaction((combined,), 'combine', (term_left, term_right))
        self.apply_reaction(reaction)
        return True

    def tape_break(self, t):
        if not t.is_leaf():
            if self.break_position == 'top':
                term_left, term_right = t.top_break()
            elif self.break_position == 'random':
                term_left, term_right = t.random_break()
            else:
                raise RuntimeError(f'Invalid break position {self.break_position}')
            reaction = Reaction((term_left, term_right), 'break', (t,))
            self.apply_reaction(reaction)
            return True
        else:
            return False

    def set_p_reduce(self, p_reduce):
        old_values = self.p_reduce, self.p_break, self.p_combine
        self.p_reduce = p_reduce
        if self.p_reduce > 1:
            self.p_reduce = 1
        rem = 1 - self.p_reduce
        ratio = self.p_combine / (self.p_break + self.p_combine)
        self.p_combine = ratio * rem
        self.p_break = 1 - self.p_reduce - self.p_combine
        assert self.p_break + self.p_reduce + self.p_combine == 1
        assert self.p_break >= 0 and self.p_reduce >= 0 and self.p_combine >= 0
        return old_values

    def freeze(self):
        self.old_p_values = self.set_p_reduce(1)

    def unfreeze(self):
        self.p_reduce, self.p_break, self.p_combine = self.old_p_values

def timeout_handler(signum, frame):
    raise TimeoutError()

@contextmanager
def timeout(seconds):
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

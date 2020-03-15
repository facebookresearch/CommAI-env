import itertools 
import random
import operator
from typing import NamedTuple, Tuple, Union
from collections import namedtuple
from combinator import Combinator, combinator_factory
from functools import partial, lru_cache

# def _instance_method_alias(obj, method, *args):
#     return getattr(obj, method)(*args)
# 
# def _pickle_method(method):
#     func_name = method.im_func.__name__
#     obj = method.im_self
#     cls = method.im_class
#     return _unpickle_method, (func_name, obj, cls)
# 
# def _unpickle_method(func_name, obj, cls):
#     for cls in cls.mro():
#         try:
#             func = cls.__dict__[func_name]
#         except KeyError:
#             pass
#         else:
#             break
#         return func.__get__(obj, cls)
# 
# import copy_reg
# import types
# copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)


class Expression(object): #namedtuple('Expression', 'children size')):
    __slots__ = ('children', 'cached_hash', 'size')
    #children: Tuple[Union['Expression', Combinator]]

    def __init__(self, *children):
        self.children = children
        self.size = sum(c.get_size() for c in children)

    def __eq__(self, ot):
        if not isinstance(ot, Expression):
            return False
        return self.children == ot.children

    def __hash__(self):
        if not hasattr(self, 'cached_hash'):
            setattr(self, 'cached_hash', hash(self.children))
        return self.cached_hash

    def atoms(self):
        for ch in self.children:
            for a in ch.atoms():
                yield a

    def is_leaf(self):
        return False

    def __iter__(self):
        return iter(self.children)

    def __lt__(self, ot):
        return self.get_size() < ot.get_size()

    def is_normal_form(self):
        if self.is_leaf():
            return True
        else:
            return self.children[0].is_leaf() and all(child.is_normal_form() 
                    for child in self.children[1:])

    def to_normal_form(self):
        if self.is_leaf():
            return self
        else:
            nf_children = tuple(child.to_normal_form() for child in
                    self.children)
            first_child = nf_children[0]
            if first_child.is_leaf():
                return Expression(*nf_children)
            else:
                return Expression(*(first_child.children + nf_children[1:]))

    def to_surface_normal_form(self):
        if self.is_leaf():
            return self
        else:
            first_child = self.children[0]
            if len(self.children) > 1:
                first_child = self.children[0]
                # applies only one level of normalization
                if not first_child.is_leaf():
                    return Expression(*(first_child.children + self.children[1:]))
                else:
                    return self
            else:
                return first_child # first and only child

    def __add__(self, ot):
        if not ot:
            return self
        if not isinstance(ot, Expression):
            ot = Expression(ot)
        return Expression(self, ot).to_surface_normal_form()

    def is_well_formed(self):
        if self.is_leaf():
            return True
        else:
            for e in self.children:
                if not e.is_leaf() and not e.is_well_formed():
                    return False
            return True

    def new(self, *children):
        return type(self)(*children)

    def apply(self, *expressions):
        return Expression(self, *expressions).to_surface_normal_form()

    def __call__(self, *expressions):
        return self.apply(*expressions)

    @classmethod
    def concat(cls, *expressions):
        '''concatenates terms at the same hierarchy level'''
        return sum(expressions, EmptyExpression())

    def infix(self, left, right):
        '''prepends the list of expressions in the left and append the list of
        expressions in the right'''
        new_children = left + (self,) + right
        return Expression(*new_children).to_surface_normal_form()

    def top_break(self):
        return self.new(*self.children[:-1]).to_surface_normal_form(),\
                self.new(self.children[-1]).to_surface_normal_form()

    def random_break(self):
        i = random.randint(1, len(self.children)-1)
        return self.new(*self.children[:i]).to_surface_normal_form(),\
                self.new(*self.children[i:]).to_surface_normal_form()


    def get_ttype(self):
        assert not isinstance(self.chidren[0], Expression)
        return self.children[0].get_ttype()

    def foldl(self, leaf_f, f):
        if self.is_leaf():
            return leaf_f(self)
        stack = list(self.children)
        ret = None
        while stack:
            term = stack.pop()
            if term.is_leaf():
                if ret is None:
                    ret = leaf_f(term)
                else:
                    ret = f(leaf_f(term), ret)
            else:
                for x in term.children:
                    stack.append(x)
        return ret

    def head(self):
        assert not self.is_leaf()
        return self.children[0]
    
    def ttype(self):
        assert self.is_leaf()
        return self.children[0].ttype()

    def tail(self):
        return self.children[1:]

    def n_args(self):
        return len(self.children) - 1

    def get_size(self):
        return self.size
        #return self.foldl(lambda t: 1, lambda x, y: x + y)

    def __len__(self):
        return self.get_size()

    def get_depth(self):
        return max(*(c.get_depth() for c in self.children)) + 1

    def __bool__(self):
        return True

    def take(self, k):
        return (self.new(a) for a in self.children[:k]), self.children[k:]

    @classmethod
    def parse(cls, expr):
        tree = cls._string_to_tree(expr)
        term = cls._tree_to_expression(tree)
        return term

    @classmethod
    def _tree_to_expression(cls, tree):
        if isinstance(tree, list):
            return Expression(*(cls._tree_to_expression(t) for t in tree)).to_surface_normal_form()
        else:
            return atomic_factory(tree)

    @classmethod
    def _string_to_tree(cls, expr):
        if len(expr) > 1:
            ret = []
            stack = [ret]
            for x in expr:
                if x == '(':
                    new_list = []
                    stack[-1].append(new_list)
                    stack.append(new_list)
                elif x == ')':
                    stack.pop()
                elif x == ' ':
                    continue
                else:
                    stack[-1].append(x)
            assert len(stack) == 1
            return ret
        else:
            return expr

    def __str__(self):
        return "({})".format("".join(map(str, self.children)))

    def __repr__(self):
        return "({})".format("".join(map(repr, self.children)))

    def serializable(self):
        return str(self)

    def dreduce(self, pool=None):
        reduced_term, is_reduced, reactives, biproducts = self.reduce_aux(pool)
        return reduced_term

    def reduce_aux(self, pool):
        if self.is_leaf():
            return self, False, [], []
        # lazy evaluation
        if self.is_surface_reducible(pool):
            reduced_expr, reactives, biproducts = self.surface_reduce(pool)
            return reduced_expr, True, reactives, biproducts
        else:
            for i,t in enumerate(self):
                if not t.is_leaf():
                    reduced_expr, is_reduced, reactives, biproducts = \
                            t.reduce_aux(pool)
                    if is_reduced:
                        return reduced_expr.infix(self.children[:i], self.children[i+1:]), is_reduced, reactives, biproducts
            return self, False, [], []

    def all_reductions(self, pool=None, max_reductions=None):
        reductions = self.all_reductions_aux(pool, max_reductions)
        if not reductions:  # irreducible
            reductions.append(lambda: (self, [], []))
        return reductions

    def all_reductions_aux(self, pool=None, max_reductions=None):
        assert max_reductions is None or max_reductions >= 0
        reductions = []
        if (max_reductions is None or max_reductions > 0) and not self.is_leaf():
            if self.is_surface_reducible(pool):
                def reduction_cl():
                    return self.surface_reduce(pool)
                reductions.append(reduction_cl)
            for i,child in enumerate(self.children):
                if child.is_leaf():
                    continue
                remaining_reductions = max_reductions - len(reductions) if max_reductions is not None else None
                subreductions = child.all_reductions_aux(pool, remaining_reductions)
                for subreduction_cl in subreductions:
                    def make_reduction_cl(children, i, subreduction_cl):
                        def reduction_cl():
                            left_children = children[:i]
                            right_children  = children[i+1:]
                            reduced_subexpr, reactives, biproducts =  subreduction_cl()
                            #print(i, ' + '.join(map(str, left_children)), '+', child, '->', reduced_subexpr, '+', ' + '.join(map(str, right_children)), '==>', self)
                            reduced_expr = reduced_subexpr.infix(left_children, right_children)
                            return reduced_expr, reactives, biproducts
                        return reduction_cl
                    reductions.append(make_reduction_cl(self.children, i, subreduction_cl))
        return reductions


    def is_reducible(self, pool=None):
        if self.is_surface_reducible(pool):
            return True
        else:
            if self.is_leaf():
                return False
            else:
                for subexpr in self:
                    if not subexpr.is_leaf() and subexpr.is_reducible(pool):
                        return True
                return False

    def is_surface_reducible(self, pool):
        if self.is_leaf():
            return False
        args = self.tail()
        head = self.head()
        if not head.is_leaf():
            return False
        C = head.get_combinator()
        return C.can_reduce(args, pool)

    def surface_reduce(self, pool):
        head, args = self.head(), self.tail()
        C = head.get_combinator()
        reduced_expr, reactives, biproducts =  C.reduce(args, pool)
        biproducts.append(self.head())
        return reduced_expr.to_surface_normal_form(), reactives, biproducts 

    def reduces_to(self, tgoal, tout=100):
        t = self
        for i in range(tout):
            if t == tgoal:
                return True
            t, is_reduced, _, _ = t.reduce_aux(None)
            if not is_reduced:
                break
        return False

    @classmethod
    def search_first(cls, criterion, primitives):
        for expr in cls.recursively_enumerate(primitives):
            if criterion(expr):
                return expr

    @classmethod
    def recursively_enumerate(cls, primitives):
        length = 1
        while True:
            import sys; sys.stderr.write(f'{length}\r')
            for t in cls.recusively_enumerate_aux(primitives, length):
                yield t
            length += 1

    @classmethod
    def recusively_enumerate_aux(cls, primitives, length):
        if length == 1:
            for x in primitives:
                yield x
        else:
            for left_len in range(1, length):
                for t1, t2 in itertools.product(
                        cls.recusively_enumerate_aux(primitives, left_len),
                        cls.recusively_enumerate_aux(primitives, length - left_len)):
                    yield Expression(t1, t2).to_normal_form()

    def sreduce(self, pool=None, max_reductions=None):
        [reduced_term_cl,] = \
                random.sample(self.all_reductions(pool, max_reductions), 1)
        reduced_term, reactives, biproducts = reduced_term_cl()
        return reduced_term, reactives, biproducts
    
    def stochastically_reduces_to(self, tgoal, tout=100, tryouts=100):
        for i in range(tryouts):
            t = self
            for i in range(tout):
                if t == tgoal:
                    return True
                tnew, _, _ = t.sreduce(None)
                if tnew == t:
                    break
                t = tnew
        return False

    def is_egocentric(self, tout=10, tryouts=100):
        return self.is_reducible() and self.dreduce().stochastically_reduces_to(self, tout, tryouts)

    def bfs_reduces_to(self, tgoal, tout=100):
        if not self.is_reducible():
            return False
        ts = [self]
        for i in range(tout):
            new_gen = []
            for t in ts:
                new_gen.extend([f()[0] for f in t.all_reductions(None)])
            if tgoal in new_gen:
                return True
            ts = new_gen
        return False

    def reduces_until(self, tgoal, tout=100):
        t = self
        for i in range(tout):
            if t == tgoal:
                return t
            t = t.dreduce()
        return t

    def are_approx_coreducing(self, tgoal, tout=1000):
        t = self
        for i in range(tout):
            if t.approx(tgoal):
                return True
            t = t.dreduce()
            tgoal = tgoal.dreduce()
        return False

    def approx(self, t2, tolerance=50):
        l = self.prefix_length(t2)
        return l >= tolerance

    def prefix_length(self, t2):
        t1 = self
        if t1.is_leaf() or t2.is_leaf():
            return 1 if t1 == t2 else 0
        pl = 0
        for i in range(len(t1.children)):
            if i >= len(t2.children):
                break
            else:
                if t1.children[i] == t2.children[i]:
                    pl += t1.children[i].get_size()
                else:
                    pl += t1.children[i].prefix_length(t2.children[i])
                    break
        return pl

def get_reduction_reactives(term):
    reduced_term, is_reduced, reactives, biproducts = reduce_aux(term, None)
    return reactives

def get_reduction_products(term):
    reduced_term, is_reduced, reactives, biproducts = reduce_aux(term, None)
    if is_reduced:
        biproducts.append(reduced_term)
    return biproducts


#from expression_aux import Expression as A
#import types
#Expression.all_reductions_aux = A.all_reductions_aux

class AtomicExpression(Expression):
    def __init__(self, combinator):
        assert(isinstance(combinator, Combinator))
        self.combinator = combinator

    def is_leaf(self):
        return True

    def atoms(self):
        yield self

    def __str__(self):
        return str(self.combinator)

    def __repr__(self):
        return "{}'".format(repr(self.combinator))

    def __eq__(self, ot):
        if not isinstance(ot, AtomicExpression):
            return False
        return self.combinator == ot.combinator

    def __hash__(self):
        if not hasattr(self, 'cached_hash'):
            setattr(self, 'cached_hash', hash(self.combinator))
        return self.cached_hash

    def get_combinator(self):
        assert self.is_leaf()
        return self.combinator

    def get_size(self):
        return 1

    def get_depth(self):
        return 1

def expr(*children):
    if len(children) == 1:
        return children[0]
    else:
        return Expression(*children)

S = AtomicExpression(combinator_factory('S'))
K = AtomicExpression(combinator_factory('K'))
I = AtomicExpression(combinator_factory('I'))
C = AtomicExpression(combinator_factory('C'))
B = AtomicExpression(combinator_factory('B'))
W = AtomicExpression(combinator_factory('W'))

def atomic_factory(name):
    if name == 'S':
        return S
    elif name == 'K':
        return K
    elif name == 'I':
        return I
    elif name == 'C':
        return C
    elif name == 'B':
        return B
    elif name == 'W':
        return W

class EmptyExpression(object):
    def __add__(self, ot):
        return ot
    def __bool__(self):
        return False

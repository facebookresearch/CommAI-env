# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import logging
from collections import namedtuple
import expression as xp
import random

import logging
logger = logging.getLogger(__name__)

class Combinator(object):
    __slots__ = ('ttype', 'cached_hash')
    #ttype: str
    #p_r: float

    #def __new__(cls, ttype, p_r=None):
    #    return super(cls, Combinator).__new__(cls, ttype, p_r)

    def __init__(self, ttype):
        self.ttype = ttype

    def __hash__(self):
        if not hasattr(self, 'cached_hash'):
            setattr(self, 'cached_hash', ord(self.ttype))
        return self.cached_hash

    def __eq__(self, ot):
        if not isinstance(ot, Combinator):
            return False
        return self.ttype == ot.ttype

    def __len__(self):
        raise TypeError()

    def __iter__(self):
        raise TypeError()

    def get_ttype(self):
        return self.ttype

    def __str__(self):
        return self.ttype

    def __repr__(self):
        return self.ttype

    def can_reduce(self, args, pool=None):
        raise NotImplementedError()

class ICombinator(Combinator):
    def __init__(self):
        super(ICombinator, self).__init__('I')

    def can_reduce(self, args, pool=None):
        return len(args) >= 1

    def reduce(self, args, pool):
        arg0, args_tail = args[0], args[1:]
        return xp.Expression.concat(arg0, *args_tail), [], []

class KCombinator(Combinator):

    def __init__(self):
        super(KCombinator, self).__init__('K')

    def can_reduce(self, args, pool=None):
        return len(args) >= 2

    def reduce(self, args, pool):
        (arg0, arg1), args_tail = args[:2], args[2:]
        return xp.Expression.concat(arg0, *args_tail), [], [arg1]

class SCombinator(Combinator):

    def __init__(self):
        super(SCombinator, self).__init__('S')

    def can_reduce(self, args, pool=None):
        return len(args) >= 3 and (pool is None or args[2] in pool)

    def reduce(self, args, pool):
        (arg0, arg1, arg2), args_tail = args[:3], args[3:]
        #logger.debug(f'S x={arg0} y={arg1} z={arg2}')
        return xp.Expression.concat(
                xp.Expression(arg0, arg2, xp.Expression(arg1, arg2).to_surface_normal_form()), *args_tail), [arg2], []

class BCombinator(Combinator):
    def __init__(self):
        super(BCombinator, self).__init__('B')

    def can_reduce(self, args, pool=None):
        return len(args) >= 3

    def reduce(self, args, pool):
        (f, g, x), args_tail = args[:3], args[3:]
        return xp.Expression.concat(f(g(x)), *args_tail), [], []

class CCombinator(Combinator):
    def __init__(self):
        super(CCombinator, self).__init__('C')

    def can_reduce(self, args, pool=None):
        return len(args) >= 3

    def reduce(self, args, pool):
        (f, g, x), args_tail = args[:3], args[3:]
        return xp.Expression.concat(f, x, g, *args_tail), [], []

class WCombinator(Combinator):
    def __init__(self):
        super(WCombinator, self).__init__('W')

    def can_reduce(self, args, pool=None):
        return len(args) >= 2

    def reduce(self, args, pool):
        (x, y), args_tail = args[:2], args[2:]
        return xp.Expression.concat(x, y, y, *args_tail), [y], []

def combinator_factory(name):
    if name == 'S':
        return SCombinator()
    elif name == 'K':
        return KCombinator()
    elif name == 'I':
        return ICombinator()
    elif name == 'B':
        return BCombinator()
    elif name == 'C':
        return CCombinator()
    elif name == 'W':
        return WCombinator()


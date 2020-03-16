# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from collections import namedtuple
from expression import Expression
import numpy as np

class Reaction():
    __slots__ = ('products', 'type', 'reactives')

    def __init__(self, products, ttype, reactives):
        self.products = products
        self.type = ttype
        self.reactives = reactives

    def __hash__(self):
        return hash((self.products, self.type, self.reactives))

    def __eq__(self, ot):
        if not isinstance(ot, Reaction):
            return False
        return self.products == ot.products and self.type == ot.type and \
                self.reactives == ot.reactives

    def __lt__(self, ot):
        if self.type < ot.type:
            return True
        elif self.type == ot.type:
            if self.products < ot.products:
                return True
            elif self.products == ot.products:
                if self.reactives < ot.reactives:
                    return True
        return False

    def __str__(self):
        return f"[{self.type[0].upper()}] " + " + ".join(map(str, self.reactives)) + \
                    '->' + " + ".join(map(str, self.products))

    def __repr__(self):
        return str(self)

    def get_substrate(self):
        shortest_reactive_ix= np.argmin([len(r)
            for r in self.reactives])
        if self.type=='reduce' and len(self.reactives) > 1:
            return self.reactives[shortest_reactive_ix]

    def serializable(self):
        return {'products': tuple(map(str,self.products)), 'type': self.type, 
                'reactives': tuple(map(str, self.reactives))}

    @classmethod
    def unserialize(cls, r):
        products = r['products']
        typ = r['type']
        reactives = r['reactives']
        return Reaction(tuple(Expression.parse(product) for product in products),
                typ,
                tuple(Expression.parse(reactive) for reactive in reactives))


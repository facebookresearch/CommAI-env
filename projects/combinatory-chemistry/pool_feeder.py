# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from expression import Expression
class PoolFeeder():
    def __init__(self, food, period):
        self.food = food
        self.period = period

    def on_step_computed(self, pool, ticks):
        if ticks > 0 and ticks % self.period == 0:
            for f in self.food:
                for a in f.atoms():
                    pool.remove(a)
                pool.append(f)


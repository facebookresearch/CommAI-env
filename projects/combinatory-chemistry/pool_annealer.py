# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

class PoolAnnealer():
    def __init__(self, annealing):
        self.annealing = annealing

    def on_step_computed(self, pool, tick):
        if self.annealing == 0 or pool.p_reduce == 1:
            return
        pool.set_p_reduce(pool.p_reduce + self.annealing)

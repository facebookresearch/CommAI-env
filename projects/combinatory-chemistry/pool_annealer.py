class PoolAnnealer():
    def __init__(self, annealing):
        self.annealing = annealing

    def on_step_computed(self, pool, tick):
        if self.annealing == 0 or pool.p_reduce == 1:
            return
        pool.set_p_reduce(pool.p_reduce + self.annealing)

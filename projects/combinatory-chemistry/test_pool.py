import unittest
from pool import Pool
from expression import Expression

N = 1000
class TestPool(unittest.TestCase):
    def setUp(self):
        self.pool = Pool(N, 1./3, 1./3, 1./3)

    def test_constant_size_init(self):
        total_size = self.pool.get_total_size()
        self.assertEqual(total_size, N)

    def test_constant_size_combine(self):
        t1 = self.pool.pop_reactive()
        t2 = self.pool.pop_reactive()
        self.pool.tape_combine(t1, t2)
        total_size = self.pool.get_total_size()
        self.assertEqual(total_size, N)

    def test_break_conservation(self):
        for i in range(N//10):
            self.pool.remove(Expression.parse('I'))
            self.pool.remove(Expression.parse('S'))
            self.pool.append(Expression.parse('IS'))
        total_size = self.pool.get_total_size()
        self.assertEqual(total_size, N)
        for i in range(10*N):
            t = self.pool.pop_reactive()
            if not self.pool.tape_break(t):
                self.pool.rollback(t)
        total_size = self.pool.get_total_size()
        self.assertEqual(total_size, N)

    def test_combine_shrinks(self):
        self.assertEqual(len(self.pool), N)
        t1 = self.pool.pop_reactive()
        t2 = self.pool.pop_reactive()
        self.pool.tape_combine(t1, t2)
        self.assertEqual(len(self.pool), N - 1)

    def test_break_expands(self):
        n_combs = N//10
        for i in range(n_combs):
            self.pool.remove(Expression.parse('I'))
            self.pool.remove(Expression.parse('S'))
            self.pool.append(Expression.parse('IS'))
        self.assertEqual(len(self.pool), N - n_combs)
        for i in range(10*N):
            t = self.pool.pop_reactive()
            if not self.pool.tape_break(t):
                self.pool.rollback(t)
        self.assertEqual(len(self.pool), N)

    def test_reduce_expands(self):
        n_combs = N//10
        for i in range(n_combs):
            self.pool.remove(Expression.parse('I'))
            self.pool.remove(Expression.parse('S'))
            self.pool.append(Expression.parse('IS'))
            self.assertEqual(len(self.pool), N - i - 1)
        c = 0
        for i in range(10*N):
            t = self.pool.pop_reactive()
            if self.pool.tape_reduce(t):
                c += 1
                self.assertEqual(len(self.pool), N - n_combs + c)
            else:
                if len(t) == 2:
                    print(t.is_reducible(self.pool))
                self.pool.rollback(t)
        self.assertEqual(len(self.pool), N)


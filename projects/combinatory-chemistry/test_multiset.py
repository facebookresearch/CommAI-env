import unittest
from multiset import Multiset
from collections import Counter


class TestMultiset(unittest.TestCase):

    def test_add(self):
        ms = Multiset(10)
        ms.add('a')
        self.assertTrue('a' in ms)

    def test_remove(self):
        ms = Multiset(10)
        ms.add('a')
        ms.remove('a')
        self.assertTrue('a' not in ms)

    def test_add_twice_remove_twice(self):
        ms = Multiset(10)
        ms.add('a')
        ms.add('a')
        ms.remove('a')
        ms.remove('a')
        self.assertTrue('a' not in ms)

    def test_add_remove_twice(self):
        ms = Multiset(10)
        ms.add('a')
        ms.remove('a')
        ms.add('a')
        self.assertTrue('a' in ms)
        ms.remove('a')
        self.assertTrue('a' not in ms)

    def test_add_remove_many(self):
        ms = Multiset(200)
        for i in range(100):
            ms.add('a')
            ms.add('b')
        self.assertTrue('a' in ms)
        for i in range(100):
            ms.remove('a')
        for i in range(100):
            ms.remove('b')
        self.assertTrue('a' not in ms)

    def test_counts(self):
        ms = Multiset(10)
        self.assertEqual(ms['a'], 0)
        ms.add('a')
        self.assertEqual(ms['a'], 1)
        ms.add('a')
        self.assertEqual(ms['a'], 2)
        ms.remove('a')
        self.assertEqual(ms['a'], 1)
        ms.remove('a')
        self.assertEqual(ms['a'], 0)

    def test_sample(self):
        n = 10
        ms = Multiset(n)
        n_a, n_b, n_c = 5, 3, 2
        for i in range(n_a):
            ms.add('a')
        for i in range(n_b):
            ms.add('b')
        for i in range(n_c):
            ms.add('c')
        counts = Counter()
        N = 100000
        for i in range(N):
            x = ms.sample()
            counts[x] += 1
        self.assertAlmostEqual(counts['a']/N, n_a/n, 2)
        self.assertAlmostEqual(counts['b']/N, n_b/n, 2)
        self.assertAlmostEqual(counts['c']/N, n_c/n, 2)

    def test_sample_bias(self):
        n = 1000
        ms = Multiset(n)
        n_a, n_b, n_c = 900, 90, 10
        for i in range(n_a):
            ms.add('a')
        for i in range(n_b):
            ms.add('b')
        for i in range(n_c):
            ms.add('c')
        counts = Counter()
        N = 1000000
        for i in range(N):
            x = ms.sample()
            counts[x] += 1
        self.assertAlmostEqual(counts['a']/N, n_a/n, 2)
        self.assertAlmostEqual(counts['b']/N, n_b/n, 2)
        self.assertAlmostEqual(counts['c']/N, n_c/n, 2)

    def test_sample_unbalance(self):
        n = 10000
        ms = Multiset(n)
        for i in range(99):
            ms.add('a')
        ms.add('b')

        counts = Counter()
        for i in range(1000000):
            counts[ms.sample()] += 1
        self.assertAlmostEqual(counts['b']/counts['a'], 0.01, 3)

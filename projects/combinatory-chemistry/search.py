from expression import Expression, atomic_factory

p = Expression.parse
S = atomic_factory('S')
K = atomic_factory('K')
I = atomic_factory('I')


def search_unpacker():
    def condition(x):
        t1 = 'S(K(KS))'
        t2 = 'K(K(SK))'
        t3 = 'S(S(SS))'
        ex = {
                p(f'SII(SII){t1}'): t1,
                p(f'SII(SII){t2}'): t2,
                }
        for e, t in ex.items():
            if not x(e).reduces_to(p(t)):
                return False
        return True
    expr = Expression.search_first(condition, [S, K, I])
    print(expr)


if __name__ == '__main__':
    search_unpacker()

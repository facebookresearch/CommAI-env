import unittest
from expression import Expression, atomic_factory, expr
import pickle
import itertools

S = atomic_factory('S')
K = atomic_factory('K')
I = atomic_factory('I')
B = atomic_factory('B')
C = atomic_factory('C')
W = atomic_factory('W')
p = Expression.parse
e = expr
def x(*expr):
    return Expression(*expr).to_normal_form()

class TestExpression(unittest.TestCase):
    def run(self, result=None):
        if not result.errors:
            super(TestExpression, self).run(result)

    def test_pickleable(self):
        t = e(S)
        t2 = pickle.loads(pickle.dumps(t))
        self.assertEqual(t, t2)

    def test_is_leaf(self):
        self.assertTrue(S.is_leaf())

    def test_uniqueness(self):
        t = e(K, S)
        self.assertEqual(t, e(e(K), e(S)))

    def test_apply_parenthesis(self):
        t = e(K, e(K, S))
        self.assertEqual(t, e(e(K), e(e(K), e(S))))

    def test_normal_form(self):
        t = e(e(K, S), K).to_normal_form()
        self.assertEqual(t, e(e(K), e(S), e(K)))

    def test_join_flat(self):
        t1 = e(K) + e(S) + e(K)
        t2 = e(K, S, K)
        self.assertEqual(t1, t2)
 
    def test_join_hierarchical(self):
        t1 = e(K) + e(K, S) + e(K)
        t2 = e(K, e(K, S), K)
        self.assertEqual(t1, t2)

    def test_join_hierarchical_beginning(self):
        t1 = e(K, S) + e(K)
        t2 = e(K, S, K)
        self.assertEqual(t1, t2)
 
    def test_apply(self):
        t1 = e(K, S)
        t2 = e(K)
        self.assertEqual(t1.apply(t2), e(K, S, K))

    def test_apply_hierarchical(self):
        t1 = e(K, e(S, K))
        t2 = e(K, S)
        self.assertEqual(t1.apply(t2), e(K, e(S, K), e(K, S)))

    def test_parse_atom(self):
        t = Expression.parse('K')
        self.assertEqual(t, e(K))

    def test_parse_atom_par(self):
        t = Expression.parse('(K)')
        self.assertEqual(t, e(K))

    def test_parse(self):
        t = Expression.parse("S(SK)")
        self.assertEqual(t, e(S, e(S, K)))

    def test_parse_default_parenthesis(self):
        t = Expression.parse("SSK")
        self.assertEqual(t, e(S, S, K))

    def test_parse_default_parenthesis_remove(self):
        t = Expression.parse("((SS)K)")
        self.assertEqual(t, e(S, S, K))
 
    def test_parse_default_parenthesis_remove_embedded(self):
        t = Expression.parse("K(KKS)")
        self.assertEqual(t, e(K, e(K, K, S)))
 
    def test_parse_spaces(self):
        t = Expression.parse("S  ( S  K  )")
        self.assertEqual(t, e(S,e(S,K)))

    def test_parse_simplify(self):
        t = Expression.parse("(SK)")
        self.assertEqual(t, e(S, K))

    def test_parse_complex(self):
        t = Expression.parse("(SK(SK))S")
        self.assertEqual(t, 
                e(S, K, e(S, K), S))

    def test_parse_renormalize(self):
        t = Expression.parse('(SKK)S')
        self.assertEqual(t, e(S, K, K, S))

    def test_str_parsable(self):
        t = e(S, e(K, K), e(K, e(K, K), S, I))
        self.assertEqual(Expression.parse(str(t)), t)

    def test_str_parsable_atomic(self):
        t = e(S)
        self.assertEqual(Expression.parse(str(t)), t)

    def test_break(self):
        t = p('KS')
        l, r = t.top_break()
        self.assertEqual(l, e(K))
        self.assertEqual(r, e(S))

    def test_random_break(self):
        t = p('KS')
        l, r = t.random_break()
        self.assertEqual(l, e(K))
        self.assertEqual(r, e(S))
    
    def test_infix(self):
        t1 = p('KS')
        e = p('I')
        t2 = p('KS')
        t = e.infix(t1.children, t2.children)
        self.assertEqual(t, p('KSIKS'))

    def test_infix_hierarchical(self):
        t1 = p('KS')
        e = p('I')
        t2 = p('KS')
        t = e.infix(t1.children, (t2,))
        self.assertEqual(t, p('KSI(KS)'))

    def test_random_break_two(self):
        t = p('KSK')
        l, r = t.random_break()
        self.assertTrue(l == e(K) or l == e(K,S))
        if l == e(K):
            self.assertEqual(r, e(S, K))
        else:
            self.assertEqual(r, e(K))

    def test_random_break_hierarchical(self):
        t = p('K(SK)')
        l, r = t.random_break()
        self.assertEqual(l, e(K))
        self.assertEqual(r, e(S, K))

    def test_I_underarg(self):
        t = e(I)
        self.assertEqual(t.dreduce(), t)

    def test_I(self):
        t = e(I, K)
        self.assertEqual(t.dreduce(), e(K))
        
    def test_I_multiarg(self):
        t = e(I, K, S)
        self.assertEqual(t.dreduce(), e(K, S))

    def test_I_multiarg2(self):
        t = e(I, e(K, S))
        self.assertEqual(t.dreduce(), e(K, S))

    def test_K_underarg(self):
        t = e(K, K)
        self.assertEqual(t.dreduce(), e(K, K))

    def test_K(self):
        t = e(K, S, K)
        self.assertEqual(t.dreduce(), e(S))

    def test_K_multiarg(self):
        t = e(K, S, K, I)
        self.assertEqual(t.dreduce(), e(S, I))

    def test_K_multiarg2(self):
        t = e(K, e(S, K), I)
        self.assertEqual(t.dreduce(), e(S, K))

    def test_K_reduce(self):
        t1 = p('(KK)K')
        t2 = p('K')
        self.assertTrue(t1.reduces_to(t2))

    def test_K_reduce2(self):
        t1 = p('(((KK)K)K)S').to_normal_form()
        #print(t1, t1.to_surface_normal_form(), t1.to_normal_form())
        #t1= t1.to_normal_form()
        t2 = p('(KK)S')
        self.assertEqual(t1.dreduce(), t2)

    def test_K_reduce3(self):
        t1 = p('K(K(KK))S').to_normal_form()
        t2 = p('K(KK)')
        self.assertEqual(t1.dreduce(), t2)

    def test_K_reduce4(self):
        t1 = p('K(KK)K')
        t2 = p('KK')
        self.assertEqual(t1.dreduce(), t2)

    def test_S(self):
        t = e(S, K, I, K)
        self.assertEqual(t.dreduce(),  e(K, K, e(I, K)))

    def test_is_reducible(self):
        t = e(I, S)
        self.assertTrue(t.is_reducible())
        t = e(I, I, I)
        self.assertTrue(t.is_reducible())

    def test_is_reducible_nested(self):
        t = e(S, e(I, S))
        self.assertTrue(t.is_reducible())

    def test_reduce_nested(self):
        t = e(S, e(I, S))
        self.assertEqual(t.dreduce(), e(S, S))

    def test_reduce_nested2(self):
        t = e(S, e(I, I, I, I))
        self.assertEqual(t.dreduce(), e(S, e(I, I, I)))

    def test_size_atomic(self):
        t = e(K)
        self.assertEqual(t.get_size(), 1)

    def test_size(self):
        t = e(e(K, K), e(I, K))
        self.assertEqual(t.get_size(), 4)

    def test_str(self):
        t = e(I, S)
        self.assertEqual(str(t), "(IS)")
        t = e(S, e(I, S))
        self.assertEqual(str(t), "(S(IS))")
        t = e(e(K, K), e(I, K)).to_normal_form()
        self.assertEqual(str(t), "(KK(IK))")

    def test_enumerate_atoms(self):
        atoms = list(itertools.islice(Expression.recursively_enumerate([S,K,I]), 3))
        for x in [S, K, I]:
            self.assertTrue(x in atoms)

    def test_enumerate_binary(self):
        exprs = set(itertools.islice(Expression.recursively_enumerate([S, K, I]), 12))
        self.assertEqual(len(exprs), 12)  # no repetitions
        for t in exprs:
            self.assertTrue(t.get_size() <= 2)

    def test_enumerate_ternary(self):
        exprs = set(itertools.islice(Expression.recursively_enumerate([S, K, I]), 39))
        self.assertEqual(len(exprs), 39)  # no repetitions
        for t in exprs:
            self.assertTrue(t.get_size() <= 3, t)

    def test_all_reductions(self):
        t = p('IK(IK)K')
        self.assertEqual(len(t.all_reductions()), 2)
        exp_reds = [p('IK(K)K'), p('K(IK)K')]
        for cl in t.all_reductions():
            red, _, _ = cl()
            self.assertTrue(red in exp_reds)

    def test_all_reductions_nested(self):
        t = p('IK(IK(IK))K')
        self.assertEqual(len(t.all_reductions()), 3)
        exp_reds = [p('IK(K(IK))K'), p('K(IK(IK))K'), p('IK(IK(K))K')]
        for cl in t.all_reductions():
            red, _, _ = cl()
            self.assertTrue(red in exp_reds)

    def test_all_reductions_nested_max(self):
        t = p('IK(IK(IK))K')
        self.assertEqual(len(t.all_reductions(max_reductions=2)), 2)
        exp_reds = [p('IK(K(IK))K'), p('K(IK(IK))K')]
        for cl in t.all_reductions(max_reductions=2):
            red, _, _ = cl()
            self.assertTrue(red in exp_reds)


    def test_all_reductions_complicated(self):
        t = p('(S(K(K(I(K(SK(S(SK))))(S(S(I(K(IK)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(SI(S(SI)I)(S(SI)I))))))))))))))))))))))S)I)K)IK)II)S))K)IKI(SKI))')
        with open('complicated_reductions.txt') as exprs_f:
            correct_reductions = set([(p(l.rstrip('\n'))) for l in exprs_f])
        t_reductions = t.all_reductions()
        t_reductions_expr  = set(red()[0] for red in t_reductions)
        self.assertEqual(len(correct_reductions), len(t_reductions_expr))
        for e in t_reductions_expr:
            self.assertTrue(e in correct_reductions)

    def test_all_reductions_complicated_max(self):
        t = p('(S(K(K(I(K(SK(S(SK))))(S(S(I(K(IK)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(I(S(SI)I)(SI(S(SI)I)(S(SI)I))))))))))))))))))))))S)I)K)IK)II)S))K)IKI(SKI))')
        with open('complicated_reductions.txt') as exprs_f:
            correct_reductions = set([(p(l.rstrip('\n'))) for l in exprs_f][:10])
        t_reductions = t.all_reductions(max_reductions=10)
        t_reductions_expr  = set(red()[0] for red in t_reductions)
        self.assertEqual(len(correct_reductions), len(t_reductions_expr))
        for e in t_reductions_expr:
            self.assertTrue(e in correct_reductions)


    def test_all_reductions_atom(self):
        self.assertEqual(len(Expression.all_reductions(e(I))), 1)
        [cl,] = Expression.all_reductions(e(I))
        (reduced, reactives, biproducts) = cl()


    def test_all_reductions_identities(self):
        t = p('II')
        self.assertEqual(Expression.all_reductions(t)[0](), (e(I), [], [e(I)]))

    def test_quine(self):
        t = p('(SII)(SII)')
        self.assertTrue(t.sreduce()[0].stochastically_reduces_to(t))

    def test_egocentric(self):
        t = p('SII(SII)')
        self.assertTrue(t.is_egocentric())
        t = p('(SII)')
        self.assertFalse(t.is_egocentric())

    def test_egocentric_complex(self):
        t = p('I(SII)(I(SII))ISK')
        for i in range(100):
            t = t.sreduce()[0]

    def disabled_test_find_quine(self):
        for t in Expression.recursively_enumerate([S, K, I]):
            if t.is_reducible(None) and t.dreduce().stochastically_reduces_to(t):
                print(t)
                self.assertTrue(True)
                break

    def disabled_test_find_growing(self):
        for t in Expression.recursively_enumerate([S, K, I]):
            torig = t
            for i in range(3):
                t2 = t.dreduce()
                if t.is_reducible() and t2.get_size() > t.get_size():
                    t = t2
                else:
                    break
            else:
                print(torig)

    def disable_test_find_voter(self):
        e_vector = p("K(K(KS))")
        r_vector = p("K(K(SK))")
        for t in Expression.recursively_enumerate([S, K, I, B, C, W]):
            import sys; sys.stdout.write(f'Testing length {len(t)}\r')
            if not t.reduces_to(e_vector) and \
                    t.reduces_to(r_vector):
                print(t)
                break

    def test_numbers(self):
        defs = {
                'succ': p("K"),
                'one': p("S"),
                'two': p("KS"),
                'three': p("K(KS)"),
                'four': p("K(K(KS))"),
            }
        self.assertFact(('succ', 'one'), 'two', defs)
        self.assertFact(('succ', 'two'), 'three', defs)
        self.assertFact(('succ', 'three'), 'four', defs)

    def test_boolean(self):
        defs = {
                'true': p('K K'),
                'false': p('K'),
                'and': p('((S (S (S S))) (K (K K)))'),
                'or': p('((S S) (K (K K)))'),
                'not': p('((S ((S K) S)) (K K))')
        }
        self.assertFact(('or', 'true', 'false'), 'true', defs)
        self.assertFact(('or', 'false', 'true'), 'true', defs)
        self.assertFact(('or', 'true', 'true'), 'true', defs)
        self.assertFact(('or', 'false', 'false'), 'false', defs)
        self.assertFact(('and', 'true', 'false'), 'false', defs)
        self.assertFact(('and', 'false', 'true'), 'false', defs)
        self.assertFact(('and', 'true', 'true'), 'true', defs)
        self.assertFact(('and', 'false', 'false'), 'false', defs)
        self.assertFact(('not', 'false'), 'true', defs)
        self.assertFact(('not', 'true'), 'false', defs)

    def test_even_odd(self):
        defs = {
                'true': p('K K'),
                'odd': p("((S ((S (K S) K) K)) (S K K))"),
                'even': p("((S (S K K)) (K K))"),
                'succ': p("(((S (K (S (K (S S (K K))) K)) S) (S K K)) K)"),
                'one': p("(((S (K (S (K (S S (K K))) K)) S) (S K K)) (K K))"),
            }
        defs['two'] = x(defs['succ'], defs['one'])
        defs['three'] = x(defs['succ'], defs['two'])
        defs['four'] = x(defs['succ'], defs['three'])
        self.assertFact(('odd', 'one'), 'true', defs)
        self.assertFact(('even', 'two'), 'true', defs)
        self.assertFact(('odd', 'three'), 'true', defs)
        self.assertFact(('even', 'four'), 'true', defs)
        self.assertFalseFact(('even', 'one'), 'true', defs)
        self.assertFalseFact(('odd', 'two'), 'true', defs)
        self.assertFalseFact(('even', 'three'), 'true', defs)
        self.assertFalseFact(('odd', 'four'), 'true', defs)

    def test_prefix_length(self):
        t1 = e(K, K, S)
        t2 = e(K, K, I)
        self.assertEqual(t1.prefix_length(t2), 2)

    def test_prefix_length_rec(self):
        t1 = e(K, e(K, S))
        t2 = e(K, e(K, I))
        self.assertEqual(t1.prefix_length(t2), 2)

    def test_prefix_length_rec2(self):
        t1 = e(K, e(K, e(S, K)))
        t2 = e(K, e(K, e(I, K)))
        self.assertEqual(t1.prefix_length(t2), 2)

    def test_recursion(self):
        defs = {
                'Y': p('(((S (K S) K) ((S ((S (K (S (K (S S (K K))) K)) S) (S (S (S K K))))) S)) (S (K S) K))'),
                #'Y': p('SSK(S(K(SS(S(SSK))))K)'),
                'f': p('K')
            }
        Yf = self.resolve(('Y', 'f'), defs)
        fYf = self.resolve(('f', ('Y', 'f')), defs)
        self.assertTrue(Yf.are_approx_coreducing(fYf))

    def test_repetition(self):
        defs = {
                'repeat': p('((S (S (K S) K)) (S K K))'),
                'f': p('K'),
                'x': p('K')
            }
        self.assertFact((('repeat', 'f'), 'x'), ('f', ('f', 'x')), defs)

    def test_identity(self):
        defs = {
                'id': p('SKK'),
                'x': p('KSKS')
            }
        self.assertFact(('id', 'x'),'x', defs)

    def assertFact(self, e1, e2, defs):
        f1 = self.resolve(e1, defs)
        f2 = self.resolve(e2, defs)
        self.assertTrue(f1.reduces_to(f2))

    def assertFalseFact(self, e1, e2, defs):
        f1 = self.resolve(e1, defs)
        f2 = self.resolve(e2, defs)
        self.assertFalse(f1.reduces_to(f2))

    def resolve(self, expr, defs):
        def map_def(f):
            if isinstance(f, tuple):
                return x(*(map_def(x) for x in f))
            else:
                return defs[f]
        return map_def(expr)


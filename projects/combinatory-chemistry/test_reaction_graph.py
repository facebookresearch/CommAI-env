# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import unittest
from reaction_graph import ReactionGraph
from expression import Expression
from reaction import Reaction

_ = Expression.parse

class TestReactionGraph(unittest.TestCase):

    def test_raf_chain(self):
        g = ReactionGraph()
        rs = [Reaction((_('K'),), 'reduce', (_('S'),)),
                Reaction((_('S'),_('X')), 'reduce', (_('K'),))]
        for r in rs:
            g.add_reaction(r)
        raf = g.get_raf([_('X')])
        self.assertEqual(len(raf), 2)
        for r in rs:
            self.assertTrue(r in raf)


    def test_raf_chain_out(self):
        g = ReactionGraph()
        raf_rs = [Reaction((_('K'),), 'reduce', (_('S'),)),
                Reaction((_('S'),_('X')), 'reduce', (_('K'),)),
                ]
        out_rs = [
                Reaction((_('I'),), 'reduce', (_('KK'),)),
                ]
        rs = raf_rs + out_rs
        for r in rs:
            g.add_reaction(r)
        raf = g.get_raf([_('X')])
        self.assertEqual(len(raf), len(raf_rs))
        for r in raf_rs:
            self.assertTrue(r in raf)


    def test_not_a_raf(self):
        g = ReactionGraph()
        rs = [Reaction((_('K'),_('I')), 'reduce', (_('IK'),)),
                Reaction((_('KIK'),_('K')), 'reduce', (_('KIKK'),)),
                Reaction((_('KIKK'),), 'reduce', (_('KKKKK'),))
                ]
        for r in rs:
            g.add_reaction(r)
        raf = g.get_raf([_('I'), _('K'), _('S')])
        self.assertEqual(len(raf), 0)


    def test_scc(self):
        g = ReactionGraph()
        rs = [
                Reaction((_('SII(SII)'),), 'reduce', (_('I(SII)(SII)'),)),
                Reaction((_('SII(SII)'),), 'reduce', (_('SII(I(SII))'),)),
                Reaction((_('I(SII)(I(SII))'),), 'reduce', (_('SII(SII)'),)),
                Reaction((_('I(SII)(SII)'),), 'reduce', (_('I(SII)(I(SII))'),)),
                Reaction((_('SII(I(SII))'),), 'reduce', (_('I(SII)(I(SII))'),)),
        ]
        for r in rs:
            g.add_reaction(r)
        sccs = list(g.remove_selfloop().get_without_substrates_subgraph().get_all_strongly_connected_components())
        self.assertEqual(len(sccs), 1)
        for x in rs:
            self.assertTrue(x in set(sccs[0]))
        self.assertEqual(g.get_maximal_cycle_length(), 3)


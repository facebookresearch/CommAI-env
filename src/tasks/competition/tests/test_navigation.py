# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
from worlds.grid_world import GridWorld
import tasks.competition.messages as msg
import tasks.competition.navigation as navigation
import tasks.competition.repetition as repetition
from tasks.competition.tests.helpers import task_messenger
import random


class TestNavigation(unittest.TestCase):

    #
    # helper methods
    #
    def check_positive_feedback(self, m, instructions):
        # hear the congratulations
        feedback_blen = m.read()
        # there is some feedback
        self.assertGreater(feedback_blen, 0)
        m.send()
        self.assertEqual(m.get_cumulative_reward(), 1)

    def check_negative_feedback(self, m):
        # hear the feedback
        m.read()
        feedback = m.get_last_message()
        # it should be bad-learner sort of feedback
        self.failUnless(feedback in msg.failed or feedback in msg.timeout,
                        'Unexpected negative feedback: {0}'.format(feedback))

    def solve_correctly_test(self, m, solve):
        # read the instructions
        m.read()
        # get the instructions
        instructions = m.get_last_message()
        # solve the problem
        solve(m)
        # hear the congratulations
        self.check_positive_feedback(m, instructions)

    def timeout_test(self, m, solve):
        # read the instructions
        m.read()
        # stay silent
        while m.is_silent():
            m.send()
        # hear the correction
        self.check_negative_feedback(m)

    def do_test_battery(self, task, solve):
        with task_messenger(task, GridWorld) as m:
            # test for solving the task correctly
            self.solve_correctly_test(m, solve)
        with task_messenger(task, GridWorld) as m:
            # test for not solving it at all
            self.timeout_test(m, solve)

    #
    # tasks testing routines
    #

    # this has been moved into repetition
    def testAssociateObjectWithProperty(self):
        def solve(m):
            # find the answer in the instructions
            verb, = m.search_last_message(r"'I (\w+)'")
            m.send("I {verb}.".format(verb=verb))
        self.do_test_battery(repetition.VerbTask,
                             solve)

    def testTurningTask(self):
        def solve(m):
            # find the answer in the instructions
            direction, = m.search_last_message(r"Turn (\w+)")
            m.send("I turn {direction}.".format(direction=direction))
        self.do_test_battery(navigation.TurningTask,
                             solve)

    def testMoving(self):
        def solve(m):
            # find the answer in the instructions
            m.send("I move forward.")
        self.do_test_battery(navigation.MovingTask,
                             solve)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

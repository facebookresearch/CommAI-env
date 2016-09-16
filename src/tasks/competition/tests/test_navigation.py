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
        self.assertTrue(feedback in msg.failed or feedback in msg.timeout,
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

    def testMovingRelative(self):
        def solve(m):
            direction, = m.search_last_message(r"Move (\w+)")
            m.send("I turn {direction}.".format(direction=direction))
            # wait for feedback
            m.read()
            # move
            m.send("I move forward.")
        self.do_test_battery(navigation.MovingRelativeTask,
                             solve)

    def testMovingAbsolute(self):
        def solve(m):
            init_direction, dest_direction = m.search_last_message(
                r"facing (\w+), move (\w+)")
            directions = ['north', 'east', 'south', 'west']
            init_dir_idx = directions.index(init_direction)
            dest_dir_idx = directions.index(dest_direction)
            delta = (dest_dir_idx - init_dir_idx) % 4
            if delta == 3:
                delta = -1
            if delta > 0:
                direction = "right"
            else:
                direction = "left"
            for i in range(abs(delta)):
                m.send("I turn {direction}.".format(direction=direction))
                # wait for feedback
                m.read()
            # move
            m.send("I move forward.")
        self.do_test_battery(navigation.MovingAbsoluteTask,
                             solve)

    def testPickUp(self):
        def solve(m):
            object_, = m.search_last_message(r"Pick up the (\w+)")
            m.send("I pick up the {object}.".format(object=object_))
        self.do_test_battery(navigation.PickUpTask,
                             solve)

    def testPickUpAround(self):
        def solve(m):
            dest_direction, object_ = m.search_last_message(
                r"(\w+) from you, pick up the (\w+)")
            directions = ['north', 'east', 'south', 'west']
            init_dir_idx = directions.index('north')
            dest_dir_idx = directions.index(dest_direction)
            delta = (dest_dir_idx - init_dir_idx) % 4
            if delta == 3:
                delta = -1
            if delta > 0:
                direction = "right"
            else:
                direction = "left"
            for i in range(abs(delta)):
                m.send("I turn {direction}.".format(direction=direction))
                # wait for feedback
                m.read()
            # pick up the object
            m.send("I pick up the {object}.".format(object=object_))
        self.do_test_battery(navigation.PickUpAroundTask,
                             solve)

    def testPickUpInFront(self):
        def solve(m):
            nsteps, object_ = m.search_last_message(
                r"(\w+) steps forward, pick up the (\w+)")
            nsteps = msg.string_to_number(nsteps)
            for i in range(nsteps - 1):
                m.send("I move forward.")
                # wait for feedback
                m.read()
            # move
            m.send("I pick up the {object}.".format(object=object_))
        self.do_test_battery(navigation.PickUpInFrontTask,
                             solve)

    def testGiving(self):
        def solve(m):
            article, object_ = m.search_last_message(r"I gave you (\w+) (\w+)")
            m.send("I give you {article} {object}.".format(article=article,
                                                           object=object_))
        self.do_test_battery(navigation.GivingTask,
                             solve)

    def testPickUpAroundAndGive(self):
        def solve(m):
            article, object_, dest_direction = m.search_last_message(
                r"There is (\w+) (\w+) (\w+)")
            directions = ['north', 'east', 'south', 'west']
            init_dir_idx = directions.index('north')
            dest_dir_idx = directions.index(dest_direction)
            delta = (dest_dir_idx - init_dir_idx) % 4
            if delta == 3:
                delta = -1
            if delta > 0:
                direction = "right"
            else:
                direction = "left"
            for i in range(abs(delta)):
                m.send("I turn {direction}.".format(direction=direction))
                # wait for feedback
                m.read()
            m.send("I pick up the {object}.".format(object=object_))
            m.read()
            m.send("I give you {article} {object}.".format(article=article,
                                                           object=object_))
        self.do_test_battery(navigation.PickUpAroundAndGiveTask,
                             solve)

    def testCountingInventoryGiving(self):
        def solve(m):
            object_, = m.search_last_message(r"How many (\w+)")
            # I don't have anything in the beginning
            m.send(msg.number_to_string(0) + ".")
            m.read()
            article, object_, = m.search_last_message(r"I gave you (\w+) (\w+)")
            # The teacher just gave me somthing
            m.send(msg.number_to_string(1) + ".")
            m.read()
            # Give the object back to the teacher
            m.send("I give you {article} {object}.".format(article=article,
                                                           object=object_))
            m.read()
            # I don't have anything anymore
            m.send(msg.number_to_string(0) + ".")
        self.do_test_battery(navigation.CountingInventoryGivingTask,
                             solve)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

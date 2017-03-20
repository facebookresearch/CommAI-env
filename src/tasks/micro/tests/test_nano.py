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
import tasks.micro.nano as nano
from core.task import on_start, on_message
from tasks.competition.tests.helpers import task_messenger
from core.serializer import IdentitySerializer


class TestRepetitionTasks(unittest.TestCase):
        #
        # task testing routines
        #

        def trySolution(self, Task, patient, solution, correct):
            with task_messenger(lambda: Task(patient=patient),
                                serializer=IdentitySerializer()) as m:
                    N = m._env._max_reward_per_task
                    # rewards will be negative or positive
                    sign = correct and 1 or -1
                    # try to get as much reward as possible from the solution
                    for i in range(N):
                        m.send(solution)
                        self.assertEqual(m.get_cumulative_reward(),
                                         sign * (i + 1))

        def testTask0(self):
            # Impatient solutions

            # you have to stay silent for 5 bits (because by the time the
            # 6th bit gets emitted, the task is already rewarding you for being
            # silent), and then wait for one more bit for the task separator
            # (to be removed later)
            # This leads to 1 / 32 correct ratio
            self.trySolution(nano.Task0, patient=False, solution="0000000",
                             correct=True)
            self.trySolution(nano.Task0, patient=False, solution="0000001",
                             correct=True)
            # and also the last bit of the task doesn't really count
            self.trySolution(nano.Task0, patient=False, solution="0000010",
                             correct=True)
            self.trySolution(nano.Task0, patient=False, solution="0000011",
                             correct=True)

            # speaking earlier shouldn't work and stop you
            self.trySolution(nano.Task0, patient=False, solution="000010",
                             correct=False)
            # the patient teacher waits a bit longer
            self.trySolution(nano.Task0, patient=True, solution="0000100",
                             correct=False)

        def testTask1(self):
            # You have to say 1 by the 7th bit
            self.trySolution(nano.Task1, patient=False, solution="00000010",
                             correct=True)
            # What you say on the 8th bit doesn't matter
            self.trySolution(nano.Task1, patient=False, solution="00000011",
                             correct=True)
            # By the 8th bit is already too late
            self.trySolution(nano.Task1, patient=False, solution="00000001",
                             correct=False)
            # And the 6th bit too early
            self.trySolution(nano.Task1, patient=False, solution="0000010",
                             correct=False)
            # With a patient teacher you have to wait for the 8 bits of the
            # task + 1 of the separator
            self.trySolution(nano.Task1, patient=True, solution="000001000",
                             correct=False)

        def testTask10(self):
            # You have to say 10 by the 8th bit
            self.trySolution(nano.Task10, patient=False, solution="0000000100",
                             correct=True)
            # What you say on the 9th bit doesn't matter
            self.trySolution(nano.Task10, patient=False, solution="0000000101",
                             correct=True)
            # If you didn't put a 1 in the 8th bit, you are lost no matter
            # what you do on the 9th bit
            self.trySolution(nano.Task10, patient=False, solution="000000000",
                             correct=False)
            self.trySolution(nano.Task10, patient=False, solution="000000001",
                             correct=False)
            # And the 7th bit istoo early
            self.trySolution(nano.Task10, patient=False, solution="00000010",
                             correct=False)
            # With a patient teacher you have to wait for the 10 bits of the
            # task + 1 of the separator
            self.trySolution(nano.Task10, patient=True, solution="00000010000",
                             correct=False)

        def testTask11(self):
            # You have to say 10 by the 8th bit
            self.trySolution(nano.Task11, patient=False, solution="0000000110",
                             correct=True)
            # What you say on the 9th bit doesn't matter
            self.trySolution(nano.Task11, patient=False, solution="0000000111",
                             correct=True)
            # If you didn't put a 1 in the 8th bit, you are lost no matter
            # what you do on the 9th bit
            self.trySolution(nano.Task11, patient=False, solution="000000000",
                             correct=False)
            self.trySolution(nano.Task11, patient=False, solution="000000001",
                             correct=False)
            # And the 7th bit is too early
            self.trySolution(nano.Task11, patient=False, solution="00000010",
                             correct=False)
            self.trySolution(nano.Task11, patient=False, solution="00000011",
                             correct=False)
            # With a patient teacher you have to wait for the 10 bits of the
            # task + 1 of the separator
            self.trySolution(nano.Task11, patient=True, solution="00000011000",
                             correct=False)


def main():
    unittest.main()


if __name__ == '__main__':
    main()

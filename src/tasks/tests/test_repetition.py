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
import tasks.repetition as repetition
from tasks.tests.helpers import task_messenger


class TestRepetitionTasks(unittest.TestCase):

    def check_positive_feedback(self, m, instructions, answer):
        # hear the congratulations
        feedback_blen = m.read()
        # there is some feedback
        self.assertGreater(feedback_blen, 0)
        m.send()
        self.assertEqual(m.get_cumulative_reward(), 1,
                         "answering '{0}' to query '{1}' didn't work.".format(
                             answer, instructions))

    def testBeSilent(self):
        with task_messenger(repetition.BeSilentTask) as m:
            # read the instructions
            instructions_blen = m.read()
            instructions = m.get_last_message()
            # there are some instructions
            self.assertGreater(instructions_blen, 0)
            # stay silent until rewarded
            for x in range(1000):
                if m.get_cumulative_reward() > 0:
                    break
                m.send()
            self.assertEqual(m.get_cumulative_reward(), 1)
            # read the instructions again
            instructions_blen = m.read()
            instructions = m.get_last_message()
            # there are some instructions
            self.assertGreater(instructions_blen, 0)
            # we fail
            m.send('a')
            self.assertEqual(m.get_cumulative_reward(), 1)
            # we should have prompted a restart
            m.read()
            instructions = m.get_last_message()
            # there are some instructions
            self.assertGreater(len(instructions), 0)
            self.assertEqual(m.get_cumulative_reward(), 1)

    def solve_correctly_test(self, m, get_correct_answer):
        # wait for the instructions
        instructions_blen = m.read()
        instructions = m.get_last_message()
        # there are some instructions
        self.assertGreater(instructions_blen, 0)
        answer = get_correct_answer(m)
        # repeat it
        m.send(answer + ".")
        self.check_positive_feedback(m, instructions, answer)

    def repeat_everything(self, m, get_correct_answer):
        # first, send one silence
        m.send()
        while not m.is_silent():
            # repeat the previous char sent by the teacher
            m.send(m.get_text()[-1])
        m.send(m.get_text()[-1])
        # read feedback, if any
        m.read()
        self.assertEqual(m.get_cumulative_reward(), 0,
                         "Memory-less repeating cannot work")

    def do_test_battery(self, task, get_correct_answer):
        with task_messenger(task) as m:
            # test for solving the task correctly
            self.solve_correctly_test(m, get_correct_answer)
        with task_messenger(task) as m:
            # test for not solving it at all
            self.repeat_everything(m, get_correct_answer)

    def testRepeatWhatISay(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, = m.search_last_message(r"(?:{verb}) (.*)\.".format(
                verb="|".join(repetition.verbs)))
            return answer
        self.do_test_battery(repetition.RepeatWhatISayTask, get_correct_answer)

    def testRepeatWhatISay2(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, = m.search_last_message(
                r"(?:{verb}) (.*) (?:{context})\.".format(
                    verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            return answer
        self.do_test_battery(repetition.RepeatWhatISay2Task, get_correct_answer)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

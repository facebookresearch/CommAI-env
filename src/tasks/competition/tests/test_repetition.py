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
import tasks.competition.repetition as repetition
import tasks.competition.messages as msg
from tasks.competition.tests.helpers import task_messenger


class TestRepetitionTasks(unittest.TestCase):
    #
    # helper methods
    #

    def check_positive_feedback(self, m, instructions, answer):
        # hear the congratulations
        feedback_blen = m.read()
        # there is some feedback
        self.assertGreater(feedback_blen, 0)
        m.send()
        self.assertEqual(m.get_cumulative_reward(), 1,
                         "answering '{0}' to query '{1}' didn't work.".format(
                             answer, instructions))

    def check_negative_feedback(self, m, exp_answer):
        # hear the feedback
        m.read()
        try:
            answer, = m.search_last_message(
                r"correct answer is: (.+)\.$")
            self.assertEqual(answer, exp_answer)
        except RuntimeError:
            # if the correct message wasn't given, the feedback was
            # an error message
            self.assertIn(m.get_last_message(), msg.failed)

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

    def add_ending_garbage_test(self, m, get_correct_answer):
        # wait for the instructions
        instructions_blen = m.read()
        # there are some instructions
        self.assertGreater(instructions_blen, 0)
        answer = get_correct_answer(m)
        # repeat it with some garbage at the end
        m.send(answer + " spam, spam, eggs, bacon and spam.")
        # hear feedback if there is any
        self.check_negative_feedback(m, answer)
        self.assertEqual(m.get_cumulative_reward(), 0,
                         "The correct answer must be an exact match.")
        # stay silent until the end
        while m.is_silent():
            m.send()
        self.assertEqual(m.get_cumulative_reward(), 0,
                         "The correct answer must be an exact match.")

    def timeout_test(self, m, get_correct_answer):
        # read the instructions
        m.read()
        # get the answer
        answer = get_correct_answer(m)
        # stay silent
        while m.is_silent():
            m.send()
        # hear the correction
        self.check_negative_feedback(m, answer)
        self.assertEqual(m.get_cumulative_reward(), 0,
                         "Doing nothing is not a solution")

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
        with task_messenger(task) as m:
            # test for not solving it at all
            self.add_ending_garbage_test(m, get_correct_answer)
        with task_messenger(task) as m:
            # test for solving the task correctly
            self.timeout_test(m, get_correct_answer)

    #
    # task testing routines
    #
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

    def testRepeatCharacter(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, = m.search_last_message(r"(?:{verb}) (\w)\.".format(
                verb="|".join(repetition.verbs)))
            return answer
        task = repetition.RepeatCharacterTask
        # cannot use the add ending garbage test here
        # (spam. could prompt a correct answer if the query is for m)
        with task_messenger(task) as m:
            # test for solving the task correctly
            self.solve_correctly_test(m, get_correct_answer)
        with task_messenger(task) as m:
            # test for not solving it at all
            self.repeat_everything(m, get_correct_answer)
        with task_messenger(task) as m:
            # test for solving the task correctly
            self.timeout_test(m, get_correct_answer)

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

    def testRepeatWhatISayMultipleTimes(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times\.".format(
                    verb="|".join(repetition.verbs)))
            return " ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(repetition.RepeatWhatISayMultipleTimesTask,
                             get_correct_answer)

    def testRepeatWhatISayMultipleTimes2(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times (?:{context})\.".format(
                    verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            return " ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(repetition.RepeatWhatISayMultipleTimes2Task,
                             get_correct_answer)

    def testRepeatWhatISayMultipleTimesSeparatedByComma(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times separated".format(
                    verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            return ", ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(
            repetition.RepeatWhatISayMultipleTimesSeparatedByCommaTask,
            get_correct_answer)

    def testRepeatWhatISayMultipleTimesSeparatedByAnd(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times separated".format(
                    verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            return " and ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(
            repetition.RepeatWhatISayMultipleTimesSeparatedByAndTask,
            get_correct_answer)

    def testRepeatWhatISayMultipleTimesSeparatedByCA(self):
        def get_correct_answer(m):
            # get the string to be repeated
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times separated".format(
                    verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            enum = [answer] * msg.string_to_number(n)
            return " and ".join([", ".join(enum[:-1]), enum[-1]])
        self.do_test_battery(
            repetition.RepeatWhatISayMultipleTimesSeparatedByCATask,
            get_correct_answer)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

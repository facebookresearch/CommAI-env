from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
import tasks.micro.small_comp as small_comp
from tasks.competition.tests.helpers import task_messenger
from core.serializer import IdentitySerializer


class TestSmallCompTasks(unittest.TestCase):

    #
    # helper methods
    #

    def _test_solution(self, Task, get_answer, answer_correct=True):
        sign = answer_correct and 1 or -1
        with task_messenger(Task,
                            serializer=IdentitySerializer()) as m:
            # we will solve the task N times (to check for sync issues)
            N = m._env._max_reward_per_task
            for i in range(N):
                # wait for the instructions
                instructions_blen = m.read()
                # there are some instructions
                self.assertGreater(instructions_blen, 0, "No instructions!")
                # we should have received the reward from the previous iteration
                self.assertEqual(m.get_cumulative_reward(),
                                 sign * i)
                # extract the correct answer
                answer = get_answer(m)
                m.send(answer)
                # get the next task going
                m.send()

    #
    # unit tests
    #

    def testReverseXTask(self):
        # function that reads the instructions and produces the correct answer
        def get_correct_answer(m):
            answer, = m.search_full_message(r"V([01]*)\.$")
            return answer[::-1]

        # function that reads the instructions and produces an incorrect answer
        def get_incorrect_answer_impatient(m):
            answer, = m.search_full_message(r"V([01]*)\.$")
            return "1" if answer[-1] == "0" else "0"

        # try to solve correctly
        self._test_solution(small_comp.ReverseXTask, get_correct_answer, True)
        # try to solve incorrectly with an impatient teacher
        self._test_solution(small_comp.ReverseXTask,
                            get_incorrect_answer_impatient, False)


def main():
    unittest.main()


if __name__ == '__main__':
    main()

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import on_start, on_message, on_timeout
from tasks.competition.base import BaseTask
import random
import string
import re

# list of congratulation and failed messages, in case we
# want to play with it
micro_congratulations = ['correct.']
# a list of congratulations messages to be issued when the learner fails a task
micro_failed = ['wrong: ']

# a function that takes two positive integers as input
# 1) the alphabet vocabulary size V (<=26) and
# 2) maximum string length L
# and returns a string of maximally L random upper-case characters sampled
# from the first V in the English alphabe
def return_random_string(V,L):
    if (V>26 or V<1):
        raise ValueError(str(V) + ' is outside legal vocabulary range (1-26)')
    if (L<1):
        raise ValueError(str(L) + ' is not a possible string length')
    V=V-1
    maxL=random.randint(1,L)
    random_string = ""
    for i in range(maxL):
        random_string += chr(ord('A') + random.randint(0, V))
    return random_string

class Repeat1V1L(BaseTask):
    def __init__(self, world=None):
        super(Repeat1V1L, self).__init__(world=world, max_time=(64+((8*1)+8)*3))
        # NB: we use a formula for max_time, in the hope to remember
        # to adjust it from task to task: the only variable should
        # be the value equal to L

    @on_start()
    def give_instructions(self, event):
        self.target_string = return_random_string(1,1)
        self.set_message("repeat: " + self.target_string + ".")

    @on_message(r"\.")
    def check_response(self, event):
        if event.is_message(self.target_string, '.'):
            self.set_reward(1, random.choice(micro_congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def give_away_answer(self, event):
        self.fail_learner()

    def fail_learner(self):
        feedback = random.choice(micro_failed)
        feedback += self.target_string + '.'
        self.set_reward(0, feedback)


class Repeat3V1L(BaseTask):
    def __init__(self, world=None):
        super(Repeat3V1L, self).__init__(world=world, max_time=(64+((8*1)+8)*3))
        # NB: we use a formula for max_time, in the hope to remember
        # to adjust it from task to task: the only variable should
        # be the value equal to L

    @on_start()
    def give_instructions(self, event):
        self.target_string = return_random_string(3,1)
        self.set_message("repeat: " + self.target_string + ".")

    @on_message(r"\.")
    def check_response(self, event):
        if event.is_message(self.target_string, '.'):
            self.set_reward(1, random.choice(micro_congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def give_away_answer(self, event):
        self.fail_learner()

    def fail_learner(self):
        feedback = random.choice(micro_failed)
        feedback += self.target_string + '.'
        self.set_reward(0, feedback)


class Repeat3V2L(BaseTask):
    def __init__(self, world=None):
        super(Repeat3V2L, self).__init__(world=world, max_time=(64+((8*2)+8)*3))
        # NB: we use a formula for max_time, in the hope to remember
        # to adjust it from task to task: the only variable should
        # be the value equal to L

    @on_start()
    def give_instructions(self, event):
        self.target_string = return_random_string(3,2)
        self.set_message("repeat: " + self.target_string + ".")

    @on_message(r"\.")
    def check_response(self, event):
        if event.is_message(self.target_string, '.'):
            self.set_reward(1, random.choice(micro_congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def give_away_answer(self, event):
        self.fail_learner()

    def fail_learner(self):
        feedback = random.choice(micro_failed)
        feedback += self.target_string + '.'
        self.set_reward(0, feedback)

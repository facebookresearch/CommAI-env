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
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_init
#from worlds.grid_world import Point, Span
import random


class BeSilentTask(Task):
    def __init__(self, env):
        super(BeSilentTask, self).__init__(env=env,
                                           max_time=random.randint(100, 1000))

    @on_start()
    def on_start(self, event):
        self.set_message("be silent now")

    @on_sequence("1")
    def on_message(self, event):
        # if the learner produces non-space character, it receives reward 0 and
        # the task is over.
        self.set_reward(0, '')

    @on_timeout()
    def on_timeout(self, event):
        # if the learner has been silent, it receives reward +1 and the task is
        # over.
        self.set_reward(1, '')


class RepeatWhatISayTask(Task):
    def __init__(self, env):
        super(RepeatWhatISayTask, self).__init__(env=env, max_time=1000)
        self.verbs = ["say", "repeat"]
        self.words = ["apple", "banana", "cat", "hello world"]

    @on_start()
    def on_start(self, event):
        # sample a random verb
        cur_verb = random.choice(self.verbs)
        message = cur_verb + " "

        # sample a random word
        self.cur_word = random.choice(self.words)
        message += self.cur_word

        self.set_message(message)

    @on_message()
    def on_message(self, event):
        # on every character check if the suffix of the learner's message
        # equals to the teacher's word.
        if event.message[-len(self.cur_word):] == self.cur_word:
            self.set_reward(1, 'good job')

class RepeatWhatISay2Task(Task):
    def __init__(self, env):
        super(RepeatWhatISay2Task, self).__init__(env=env, max_time=1000)
        self.verbs = ["say", "repeat"]
        self.words = ["apple", "banana", "cat", "hello world"]
        self.context = ["and you will get a reward",
                        "and a reward is yours",
                        "and you will pass this task"]

    @on_start()
    def on_start(self, event):
        # sample a random verb
        cur_verb = random.choice(self.verbs)
        message = cur_verb + " "

        # sample a random word
        self.cur_word = random.choice(self.words)
        message += self.cur_word + " "

        # sample a random context
        context = random.choice(self.context)
        message += context

        self.set_message(message)

    @on_message()
    def on_message(self, event):
        # on every character check if the suffix of the learner's message
        # equals to the teacher's word.
        if event.message[-len(self.cur_word):] == self.cur_word:
            self.set_reward(1, 'correct')

class RepeatWhatISayMultipleTimesTask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesTask, self).__init__(env=env,
                                                              max_time=10000)
        self.verbs = ["say", "repeat"]
        self.words = ["apple", "banana", "cat", "hello world"]

    @on_start()
    def on_start(self, event):
        # sample a random verb
        cur_verb = random.choice(self.verbs)
        message = cur_verb + " "

        # sample a random word
        self.cur_word = random.choice(self.words)
        message += self.cur_word + " "

        # sample a random number
        self.n = random.randint(2, 3)
        message += str(self.n)
        message += " times"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ' '.join([self.cur_word] * self.n)
        if target in event.message:
            self.set_reward(1, '')
        else:
            self.set_reward(0, '')

class RepeatWhatISayMultipleTimes2Task(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimes2Task, self).__init__(env=env,
                                                               max_time=10000)
        self.verbs = ["say", "repeat"]
        self.words = ["apple", "banana", "cat", "hello world"]
        self.context = ["and you will get a reward",
                        "and a reward is yours",
                        "and you will pass this task"]

    @on_start()
    def on_start(self, event):
        # sample a random verb
        cur_verb = random.choice(self.verbs)
        message = cur_verb + " "

        # sample a random word
        self.cur_word = random.choice(self.words)
        message += self.cur_word + " "

        # sample a random number
        self.n = random.randint(2, 3)
        message += str(self.n)
        message += " times "

        # sample a random context
        context = random.choice(self.context)
        message += context

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ' '.join([self.cur_word] * self.n)
        if target in event.message:
            self.set_reward(1, '')
        else:
            self.set_reward(0, '')

class RepeatWhatISayMultipleTimesSeparatedByCommaTask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByCommaTask, self).__init__(
            env=env,
            max_time=10000)
        self.verbs = ["say", "repeat"]
        self.words = ["apple", "banana", "cat", "hello world"]

    @on_start()
    def on_start(self, event):
        # sample a random verb
        cur_verb = random.choice(self.verbs)
        message = cur_verb + " "

        # sample a random word
        self.cur_word = random.choice(self.words)
        message += self.cur_word + " "

        # sample a random number
        self.n = random.randint(2, 3)
        message += str(self.n)
        message += " times separated by comma"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ', '.join([self.cur_word] * self.n)
        if target in event.message:
            self.set_reward(1, '')
        else:
            self.set_reward(0, '')

class RepeatWhatISayMultipleTimesSeparatedByAndTask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByAndTask, self).__init__(
            env=env,
            max_time=10000)
        self.verbs = ["say", "repeat"]
        self.words = ["apple", "banana", "cat", "hello world"]

    @on_start()
    def on_start(self, event):
        # sample a random verb
        cur_verb = random.choice(self.verbs)
        message = cur_verb + " "

        # sample a random word
        self.cur_word = random.choice(self.words)
        message += self.cur_word + " "

        # sample a random number
        self.n = random.randint(2, 3)
        message += str(self.n)
        message += " times separated by and"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ' and '.join([self.cur_word] * self.n)
        if target in event.message:
            self.set_reward(1, '')
        else:
            self.set_reward(0, '')

class RepeatWhatISayMultipleTimesSeparatedByCATask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByCATask, self).__init__(
            env=env,
            max_time=10000)
        self.verbs = ["say", "repeat"]
        self.words = ["apple", "banana", "cat", "hello world"]

    @on_start()
    def on_start(self, event):
        # sample a random verb
        cur_verb = random.choice(self.verbs)
        message = cur_verb + " "

        # sample a random word
        self.cur_word = random.choice(self.words)
        message += self.cur_word + " "

        # sample a random number
        self.n = random.randint(2, 3)
        message += str(self.n)
        message += " times separated by comma and and"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ''
        if self.n == 2:
            target = self.cur_word + ' and ' + self.cur_word
        else:
            target = ', '.join([self.cur_word] * (self.n - 1))
            target += ', and ' + self.cur_word
        if target in event.message:
            self.set_reward(1, '')
        else:
            self.set_reward(0, '')

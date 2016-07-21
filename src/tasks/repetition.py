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
from tasks.base import BaseTask
import random
import tasks.messages as msg


verbs = ["say", "repeat"]
phrases = ["apple", "banana", "cat", "hello world"]
context = ["and you will get a reward",
           "and a reward is yours",
           "and you will pass this task",
           "and you will solve this problem"]


class BeSilentTask(Task):
    def __init__(self, env):
        super(BeSilentTask, self).__init__(env=env,
                                           max_time=random.randint(100, 1000))

    # give instructions at the beginning of the task
    @on_start()
    def on_start(self, event):
        self.set_message("be silent now.")

    # catch any bit 1 sent by the learner
    @on_sequence("1")
    def on_message(self, event):
        # if the learner produces bit 1, it receives reward 0 and the task is
        # over.
        self.set_reward(0, '')

    # when the maximum amount of time set for the task has elapsed
    @on_timeout()
    def on_timeout(self, event):
        # if the learner has been silent, it receives reward +1 and the task is
        # over.
        self.set_reward(1, random.choice(msg.congratulations))


class RepeatWhatISayTask(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISayTask, self).__init__(env=env, max_time=1000)

    @on_start()
    def on_start(self, event):
        # randomly sample a phrase
        self.cur_phrase = random.choice(phrases)
        # ask the learner to repeat a phrase randomly choosing the verb
        self.set_message(random.choice(verbs) + " " + self.cur_phrase + ".")

    # we wait for the learner to send a message finalized by a full stop.
    @on_message(r'\.$')
    def on_message(self, event):
        # if the message sent by the learner equals the teacher's selected
        # phrase followed by a period, reward the learner.
        # otherwise, it gets another chance while time allows.
        if event.is_message(self.cur_phrase, '.'):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def on_timeout(self, event):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, random.choice(msg.fail))


class RepeatWhatISay2Task(Task):
    def __init__(self, env):
        super(RepeatWhatISay2Task, self).__init__(env=env, max_time=1000)

    @on_start()
    def on_start(self, event):
        # sample a random phrase
        self.cur_phrase = random.choice(phrases)
        # ask the learner to repeat the phrase sampling one of the possible
        # ways of asking that, and putting some context after the target.
        self.set_message(random.choice(verbs) + " " + self.cur_phrase + " " +
                         random.choice(context) + ".")

    @on_message(r'\.$')
    def on_message(self, event):
        # on every character check if the suffix of the learner's message
        # equals to the teacher's phrase.
        if event.is_message(self.cur_phrase, '.'):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def on_timeout(self, event):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, random.choice(msg.fail))

repeat_min = 2
repeat_max = 3


class RepeatWhatISayMultipleTimesTask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesTask, self).__init__(env=env,
                                                              max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random verb
        message = random.choice(verbs) + " "

        # sample a random phrase
        self.cur_phrase = random.choice(phrases)
        message += self.cur_phrase + " "

        # sample a random number
        self.n = random.randint(repeat_min, repeat_max)
        message += str(self.n) + " times"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ' '.join([self.cur_phrase] * self.n)
        if target in event.message:
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            self.set_reward(0, '')

    @on_timeout()
    def on_timeout(self, event):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, random.choice(msg.fail))


class RepeatWhatISayMultipleTimes2Task(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimes2Task, self).__init__(env=env,
                                                               max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random verb
        message = random.choice(verbs) + " "

        # sample a random phrase
        self.cur_phrase = random.choice(phrases)
        message += self.cur_phrase + " "

        # sample a random number
        self.n = random.randint(repeat_min, repeat_max)
        message += str(self.n) + " times "

        # sample a random context
        message += random.choice(context)

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ' '.join([self.cur_phrase] * self.n)
        if target in event.message:
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            self.set_reward(0, '')

    @on_timeout()
    def on_timeout(self, event):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, random.choice(msg.fail))


class RepeatWhatISayMultipleTimesSeparatedByCommaTask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByCommaTask, self).__init__(
            env=env,
            max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random verb
        message = random.choice(verbs) + " "

        # sample a random phrase
        self.cur_phrase = random.choice(phrases)
        message += self.cur_phrase + " "

        # sample a random number
        self.n = random.randint(repeat_min, repeat_max)
        message += str(self.n) + " times separated by comma (,)"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ', '.join([self.cur_phrase] * self.n)
        if target in event.message:
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            self.set_reward(0, '')

    @on_timeout()
    def on_timeout(self, event):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, random.choice(msg.fail))


class RepeatWhatISayMultipleTimesSeparatedByAndTask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByAndTask, self).__init__(
            env=env,
            max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random verb
        message = random.choice(verbs) + " "

        # sample a random phrase
        self.cur_phrase = random.choice(phrases)
        message += self.cur_phrase + " "

        # sample a random number
        self.n = random.randint(repeat_min, repeat_max)
        message += str(self.n) + " times separated by and"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ' and '.join([self.cur_phrase] * self.n)
        if target in event.message:
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            self.set_reward(0, '')

    @on_timeout()
    def on_timeout(self, event):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, random.choice(msg.fail))


class RepeatWhatISayMultipleTimesSeparatedByCATask(Task):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByCATask, self).__init__(
            env=env,
            max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random verb
        message = random.choice(verbs) + " "

        # sample a random phrase
        self.cur_phrase = random.choice(phrases)
        message += self.cur_phrase + " "

        # sample a random number
        self.n = random.randint(repeat_min, repeat_max)
        message += str(self.n) + " times separated by comma and and"

        self.set_message(message)

    @on_message(r'\.$')
    def on_message(self, event):
        target = ''
        if self.n == 2:
            target = self.cur_phrase + ' and ' + self.cur_phrase
        else:
            target = ', '.join([self.cur_phrase] * (self.n - 1))
            target += ' and ' + self.cur_phrase
        if target in event.message:
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            self.set_reward(0, '')

    @on_timeout()
    def on_timeout(self, event):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, random.choice(msg.fail))

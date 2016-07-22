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
import tasks.messages as msg
import random
import string

# task-specific messages
verbs = ["say", "repeat"]
# FIXME: replace with association's objects and properties?
phrases = ["apple", "banana", "cat", "hello world"]
context = ["and you will get a reward",
           "and a reward is yours",
           "and you will pass this task",
           "and you will solve this problem"]
# repetition tasks configuration
repeat_min = 2
repeat_max = 3


class BeSilentTask(Task):
    def __init__(self, env):
        super(BeSilentTask, self).__init__(env=env,
                                           max_time=random.randint(100, 1000))

    # give instructions at the beginning of the task
    @on_start()
    def on_start(self, event):
        # initialize a variable to keep track if the learner has been failed
        self.flag_failed = False
        self.set_message(random.choice(["be silent now.",
                                        "do not say anything."]))

    # silence is encoded as all-zeros tokens
    # catch any bit 1 sent by the learner
    @on_sequence("1")
    def on_message(self, event):
        # if the learner produces bit 1, it receives reward 0 and the task is
        # over. We need to make sure to do this only once so for every
        # incoming 1 bit we don't start again sending the feedback message.
        if not self.flag_failed:
            self.set_reward(0, random.choice(msg.failed))
            # set the flag, so we don't
            self.flag_failed = True

    # when the maximum amount of time set for the task has elapsed
    @on_timeout()
    def on_timeout(self, event):
        # if the learner has been silent, it receives reward +1 and the task is
        # over.
        self.set_reward(1, random.choice(msg.congratulations))


class RepeatCharacterTask(BaseTask):
    def __init__(self, env):
        super(RepeatCharacterTask, self).__init__(env=env, max_time=1000)

    @on_start()
    def on_start(self, event):
        # randomly sample a character to be repeated
        self.cur_char = random.choice(string.letters)
        # ask the learner to repeat the phrase sampling one of the possible
        # ways of asking that.
        self.set_message("{query_verb} {phrase}."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_char))

    # we wait for the learner to send a message finalized by a full stop.
    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.cur_char, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.
        self.fail_learner()

    def fail_learner(self):
        # fail the learner sending a random fail feedback message
        self.set_reward(0, random.choice(msg.failed))


class RepeatWhatISayTask(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISayTask, self).__init__(env=env, max_time=1000)

    @on_start()
    def on_start(self, event):
        # randomly sample a phrase
        self.cur_phrase = random.choice(phrases)
        # ask the learner to repeat the phrase sampling one of the possible
        # ways of asking that.
        self.set_message("{query_verb} {phrase}."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_phrase))

    # we wait for the learner to send a message finalized by a full stop.
    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.cur_phrase, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.
        self.fail_learner()

    def fail_learner(self):
        # fail the learner sending a random fail feedback message
        self.set_reward(0, random.choice(msg.failed))


class RepeatWhatISay2Task(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISay2Task, self).__init__(env=env, max_time=1000)

    @on_start()
    def on_start(self, event):
        # sample a random phrase
        self.cur_phrase = random.choice(phrases)
        # ask the learner to repeat the phrase sampling one of the possible
        # ways of asking that, and putting some context after the target.
        self.set_message("{query_verb} {phrase} {context}."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_phrase,
                             context=random.choice(context)))

    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.cur_phrase, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.
        self.fail_learner()

    def fail_learner(self):
        # fail the learner sending a random fail feedback message
        self.set_reward(0, random.choice(msg.failed))


class RepeatWhatISayMultipleTimesTask(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesTask, self).__init__(env=env,
                                                              max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random phrase
        self.cur_phrase = random.choice(phrases)

        # sample the number of times it has to repeat the phrase
        # (can be expressed in letters or numbers)
        self.n = random.randint(repeat_min, repeat_max)

        # ask the learner to repeat the target phrase n times.
        self.set_message("{query_verb} {phrase} {times} times."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_phrase,
                             times=msg.number_to_string(self.n)
                         ))
        # save the correct answer
        self.target = ' '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.target, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase repeated n times followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.
        self.fail_learner()

    def fail_learner(self):
        # fail the learner teaching it the correct answer
        self.set_reward(0, "{negative_feedback} correct answer is: {answer}."
                        .format(
                            negative_feedback=random.choice(msg.failed),
                            answer=self.target
                        ))


class RepeatWhatISayMultipleTimes2Task(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimes2Task, self).__init__(env=env,
                                                               max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random phrase
        self.cur_phrase = random.choice(phrases)

        # sample the number of times it has to repeat the phrase
        # (can be expressed in letters or numbers)
        self.n = random.randint(repeat_min, repeat_max)

        self.set_message("{query_verb} {phrase} {times} times {context}."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_phrase,
                             times=msg.number_to_string(self.n),
                             context=random.choice(context)
                         ))
        # save the correct answer
        self.target = ' '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.target, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase repeated n times followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        self.fail_learner()

    def fail_learner(self):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, "{negative_feedback} correct answer is: {answer}."
                        .format(
                            negative_feedback=random.choice(msg.failed),
                            answer=self.target
                        ))


class RepeatWhatISayMultipleTimesSeparatedByCommaTask(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByCommaTask, self).__init__(
            env=env,
            max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random phrase
        self.cur_phrase = random.choice(phrases)

        # sample the number of times it has to repeat the phrase
        # (can be expressed in letters or numbers)
        self.n = random.randint(repeat_min, repeat_max)

        self.set_message("{query_verb} {phrase} {times} times separated "
                         "by comma (,)."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_phrase,
                             times=msg.number_to_string(self.n),
                             context=random.choice(context)
                         ))
        # save the correct answer
        self.target = ', '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.target, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase repeated n times followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        self.fail_learner()

    def fail_learner(self):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, "{negative_feedback} correct answer is: {answer}."
                        .format(
                            negative_feedback=random.choice(msg.failed),
                            answer=self.target
                        ))


class RepeatWhatISayMultipleTimesSeparatedByAndTask(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByAndTask, self).__init__(
            env=env,
            max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random phrase
        self.cur_phrase = random.choice(phrases)

        # sample the number of times it has to repeat the phrase
        # (can be expressed in letters or numbers)
        self.n = random.randint(repeat_min, repeat_max)

        self.set_message("{query_verb} {phrase} {times} times separated "
                         "by and."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_phrase,
                             times=msg.number_to_string(self.n),
                             context=random.choice(context)
                         ))
        # save the correct answer
        self.target = ' and '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.target, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase repeated n times followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        self.fail_learner()

    def fail_learner(self):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, "{negative_feedback} correct answer is: {answer}."
                        .format(
                            negative_feedback=random.choice(msg.failed),
                            answer=self.target
                        ))


class RepeatWhatISayMultipleTimesSeparatedByCATask(BaseTask):
    def __init__(self, env):
        super(RepeatWhatISayMultipleTimesSeparatedByCATask, self).__init__(
            env=env,
            max_time=10000)

    @on_start()
    def on_start(self, event):
        # sample a random phrase
        self.cur_phrase = random.choice(phrases)

        # sample the number of times it has to repeat the phrase
        # (can be expressed in letters or numbers)
        self.n = random.randint(repeat_min, repeat_max)

        self.set_message("{query_verb} {phrase} {times} times separated "
                         "by comma and and."
                         .format(
                             query_verb=random.choice(verbs),
                             phrase=self.cur_phrase,
                             times=msg.number_to_string(self.n),
                             context=random.choice(context)
                         ))
        # save the correct answer
        self.target = ' and '.join([", ".join([self.cur_phrase] * (self.n - 1)),
                                    self.cur_phrase])

    @on_message(r'\.$')
    def on_message(self, event):
        if event.is_message(self.target, '.'):
            # if the message sent by the learner equals the teacher's selected
            # phrase repeated n times followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        self.fail_learner()

    def fail_learner(self):
        # fail the learner if it hasn't repeated the message by the timeout
        self.set_reward(0, "{negative_feedback} correct answer is: {answer}."
                        .format(
                            negative_feedback=random.choice(msg.failed),
                            answer=self.target
                        ))

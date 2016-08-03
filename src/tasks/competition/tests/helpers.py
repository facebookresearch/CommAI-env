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
import core.environment as environment
import core.serializer as serializer
import core.channels as channels
import contextlib
import re


class EnvironmentMessenger:
    def __init__(self, env, serializer):
        self._env = env
        self._serializer = serializer
        self._input_channel = channels.InputChannel(serializer)
        self._output_channel = channels.OutputChannel(serializer)
        self.cum_reward = 0
        self.init()

    def init(self):
        '''Kick-starts the environment'''
        first_bit, reward = self._env.next(None)
        self._input_channel.consume_bit(first_bit)

    def is_silent(self):
        return self._env._output_channel.is_silent()

    def read(self):
        '''Sends silence until the teacher has stopped speaking'''
        nbits = 0
        while not self.is_silent():
            # Keep on putting silence in the output channel
            nbits += self.send(self._serializer.SILENCE_TOKEN)
        return nbits

    def read_until(self, condition):
        '''Sends silence until a given condition holds true.
        Args:
            condition: a function that takes an EnvironmentMessenger
        '''
        # wrap the condition to catch exceptions
        def safe_condition_eval():
            try:
                return condition(self)
            except BaseException:
                return False
        nbits = 0
        while not self.is_silent() and not safe_condition_eval():
            # Keep on putting silence in the output channel
            nbits += self.send(self._serializer.SILENCE_TOKEN)
        return nbits

    def send(self, msg=None):
        # default message is a silence
        if msg is None:
            msg = self._serializer.SILENCE_TOKEN
        nbits = 0
        # puts the message in the output channel
        self._output_channel.set_message(msg)
        # send every bit in it
        while not self._output_channel.is_empty():
            # send/receive a bit and reward
            env_bit, reward = self._env.next(self._output_channel.consume_bit())
            # save the bit
            self._input_channel.consume_bit(env_bit)
            # save the reward
            if reward is not None:
                self.cum_reward += reward
                # a reward marks the end of a task for now, so clear
                # the buffers
            nbits += 1
        return nbits

    def get_text(self):
        return self._input_channel.get_text()

    def get_last_message(self, n_silence=2):
        '''
        Returns the last message sent by the teacher. The message is delimited
        between the end of the input stream and the point after n_silence
        silent tokens where issued.
        '''
        # get the input text
        input_text = self._input_channel.get_text()
        # remove the trailing silences
        input_text = input_text.rstrip(self._serializer.SILENCE_TOKEN)
        # find the point where the last message started
        # (after at least n_silence tokens)
        last_silence = input_text.rfind(self._serializer.SILENCE_TOKEN *
                                        n_silence)
        if last_silence == -1:
            return input_text
        else:
            return input_text[last_silence + n_silence:]

    def search_last_message(self, pattern):
        message = self.get_last_message()
        match = re.search(pattern, message)
        if match is None:
            raise RuntimeError("'{0}' did not find any match on '{1}'".format(
                pattern, message
            ))
        return match.groups()

    def get_cumulative_reward(self):
        return self.cum_reward

    def get_time(self):
        return self._env._task_time


class SingleTaskScheduler():
    def __init__(self, task):
        self.task = task

    def get_next_task(self):
        return self.task

    def reward(self, reward):
        pass


@contextlib.contextmanager
def task_messenger(task_funct, world_funct=None):
    '''
    Returns an EnvironmentMessenger to interact with the created task.
    Args:
        task_func (functor): takes an environment (optionally a world) and
            returns a task object.
        world_func (functor): takes an environment and returns a world
            object.
    '''
    slzr = serializer.StandardSerializer()
    if world_funct:
        world = world_funct()
        task = task_funct(world)
    else:
        task = task_funct()
    scheduler = SingleTaskScheduler(task)
    env = environment.Environment(slzr, scheduler)
    m = EnvironmentMessenger(env, slzr)
    yield m

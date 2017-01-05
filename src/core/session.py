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
from core.obs.observer import Observable
from collections import defaultdict
import time

class Session:
    def __init__(self, environment, learner,
                 default_sleep=0.01):
        # internal initialization
        self._env = environment
        self._learner = learner
        self._default_sleep = default_sleep
        self._sleep = self._default_sleep
        # listen to changes in the currently running task
        self._env.task_updated.register(self.on_task_updated)
        # observable status
        self.env_token_updated = Observable()
        self.learner_token_updated = Observable()
        self.total_reward_updated = Observable()
        self.total_time_updated = Observable()
        # -- accounting --
        # total time
        self._total_time = 0
        # total cumulative reward
        self._total_reward = 0
        # keep track of how many times we have tried each task
        self._task_count = defaultdict(int)
        # keep track of how much time we have spent on each task
        self._task_time = defaultdict(int)

    def run(self):
        # initialize a token variable
        token = None
        # send out initial values of status variables
        self.total_time_updated(self._total_time)
        self.total_reward_updated(self._total_reward)
        # loop until stopped
        self._stop = False

        while not self._stop:
            # first speaks the environment one token (one bit)
            token, reward = self._env.next(token)
            self.env_token_updated(token)
            # reward the learner if it has been set
            self._learner.try_reward(reward)
            self.accumulate_reward(reward)

            # allow some time before processing the next iteration
            if self._sleep > 0:
                time.sleep(self._sleep)

            # then speaks the learner one token
            token = self._learner.next(token)
            self.learner_token_updated(token)

            # and we loop
            self._total_time += 1
            self._task_time[self._current_task.get_name()] += 1
            self.total_time_updated(self._total_time)

    def stop(self):
        self._stop = True

    def get_total_time(self):
        return self._total_time

    def get_total_reward(self):
        return self._total_reward

    def get_reward_per_task(self):
        return self._env.get_reward_per_task()

    def get_task_count(self):
        return self._task_count

    def get_task_time(self):
        return self._task_time

    def accumulate_reward(self, reward):
        '''Records the reward if the learner hasn't exceeded the maximum
        possible amount of reward allowed for the current task.'''
        if reward is not None:
            self._total_reward += reward
            if reward != 0:
                self.total_reward_updated(self._total_reward)

    def on_task_updated(self, task):
        self._current_task = task
        self._task_count[self._current_task.get_name()] += 1

    def set_sleep(self, sleep):
        if sleep < 0:
            sleep = 0
        self._sleep = sleep

    def get_sleep(self):
        return self._sleep

    def add_sleep(self, dsleep):
        self.set_sleep(self.get_sleep() + dsleep)

    def reset_sleep(self):
        self._sleep = self._default_sleep

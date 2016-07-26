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
from core.aux.observer import Observable
import time
import logging


class Session:
    def __init__(self, environment, learner, task_scheduler):
        self._env = environment
        self._learner = learner
        self._env.set_task_scheduler(task_scheduler)
        self.env_token_updated = Observable()
        self.learner_token_updated = Observable()
        self.total_reward_updated = Observable()
        self.total_time_updated = Observable()
        self._default_sleep = 0.01
        self._sleep = self._default_sleep
        self.logger = logging.getLogger(__name__)

    def run(self):
        token = None
        self._total_time = 0
        self._total_reward = 0
        self.total_time_updated(self._total_time)
        self.total_reward_updated(self._total_reward)
        while True:
            # first speaks the environment one token (one bit)
            token, reward = self._env.next(token)
            self.env_token_updated(token)
            # reward the learner if it has been set
            if reward is not None:
                self._learner.reward(reward)
                self._total_reward += reward
                self.total_reward_updated(self._total_reward)
            time.sleep(self._sleep)
            # then speaks the learner one token
            token = self._learner.next(token)
            self.learner_token_updated(token)
            # and we loop
            self._total_time += 1
            self.total_time_updated(self._total_time)

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


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
import core.task as task
import core.session as session
import core.serializer as serializer
import core.environment as environment
from core.obs.observer import Observable


class NullTask(task.Task):
    def __init__(self):
        super(NullTask, self).__init__(max_time=100)


class EnvironmentMock(object):
    def __init__(self):
        self.task_updated = Observable()

    def set_task(self, task):
        self.task = task

    def next(self, token):
        self.task_updated(self.task)
        # always return a reward of 1
        return token, 1

    def raise_event(self, event):
        pass

    def set_task_scheduler(self, ts):
        pass


class LearnerMock(object):
    def next(self, token):
        return token

    def try_reward(self, r):
        pass


class SingleTaskScheduler():
    def __init__(self, task):
        self.task = task

    def get_next_task(self):
        return self.task

    def reward(self, reward):
        pass


class TestSession(unittest.TestCase):

    def testLimitReward(self):
        env = environment.Environment(serializer.StandardSerializer(),
                                      SingleTaskScheduler(NullTask()))
        learner = LearnerMock()
        s = session.Session(env, learner)

        def on_time_updated(t):
            if t >= 20:
                s.stop()
        s.total_time_updated.register(on_time_updated)

        s.run()
        self.assertLessEqual(s._total_reward, 10)

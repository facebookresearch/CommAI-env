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
import random


class RandomTaskScheduler:
    '''
    A Scheduler provides new tasks every time is asked.
    This is a random scheduler
    '''
    def __init__(self, tasks):
        self.tasks = tasks

    def get_next_task(self):
        # pick a random task
        return random.choice(self.tasks)

    def reward(self):
        # whatever
        pass


class SequentialTaskScheduler:
    '''
    A Scheduler provides new tasks every time is asked.
    This is a random scheduler
    '''
    def __init__(self, tasks):
        self.tasks = tasks
        self.i = 0

    def get_next_task(self):
        # pick a random task
        ret = self.tasks[self.i]
        self.i = (self.i + 1) % len(self.tasks)
        return ret

    def reward(self):
        # whatever
        pass

class IncrementalTaskScheduler:
    '''
    Switches to the next task type sequentially
    After the current task was successfully learned N times
    '''

    def __init__(self, tasks, success_threshold=2):
        self.tasks = tasks
        self.task_ptr = 0
        self.reward_count = 0
        self.success_threshold = success_threshold

    def get_next_task(self):
        if self.reward_count == self.success_threshold:
            self.reward_count = 0
            self.task_ptr = (self.task_ptr + 1) % len(self.tasks)
        return self.tasks[self.task_ptr]

    def reward(self):
        self.reward_count += 1

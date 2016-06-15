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

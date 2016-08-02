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
import random

# This can be set to any collection of objects.
objects = ["apple", "banana", "pineapple", "pear"]


class ObjectExistence(Task):
    def __init__(self, env):
        super(ObjectExistence, self).__init__(env=env, max_time=3000)

    @on_start()
    def on_start(self, event):
        self.obj = random.choice(objects)
        self.obj_question = random.choice(objects)

        s = "Let's play game with objects. "
        s += "I have " + self.obj + ". "
        s += "Do I have " + self.obj_question + "?"
        self.set_message(s)

    @on_message("(yes|no).$")
    def on_message(self, event):
        if event.is_message("yes", '.'):
            if self.obj == self.obj_question:
                self.set_reward(1, "Correct!")
            else:
                s = "Wrong, I do not have " + self.obj_question + ". "
                s += "Do I have " + self.obj_question + "?"
                self.set_message(s)
            return

        if event.is_message("no", '.'):
            if self.obj != self.obj_question:
                self.set_reward(1, "Correct!")
            else:
                s = "Wrong, I do have " + self.obj_question + ". "
                s += "Do I have " + self.obj_question + "?"
                self.set_message(s)

    @on_timeout()
    def on_timeout(self, event):
        self.set_reward(0, "You are too slow! Let's try something else.")

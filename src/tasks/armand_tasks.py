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
    on_state_changed, on_timeout, on_output_message, on_init, on_ended
from tasks.competition.base import BaseTask
from worlds.grid_world import Point, Span
import random
import re

# global variables:
dirs = ['east', 'west', 'north', 'south']
objs = ['banana', 'apple', 'pineapple', 'cherry']

###############################################################################

# look in a predifined direction.
class LookTask(BaseTask):
    def __init__(self, env, world):
        super(LookTask, self).__init__(env=env, max_time=1000, world=world)

    @on_init()
    def on_init(self, event):
        self.dir = random.choice(dirs)
        dir = self.get_world().state.learner_direction
        self.set_message("Look to the " + self.dir + "," + " you are currently facing " + dir + ".")

    @on_message(r"I look\.$")
    def on_message(self, event):
        dir = self.get_world().state.learner_direction
        if dir == self.dir:
            self.set_reward(1, "Congratulations! You are looking in the right direction.")

###############################################################################

# the learner must look around his current position
class LookAround(Task):
    def __init__(self, env, world):
        super(LookAround, self).__init__(env=env, max_time=5000, world=world)

    @on_init()
    def on_init(self, event):
        self.visited_dirs = {'east': False, 'west': False,
                             'north': False, 'south': False}
        self.ndir = 0
        dir = self.get_world().state.learner_direction
        self.set_message("Look around. You are facing "+ dir + ".")
        self.state.learner_pos = self.get_world().state.learner_pos

    @on_state_changed(lambda ws, ts: ws.learner_pos != ts.learner_pos)
    def on_moved(self, event):
        self.set_reward(0, "You are not allowed to move.")

    @on_message(r"I look\.$")
    def on_message(self, event):
        dir = self.get_world().state.learner_direction
        if dir in self.visited_dirs and not self.visited_dirs[dir]:
            self.visited_dirs[dir] = True
            self.ndir += 1
            ddir = len(self.visited_dirs) - self.ndir
            if ddir == 0:
                self.set_reward(1, "Congratulations!")
            else:
                self.set_message( str(ddir) + " directions to go.")
        elif dir in self.visited_dirs:
            self.set_message("You already look here.")


###############################################################################

# Set 4 objects around the learner, ask to find one of them.
class FindObjectAround(Task):
    def __init__(self, env, world):
        super(FindObjectAround, self).__init__(env=env, max_time=10000,
                                               world=world)
        self.dir2obj = [0,1,2,3]
        random.shuffle(self.dir2obj)

    @on_init()
    def on_init(self, event):
        # random assignment of object to location
        self.state.learner_pos = self.get_world().state.learner_pos
        pos = self.state.learner_pos
        pe = self.get_world().put_entity
        for i in range(0, len(dirs)):
            np = pos + self.get_world().valid_directions[dirs[i]]
            pe(np, objs[self.dir2obj[i]], True, True)
        self.dir = random.choice(self.dir2obj)
        self.obj = objs[self.dir2obj[self.dir]]
        self.instructions_completed = False
        self.set_message("Pick the " + self.obj + " next to you.")
        obj_count = self.get_world().state.learner_inventory[self.obj]
        self.add_handler(
            on_state_changed(lambda ws, ts: ws.learner_inventory[self.obj] == obj_count + 1)(self.on_object_picked.im_func)
        )

    @on_ended()
    def on_ended(self, event):
        pos = self.state.learner_pos
        for i in range(0, len(dirs)):
            np = pos + self.get_world().valid_directions[dirs[i]]
            self.get_world().remove_entity(np)

    def on_object_picked(self, event):
        self.set_reward(1, 'Well done!')


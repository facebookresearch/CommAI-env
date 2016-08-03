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
from worlds.grid_world import GridWorld
from tasks.sample.sample_tasks import PickAnApple, MovingTask
from core.scheduler import RandomTaskScheduler


def create_tasks():
    # a world for some tasks
    grid_world = GridWorld()
    # we get today's task menu
    return RandomTaskScheduler([PickAnApple(grid_world),
                                MovingTask(grid_world)])

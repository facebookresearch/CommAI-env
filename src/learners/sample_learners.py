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


class SampleRepeatingLearner:
    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        # do super fancy computations
        # return our guess
        return input


class SampleSilentLearner:
    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        return 0


class SampleMemorizingLearner:
    def __init__(self):
        self.memory = []
        self.teacher_stopped_talking = False

    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        # Now this robotic teacher is going to mumble things again
        self.teacher_stopped_talking = False
        self.memory = []

    def next(self, input):
        # If we have received a silence byte
        if len(self.memory) > 0 and len(self.memory) % 8 == 0 and \
                all(map(lambda x: x == '0', self.memory[-8:])):
            self.teacher_stopped_talking = True

        if self.teacher_stopped_talking:
            # send the memorized sequence
            output, self.memory = self.memory[0], self.memory[1:]
        else:
            output = '0'
        # memorize what the teacher said
        self.memory.append(input)
        return output

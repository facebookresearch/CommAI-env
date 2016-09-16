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
from core.serializer import StandardSerializer, IdentitySerializer
from learners.base import BaseLearner


class SampleRepeatingLearner(BaseLearner):
    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        # do super fancy computations
        # return our guess
        return input


class SampleSilentLearner(BaseLearner):
    def __init__(self):
        self.serializer = StandardSerializer()
        self.silence_code = self.serializer.to_binary(' ')
        self.silence_i = 0

    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        self.silence_i = 0

    def next(self, input):
        output = self.silence_code[self.silence_i]
        self.silence_i = (self.silence_i + 1) % len(self.silence_code)
        return output


class SampleMemorizingLearner(BaseLearner):
    def __init__(self):
        self.memory = ''
        self.teacher_stopped_talking = False
        # the learner has the serialization hardcoded to
        # detect spaces
        self.serializer = StandardSerializer()
        self.silence_code = self.serializer.to_binary(' ')
        self.silence_i = 0

    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        # Now this robotic teacher is going to mumble things again
        self.teacher_stopped_talking = False
        self.silence_i = 0
        self.memory = ''

    def next(self, input):
        # If we have received a silence byte
        text_input = self.serializer.to_text(self.memory)
        if text_input and text_input[-2:] == '  ':
            self.teacher_stopped_talking = True

        if self.teacher_stopped_talking:
            # send the memorized sequence
            output, self.memory = self.memory[0], self.memory[1:]
        else:
            output = self.silence_code[self.silence_i]
            self.silence_i = (self.silence_i + 1) % len(self.silence_code)
        # memorize what the teacher said
        self.memory += input
        return output

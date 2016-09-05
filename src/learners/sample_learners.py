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
    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        return 0


class SampleMemorizingLearner(BaseLearner):
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


class SampleRandomWordsLearner(BaseLearner):
    def __init__(self, min_length=2, max_length=3):
        # recording the last word
        self.memory = []
        # responses are queued here
        self.output_buf = []
        # recording unique words used by teacher
        self.words = []
        self.teacher_stopped_talking = False
        self.serializer = StandardSerializer()

        # response construction configs
        self.min_length = min_length
        self.max_length = max_length

    def reward(self, reward):
        self.teacher_stopped_talking = False
        # also cleaning the phrases queue
        self.output_buf = []

    def build_random_phrase(self):
        size = random.randint(self.min_length, self.max_length)
        N = len(self.words)
        resp = ''
        for _ in range(size):
            resp += self.words[random.randint(0, N - 1)] + ' '
        return self.serializer.to_binary(resp)

    def next(self, input):
        self.teacher_stopped_talking = False
        # checking for silence byte
        if len(self.memory) > 0 and len(self.memory) % 8 == 0 and \
                all(map(lambda x: x == '0', self.memory[-8:])):
            self.teacher_stopped_talking = True

        if self.teacher_stopped_talking:
            # Learning new words and filtering out the case when the word is
            # empty (because the teacher is silent)
            binary_text = ''.join(self.memory[:-8])
            word = self.serializer.to_text(binary_text)
            if word is not None:
                word = str(word)
                if word not in self.words:
                    self.words.append(word)
            phrase_bin = self.build_random_phrase()
            self.output_buf.extend(phrase_bin)
            self.memory = []
        self.memory.append(input)
        if len(self.output_buf) > 0:
            output, self.output_buf = self.output_buf[0], self.output_buf[1:]
        else:
            output = '0'
        return output


class RandomCharacterLearner(BaseLearner):

    # just for testing the char-level environment
    def __init__(self, logging_path=None):
        self.alphabet = [chr(ord('a') + x) for x in range(26)] + [chr(ord('A') + x) for x in range(26)] + [chr(ord('0') + x) for x in range(10)] + ['.', '\'', '\"', ',', ' ']
        self.log_file = open(logging_path) if logging_path is not None else None
        self.serializer = IdentitySerializer()

    def reward(self, reward):
        pass

    def next(self, input):
        output = random.randint(0, len(self.alphabet) - 1)
        output = self.alphabet[output]
        if self.log_file is not None:
            self.log_file.write('{} -> {}'.format(input, output))
        return output

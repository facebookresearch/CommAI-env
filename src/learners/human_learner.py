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
from core.channels import InputChannel, OutputChannel
from learners.base import BaseLearner
import logging
import re


class HumanLearner(BaseLearner):
    def __init__(self, serializer):
        '''
        Takes the serialization protocol
        '''
        self._serializer = serializer
        self._input_channel = InputChannel(serializer)
        self._output_channel = OutputChannel(serializer)
        self._input_channel.message_updated.register(self.on_message)
        self.logger = logging.getLogger(__name__)
        self.speaking = False

    def set_view(self, view):
        '''
        Sets the user interface to get the user input
        '''
        self._view = view

    def reward(self, reward):
        self.logger.info("Reward received: {0}".format(reward))
        self._input_channel.clear()
        self._output_channel.clear()

    def next(self, input):
        # If the buffer is empty, fill it with silence
        if self._output_channel.is_empty():
            self.logger.debug("Output buffer is empty, filling with silence")
            # Add one silence token to the buffer
            self._output_channel.set_message(self._serializer.SILENCE_TOKEN)

        # Get the bit to return
        output = self._output_channel.consume_bit()
        # Interpret the bit from the learner
        self._input_channel.consume_bit(input)
        return output

    def on_message(self, message):
        # we ask for input on two consecutive silences
        if message[-2:] == self._serializer.SILENCE_TOKEN * 2 and \
                self._output_channel.is_empty() and not self.speaking:
            self.ask_for_input()
        elif self._output_channel.is_empty():
            # If we were speaking, we are not speaking anymore
            self.speaking = False

    def ask_for_input(self):
        output = self._view.get_input()
        self.logger.debug("Received input from the human: '{0}'".format(output))
        if output:
            self.speaking = True
            output = re.compile('\.+').sub('.', output)
            self._output_channel.set_message(output)


class ManualHumanLearner(HumanLearner):
    def __init__(self, serializer):
        super(ManualHumanLearner, self).__init__(serializer)

    def next(self, input):
        # If the buffer is empty, ask for what to do
        while self._output_channel.is_empty():
            self.ask_for_input()
        return super(ManualHumanLearner, self).next(input)

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
from core.obs.observer import Observable
import logging


class InputChannel:

    def __init__(self, serializer):
        self.serializer = serializer
        # remembers the input in binary format
        self._binary_buffer = ''
        # leftmost deserialization of the binary buffer
        self._deserialized_buffer = ''
        # remember the position until which we deserialized the binary buffer
        self._deserialized_pos = 0

        # event that gets fired for every new bit
        self.sequence_updated = Observable()
        # event that gets fired for every new character
        self.message_updated = Observable()

    def consume_bit(self, input_bit):
        '''
        Takes a bit into the channel
        '''
        # for now we are storing the input as strings (let's change this later)
        if input_bit == 0 or input_bit == 1:
            input_bit = str(input_bit)
        # store the bit in the binary input buffer
        self._binary_buffer += input_bit
        # notify the updated sequence
        self.sequence_updated(self._binary_buffer)

        # we check if we can deserialize the final part of the sequence
        undeserialized_part = self.get_undeserialized()
        if self.serializer.can_deserialize(undeserialized_part):
            # when we do, we deserialize the chunk
            self._deserialized_buffer += \
                self.serializer.to_text(undeserialized_part)
            # we update the position
            self._deserialized_pos += len(undeserialized_part)

            self.message_updated(self._deserialized_buffer)

    def clear(self):
        '''Clears all the  buffers'''
        self._set_deserialized_buffer('')
        self._set_binary_buffer('')
        self._deserialized_pos = 0

    def get_binary(self):
        return self._binary_buffer

    def set_deserialized_buffer(self, new_buffer):
        '''
        Replaces the deserialized part of the buffer.
        '''
        self._deserialized_buffer = new_buffer

    def get_undeserialized(self):
        '''
        Returns the yet non deserialized chunk in the input
        '''
        return self._binary_buffer[self._deserialized_pos:]

    def get_text(self):
        return self._deserialized_buffer

    def _set_binary_buffer(self, new_buffer):
        '''
        Carefully raise the event only if the buffer has actually changed
        '''
        if self._binary_buffer != new_buffer:
            self._binary_buffer = new_buffer
            self.sequence_updated(self._binary_buffer)

    def _set_deserialized_buffer(self, new_buffer):
        '''
        Carefully raise the event only if the buffer has actually changed
        '''
        if self._deserialized_buffer != new_buffer:
            self._deserialized_buffer = new_buffer
            self.message_updated(self._deserialized_buffer)


class OutputChannel:

    def __init__(self, serializer):
        self.serializer = serializer
        # remembers the data that has to be shipped out
        self._binary_buffer = ''
        # event that gets fired every time we change the output sequence
        self.sequence_updated = Observable()
        self.logger = logging.getLogger(__name__)

    def set_message(self, message):
        new_binary = self.serializer.to_binary(message)
        # find the first available point from where we can insert
        # the new buffer without breaking the encoding
        insert_point = len(self._binary_buffer)
        for i in range(len(self._binary_buffer)):
            # if we can decode from insert_point on, we can replace
            # that information with the new buffer
            if self.serializer.to_text(self._binary_buffer[i:]):
                insert_point = i
                break
        if insert_point > 0:
            self.logger.debug("Inserting new contents at {0}".format(
                insert_point))
        self._set_buffer(self._binary_buffer[:insert_point] + new_binary)

    def clear(self):
        self._set_buffer('')

    def _set_buffer(self, new_buffer):
        '''
        Carefully raise the event only if the buffer has actually changed
        '''
        if self._binary_buffer != new_buffer:
            self._binary_buffer = new_buffer
            self.sequence_updated(self._binary_buffer)

    def consume_bit(self):
        if len(self._binary_buffer) > 0:
            output, new_buffer = self._binary_buffer[0], \
                self._binary_buffer[1:]
            self._set_buffer(new_buffer)
            return output

    def is_empty(self):
        return len(self._binary_buffer) == 0

    def is_silent(self):
        ''' All the bits in the output token are the result of serializing
        silence tokens'''
        buf = self._binary_buffer
        silent_bits = self.serializer.to_binary(self.serializer.SILENCE_TOKEN)
        token_size = len(silent_bits)
        while len(buf) > token_size:
            buf_suffix, buf = buf[-token_size:], buf[:-token_size]
            if buf_suffix != silent_bits:
                return False
        return len(buf) == 0 or buf == silent_bits[-len(buf):]

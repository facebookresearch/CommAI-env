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
from core.aux.observer import Observable


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
        self._set_deserialized_buffer('')
        self._set_binary_buffer('')
        self._deserialized_pos = 0

    def get_binary(self):
        return self._binary_buffer

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
            self.sequence_updated(self._deserialized_buffer)


class OutputChannel:

    def __init__(self, serializer):
        self.serializer = serializer
        # remembers the data that has to be shipped out
        self._binary_buffer = ''
        # event that gets fired every time we change the output sequence
        self.sequence_updated = Observable()

    def set_message(self, message):
        new_binary = self.serializer.to_binary(message)
        self._set_buffer(new_binary)

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

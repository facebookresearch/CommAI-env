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
import logging


class StandardSerializer:
    def __init__(self):
        self.SILENCE_TOKEN = ' '
        self.SILENCE_BITS = '00000000'
        self.logger = logging.getLogger(__name__)

    def to_binary(self, message):
        data = []
        for c in message:
            # convert to binary
            bin_c = bin(ord(c))
            # remove the '0b' prefix
            bin_c = bin_c[2:]
            # pad with zeros
            bin_c = bin_c.zfill(8)
            data.append(bin_c)
        return ''.join(data)

    def to_text(self, data):
        # special silence case
        if data == self.SILENCE_BITS:
            return self.SILENCE_TOKEN
        message = ''
        assert self.can_deserialize(data)
        for i in range(int(len(data) / 8)):
            b = data[i * 8:(i + 1) * 8]
            try:
                message += chr(int(b, 2))
            except UnicodeDecodeError:
                self.logger.error('Couldn\'t deserialize byte "{0}"'.format(b))
        return message

    def can_deserialize(self, data):
        return len(data) % 8 == 0

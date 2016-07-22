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
import codecs


class StandardSerializer:
    def __init__(self):
        self.SILENCE_TOKEN = ' '
        self.SILENCE_ENCODING = '\0'
        self.logger = logging.getLogger(__name__)

    def to_binary(self, message):
        # All spaces are encoded as null bytes:
        message = message.replace(self.SILENCE_TOKEN, self.SILENCE_ENCODING)
        # handle unicode
        message = codecs.encode(message, 'utf-8')
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

    def to_text(self, data, strict=False):
        # if we are not in strict mode, we can skip bytes to find a message
        for skip in range(int(len(data) / 8) if not strict else 1):
            try:
                message = str('')
                sub_data = data[skip * 8:]
                for i in range(int(len(sub_data) / 8)):
                    b = sub_data[i * 8:(i + 1) * 8]
                    message += chr(int(b, 2))
                message = codecs.decode(message, 'utf-8')
                message = message.replace(self.SILENCE_ENCODING,
                                          self.SILENCE_TOKEN)
                if skip > 0:
                    self.logger.warn("Skipping {0} bytes to find a valid "
                                     "unicode character".format(skip))

                return message
            except UnicodeDecodeError:
                pass

        return None

    def can_deserialize(self, data):
        if len(data) < 8:
            return False
        return self.to_text(data) is not None

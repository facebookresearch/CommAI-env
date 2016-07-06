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
import unittest
import core.serializer as serializer


class TestSerializer(unittest.TestCase):

    def testConsistency(self):
        slzr = serializer.StandardSerializer()
        self.assertEqual('a', slzr.to_text(slzr.to_binary('a')))
        self.assertEqual(' ', slzr.to_text(slzr.to_binary(' ')))

        # greek letter \alpha (not working in current ascii serialization)
        # self.assertEqual(u"\u03B1", slzr.to_text(slzr.to_binary(u"\u03B1")))


def main():
    unittest.main()

if __name__ == '__main__':
    main()

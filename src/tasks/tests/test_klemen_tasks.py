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
import tasks.klemen_tasks as klemen_tasks
from tasks.tests.helpers import task_messenger


class TestKlemenTasks(unittest.TestCase):

    def testBeSilent(self):
        with task_messenger(klemen_tasks.BeSilentTask) as m:
            # read the instructions
            m.read()
            instructions = m.get_last_message()
            # there are some instructions
            self.assertGreater(len(instructions), 0)
            # stay silent until rewarded
            while m.get_cumulative_reward() == 0:
                m.send()
            # read the instructions again
            m.read()
            instructions = m.get_last_message()
            # there are some instructions
            self.assertGreater(len(instructions), 0)
            # we fail
            m.send('a')
            # we should have prompted a restart
            m.read()
            instructions = m.get_last_message()
            # there are some instructions
            self.assertGreater(len(instructions), 0)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

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
import tasks.marco_tasks as marco_tasks
import re
from tasks.tests.helpers import task_messenger


class TestMarcoTasks(unittest.TestCase):

    def testAssociateObjectWithProperty(self):
        with task_messenger(marco_tasks.AssociateObjectWithPropertyTask) as m:
            # read the instructions
            m.read()
            instructions = m.get_last_message()
            # find the answer
            property_ = re.search(r"basket is (\w+)", instructions).group(1)
            # send the answer with the termination marker
            m.send("{0}.".format(property_))
            # hear the congratulations
            m.read()
            feedback = m.get_last_message()
            # there is some feedback
            self.assertGreater(len(feedback), 0)
            m.send()
            self.assertEqual(m.get_cumulative_reward(), 1)

    def testAssociateObjectWithPropertyTimeout(self):
        with task_messenger(marco_tasks.AssociateObjectWithPropertyTask) as m:
            # read the instructions
            m.read()
            instructions = m.get_last_message()
            # find the answer
            property_ = re.search(r"basket is (\w+)", instructions).group(1)
            # stay silent
            while m.is_silent():
                m.send()
            # hear the feedback
            m.read()
            feedback = m.get_last_message()
            answer = re.search(r"the right answer is: (\w+)", feedback).group(1)
            m.send()
            self.assertEqual(property_, answer)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

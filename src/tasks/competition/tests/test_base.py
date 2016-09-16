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
import tasks.competition.base as base
from core.task import on_start, on_message
from tasks.competition.tests.helpers import task_messenger


class TestBase(unittest.TestCase):

    def testIgnoreInterruptions(self):
        class TestTask(base.BaseTask):
            def __init__(self, max_time=1000):
                super(TestTask, self).__init__(max_time=max_time)

            @on_start()
            def on_start(self, event):
                self.interrupted = False
                self.set_message("Saying.")

            @on_message(r"Interrupt.$")
            def on_interrupt(self, event):
                self.set_message("Interrupted.")

            @on_message(r"Respectful.$")
            def on_respect(self, event):
                self.set_message("Good.")

        with task_messenger(TestTask) as m:
            # test for not solving it at all
            message = "Interrupt."
            m.send(message)
            blen = m.read()
            self.assertEqual(blen, 0)
            self.assertFalse(m.get_last_message() == "Interrupted.")
            m.send("Respectful.")
            blen = m.read()
            self.assertGreater(blen, 0)
            self.assertEqual(m.get_last_message(), 'Good.')

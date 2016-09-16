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
import core.events as events


class MyEvent(object):
    pass


class TestEvents(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestEvents, self).__init__(*args, **kwargs)

    def testEvents(self):
        self.event_raised = False

        def on_start(self, event):
            self.event_raised = True

        em = events.EventManager()
        em.register(self,
                    events.Trigger(MyEvent, lambda e: True, on_start))
        em.raise_event(MyEvent())
        self.assertTrue(self.event_raised)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

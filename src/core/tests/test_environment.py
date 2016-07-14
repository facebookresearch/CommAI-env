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
import core.task as task
import core.environment as environment


class SerializerMock(object):
    pass


class TestEnvironment(unittest.TestCase):

    def testRegistering(self):
        class TestTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(TestTask, self).__init__(*args, **kwargs)
                self.handled = False

            @task.on_init()
            def init_handler(self, event):
                self.handled = True
        env = environment.Environment(SerializerMock())
        tt = TestTask(env, max_time=10)

        env._register_task_triggers(tt)
        # Start cannot be handled
        self.failIf(env.raise_event(task.Start()))
        # Init should be handled
        self.failUnless(env.raise_event(task.Init()))
        # The init handler should have been executed
        self.failUnless(tt.handled)
        env._deregister_task_triggers(tt)
        # Init should not be handled anymore
        self.failIf(env.raise_event(task.Init()))

    def testDynRegistering(self):
        class TestTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(TestTask, self).__init__(*args, **kwargs)
                self.init_handled = False
                self.start_handled = False

            @task.on_init()
            def init_handler(self, event):
                self.dyn_add_handler(task.on_start()(
                    self.start_handler.im_func))
                self.init_handled = True

            def start_handler(self, event):
                self.start_handled = True

        env = environment.Environment(SerializerMock())
        tt = TestTask(env, max_time=10)

        env._register_task_triggers(tt)
        # Start cannot be handled
        self.failIf(env.raise_event(task.Start()))
        self.failIf(tt.start_handled)
        # Init should be handled
        self.failUnless(env.raise_event(task.Init()))
        # The init handler should have been executed
        self.failUnless(tt.init_handled)
        # Now the Start should be handled
        self.failUnless(env.raise_event(task.Start()))
        self.failUnless(tt.start_handled)
        env._deregister_task_triggers(tt)
        # Init should not be handled anymore
        self.failIf(env.raise_event(task.Init()))
        tt.start_handled = False
        # Start should not be handled anymore
        self.failIf(env.raise_event(task.Start()))
        self.failIf(tt.start_handled)
        # Register them again! mwahaha (evil laugh)
        env._register_task_triggers(tt)
        # Start should not be handled anymore
        self.failIf(env.raise_event(task.Start()))
        self.failIf(tt.start_handled)
        # Deregister them again! mwahahahaha (more evil laugh)
        env._deregister_task_triggers(tt)
        self.failIf(env.raise_event(task.Start()))
        self.failIf(tt.start_handled)

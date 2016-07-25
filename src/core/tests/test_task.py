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


class EnvironmentMock():
    def raise_event(self, event):
        pass


class TestEvents(unittest.TestCase):

    def testTriggers(self):
        class TestTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(TestTask, self).__init__(*args, **kwargs)

            @task.on_init()
            def init_handler(self, event):
                pass

            @task.on_start()
            def start_handler(self, event):
                pass

            @task.on_message()
            def message_handler(self, event):
                pass

            @task.on_timeout()
            def timeout_handler(self, event):
                pass

            @task.on_ended()
            def ended_handler(self, event):
                pass

        env = EnvironmentMock()
        tt = TestTask(env, max_time=10)
        triggers = tt.get_triggers()
        handlers = map(lambda t: t.event_handler, triggers)
        self.assertEqual(5, len(triggers))
        self.failUnless(TestTask.init_handler.im_func in handlers)
        self.failUnless(TestTask.start_handler.im_func in handlers)
        self.failUnless(TestTask.message_handler.im_func in handlers)
        self.failUnless(TestTask.timeout_handler.im_func in handlers)
        self.failUnless(TestTask.ended_handler.im_func in handlers)
        types = {t.event_handler: t.type for t in triggers}
        self.assertEqual(task.Init, types[TestTask.init_handler.im_func])
        self.assertEqual(task.Start, types[TestTask.start_handler.im_func])
        self.assertEqual(task.MessageReceived,
                         types[TestTask.message_handler.im_func])
        self.assertEqual(task.Timeout,
                         types[TestTask.timeout_handler.im_func])
        self.assertEqual(task.Ended, types[TestTask.ended_handler.im_func])

    def testInheritance(self):
        class BaseTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(BaseTask, self).__init__(*args, **kwargs)

            @task.on_init()
            def init_handler(self, event):
                pass

            @task.on_start()
            def start_handler(self, event):
                pass

        class ConcreteTask(BaseTask):
            def __init__(self, *args, **kwargs):
                super(ConcreteTask, self).__init__(*args, **kwargs)

            # overridden handler
            @task.on_start()
            def start_handler(self, event):
                pass

        env = EnvironmentMock()
        tt = ConcreteTask(env, max_time=10)
        triggers = tt.get_triggers()
        handlers = map(lambda t: t.event_handler, triggers)
        self.assertEqual(2, len(triggers))
        self.failUnless(BaseTask.init_handler.im_func in handlers)
        # The start_handler must be the one of the overridden task
        self.failUnless(ConcreteTask.start_handler.im_func in handlers)
        self.failIf(BaseTask.start_handler.im_func in handlers)

    def testDynamicHandlers(self):
        class TestTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(TestTask, self).__init__(*args, **kwargs)

            @task.on_init()
            def init_handler(self, event):
                def start_handler(self, event):
                    pass
                self.start_handler_func = start_handler
                self.add_handler(task.on_start()(start_handler))

        class EnvironmentMock():
            def __init__(self, triggers):
                self.triggers = triggers

            def raise_event(self, event):
                pass

            def _register_task_trigger(self, task, trigger):
                self.triggers.append(trigger)

        triggers = []
        env = EnvironmentMock(triggers)
        tt = TestTask(env, max_time=10)
        # raise the init event
        tt.init_handler(task.Init())
        triggers.extend(tt.get_triggers())
        handlers = map(lambda t: t.event_handler, triggers)
        self.assertEqual(2, len(triggers))
        self.failUnless(TestTask.init_handler.im_func in handlers)
        self.failUnless(tt.start_handler_func in handlers)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

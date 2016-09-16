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


class TestEvents(unittest.TestCase):

    def testTriggers(self):
        class TestTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(TestTask, self).__init__(*args, **kwargs)

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

        tt = TestTask(max_time=10)
        triggers = tt.get_triggers()
        handlers = set(map(lambda t: t.event_handler, triggers))
        self.assertEqual(4, len(triggers))
        self.assertIn(self.get_func(TestTask.start_handler), handlers)
        self.assertIn(self.get_func(TestTask.message_handler), handlers)
        self.assertIn(self.get_func(TestTask.timeout_handler), handlers)
        self.assertIn(self.get_func(TestTask.ended_handler), handlers)
        types = dict((t.event_handler, t.type) for t in triggers)
        self.assertEqual(task.Start, types[self.get_func(TestTask.start_handler)])
        self.assertEqual(task.MessageReceived,
                         types[self.get_func(TestTask.message_handler)])
        self.assertEqual(task.Timeout,
                         types[self.get_func(TestTask.timeout_handler)])
        self.assertEqual(task.Ended, types[self.get_func(TestTask.ended_handler)])

    def testInheritance(self):
        class BaseTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(BaseTask, self).__init__(*args, **kwargs)

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

        tt = ConcreteTask(max_time=10)
        triggers = tt.get_triggers()
        handlers = set(map(lambda t: t.event_handler, triggers))
        self.assertEqual(1, len(triggers))
        # The start_handler must be the one of the overridden task
        self.assertIn(self.get_func(ConcreteTask.start_handler), handlers)
        self.assertFalse(self.get_func(BaseTask.start_handler) in handlers)

    def testDynamicHandlers(self):
        class TestTask(task.Task):
            def __init__(self, *args, **kwargs):
                super(TestTask, self).__init__(*args, **kwargs)

            @task.on_start()
            def start_handler(self, event):
                def end_handler(self, event):
                    pass
                self.end_handler_func = end_handler
                self.add_handler(task.on_ended()(end_handler))

        triggers = []
        tt = TestTask(max_time=10)

        class EnvironmentMock():
            def __init__(self, triggers):
                self.triggers = triggers

            def raise_event(self, event):
                # we only generate an init event
                tt.start_handler(event)

            def _register_task_trigger(self, task, trigger):
                self.triggers.append(trigger)

        # raise the start event
        tt.start(EnvironmentMock(triggers))
        triggers.extend(tt.get_triggers())
        handlers = set(map(lambda t: t.event_handler, triggers))
        self.assertEqual(2, len(triggers))
        self.assertIn(self.get_func(TestTask.start_handler), handlers)
        self.assertIn(self.get_func(tt.end_handler_func), handlers)

    def get_func(self, method):
        try:
            return method.im_func
        except AttributeError: # Python 3
            try:
                return method.__func__
            except AttributeError: # Python 3 (unbound method == func)
                return method


def main():
    unittest.main()

if __name__ == '__main__':
    main()

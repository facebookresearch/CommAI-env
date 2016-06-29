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
from core.events import EventManager, StateChanged, MessageReceived, \
    SequenceReceived, OutputSequenceUpdated, OutputMessageUpdated
from core.aux.observer import Observable
from core.channels import InputChannel, OutputChannel
import logging
SILENCE = '0'


class Environment:
    '''
    The Environment, you know.
    '''
    def __init__(self, serializer):
        self.event_manager = EventManager()
        self._current_task = None
        self._current_world = None
        # input channel
        self._input_channel = InputChannel(serializer)
        # output channel
        self._output_channel = OutputChannel(serializer)
        # we hear to our own output
        self._output_channel_listener = InputChannel(serializer)
        # priority of ongoing message
        self._output_priority = 0
        # reward that is to be given at the learner at the end of the task
        self._reward = None
        # Current task time
        self._task_time = None
        self.logger = logging.getLogger(__name__)

        # signals
        self.world_updated = Observable()
        self.task_updated = Observable()

        # Register channel observers
        self._input_channel.sequence_updated.register(
            self.on_input_sequence_updated)
        self._input_channel.message_updated.register(
            self.on_input_message_updated)
        self._output_channel_listener.sequence_updated.register(
            self.on_output_sequence_updated)
        self._output_channel_listener.message_updated.register(
            self.on_output_message_updated)

    def set_task_scheduler(self, task_scheduler):
        ''' A task scheduler is an object with the method get_next_task
        that can feed new tasks on demand'''
        self.task_scheduler = task_scheduler

    def next(self, learner_input):
        '''Main loop of the Environment. Receives one bit from the learner and
        produces a response (also one bit)'''
        # Make sure we have a task
        if not self._current_task:
            self._switch_new_task()

        # If the task has not reached the end by either Timeout or
        # achieving the goal
        if not self._current_task.has_ended():
            # Check if a Timeout occurred
            if not self._current_task.check_timeout(self._task_time):
                # Process the input from the learner and raise events
                if learner_input is not None:
                    # record the input from the learner and deserialize it
                    self._input_channel.consume_bit(learner_input)
            # We are in the middle of the task, so no rewards are given
            reward = None
        else:
            # If the task is ended and there is nothing else to say,
            # return reward and move to next task

            if self._output_channel.is_empty():
                # Have nothing more to say
                # reward the learner if necessary and switch to new task
                reward = self._reward if self._reward is not None else 0
                self._switch_new_task()
            else:
                # TODO: decide what to do here.
                # Should we consume the bit or not?
                self._input_channel.consume_bit(learner_input)
                # If there is still something to say, continue saying it
                reward = None
        # Get one bit from the output buffer and ship it
        if not self._output_channel.is_empty():
            output = self._output_channel.consume_bit()
        else:
            output = SILENCE
        # we hear to ourselves
        self._output_channel_listener.consume_bit(output)
        # advance time
        self._task_time += 1

        return output, reward

    def on_input_sequence_updated(self, sequence):
        if self.event_manager.raise_event(SequenceReceived(sequence)):
            self.logger.debug("Message received by running task: '{0}'".format(
                sequence))

    def on_input_message_updated(self, message):
        # send the current received message to the task
        if self.event_manager.raise_event(MessageReceived(
                message)):
            self.logger.debug("Message received by running task: '{0}'".format(
                message))

    def on_output_sequence_updated(self, sequence):
        self.event_manager.raise_event(OutputSequenceUpdated(sequence))

    def on_output_message_updated(self, message):
        self.event_manager.raise_event(OutputMessageUpdated(message))

    def set_reward(self, reward, message='', priority=0):
        '''Sets the reward that is going to be given
        to the learner once the task has sent all the remaining message'''
        self._reward = reward
        self._current_task.end()
        self.set_message(message, priority)

    def set_message(self, message, priority=0):
        ''' Saves the message in the output buffer so it can be delivered
        bit by bit. It overwrites any previous content.
        '''
        if self._output_channel.is_empty() or priority >= self._output_priority:
            self._output_channel.set_message(message)
            self._output_priority = priority
        else:
            self.logger.info(
                'Message "{0}" blocked because of '
                'low priority ({1}<{2}) '.format(
                    message, priority, self._output_priority)
            )

    def raise_event(self, event):
        self.event_manager.raise_event(event)

    def raise_state_changed(self):
        '''
            This rases a StateChanged Event, meaning that something
            in the state of the world or the tasks changed (but we
            don't keep track what)
        '''
        # state changed events can only be raised if the current task is
        # started
        if self._current_task and self._current_task.has_started():
            # tasks that have a world should also take the world state as
            # an argument
            if self._current_world:
                self.raise_event(StateChanged(
                    self._current_world.state, self._current_task.state))
            else:
                self.raise_event(StateChanged(self._current_task.state))

    def _switch_new_task(self):
        '''
        Asks the task scheduler for a new task,
        reset buffers and time, and registers the event handlers
        '''
        # deregister previous event managers
        if self._current_task:
            self._current_task.deinit()
            self._deregister_task_triggers(self._current_task)

        # pick a new task
        self._current_task = self.task_scheduler.get_next_task()
        try:
            # This is to check whether the user didn't mess up in instantiating
            # the class
            self._current_task.get_world()
        except TypeError:
            raise RuntimeError("The task {0} is not correctly instantiated. "
                               "Are you sure you are not forgetting to "
                               "instantiate the class?".format(
                                   self._current_task))
        self.logger.debug("Starting new task: {0}".format(self._current_task))

        # check if it has a world:
        if self._current_task.get_world() != self._current_world:
            # if we had an ongoing world, end it.
            if self._current_world:
                self._current_world.end()
                self._deregister_task_triggers(self._current_world)
            self._current_world = self._current_task.get_world()
            if self._current_world:
                # register new event handlers for the world
                self._register_task_triggers(self._current_world)
                # initialize the new world
                self._current_world.init()
                # spin the wheel
                self._current_world.start()
            self.world_updated(self._current_world)
        # reset state
        self._task_time = 0
        self._reward = None
        self._input_channel.clear()
        self._output_channel.clear()
        self._output_channel_listener.clear()
        # register new event handlers
        self._register_task_triggers(self._current_task)
        # we reset the state of the task
        self._current_task.init()
        # raise the Start event
        self._current_task.start()
        self.task_updated(self._current_task)

    def _deregister_task_triggers(self, task):
        for trigger in task.get_triggers():
            try:
                self.event_manager.deregister(task, trigger)
            except ValueError:
                # if the trigger was not registered, we don't worry about it
                pass
            except KeyError:
                # if the trigger was not registered, we don't worry about it
                pass

    def _register_task_triggers(self, task):
        for trigger in task.get_triggers():
            self.event_manager.register(task, trigger)

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
from core.aux.observer import Observable
from core.events import Trigger, Start, StateChanged, MessageReceived, \
    SequenceReceived, Timeout, OutputSequenceUpdated, OutputMessageUpdated, \
    Init, WorldStart, WorldInit, Ended
from collections import defaultdict
import logging
import itertools
import re
# Event handlers are annotated through decorators and are automatically
# registered by the environment on Task startup

# Implementation trick to remember the type of event and the filtering condition
# that is informed through the decorators.
# We map the annotated methods to their corresponding triggers, so when we start
# a task, we can scan through its memebers and find the trigger here.
global_event_handlers = {}


# Decorator for the Start of Task event handler
def on_start():
    def register(f):
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(Start, lambda e: True, f)
        return f
    return register


# Decorator for the End of Task event handler
def on_ended():
    def register(f):
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(Ended, lambda e: True, f)
        return f
    return register


# Decorator for the World Start event handler
def on_world_start():
    def register(f):
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(WorldStart, lambda e: True, f)
        return f
    return register


# Decorator for the Init event handler
def on_init():
    def register(f):
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(Init, lambda e: True, f)
        return f
    return register


# Decorator for the Init event handler
def on_world_init():
    def register(f):
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(WorldInit, lambda e: True, f)
        return f
    return register


# Decorator for the StateChanged event handler
def on_state_changed(condition):
    def register(f):
        # The filtering condition is given as an argument.
        # There could be one or two state objects (corresponding to the
        # world state). So we check if we need to call the condition with
        # one or two arguments.
        global_event_handlers[f] = Trigger(
            StateChanged, lambda e: e.second_state and
            condition(e.state, e.second_state) or
            (not e.second_state and condition(e.state)), f)
        return f
    return register


def on_message(target_message=None):
    def register(f):
        # If a target message is given, interpret it as a regular expression
        if target_message:
            cmessage = re.compile(target_message)
        else:
            cmessage = None
        # The filtering condition applied the target message expression
        # to the event message
        global_event_handlers[f] = Trigger(
            MessageReceived,
            lambda e: cmessage is None or cmessage.search(e.message), f)
        return f
    return register


def on_output_message(target_message=None):
    def register(f):
        # If a target message is given, interpret it as a regular expression
        if target_message:
            cmessage = re.compile(target_message)
        else:
            cmessage = None
        # The filtering condition applied the target message expression
        # to the event message
        global_event_handlers[f] = Trigger(
            OutputMessageUpdated,
            lambda e: cmessage is None or cmessage.search(e.output_message), f)
        return f
    return register


def on_sequence(target_sequence=None):
    def register(f):
        if target_sequence:
            csequence = re.compile(target_sequence)
        else:
            csequence = None
        # The filtering condition is either the target bit itself or nothing
        global_event_handlers[f] = Trigger(
            SequenceReceived,
            lambda e: csequence is None or csequence.search(e.sequence), f)
        return f
    return register


def on_output_sequence(target_sequence=None):
    def register(f):
        if target_sequence:
            csequence = re.compile(target_sequence)
        else:
            csequence = None
        # The filtering condition is either the target bit itself or nothing
        global_event_handlers[f] = Trigger(
            OutputSequenceUpdated,
            lambda e: csequence is None or csequence.search(e.output_sequence),
            f)
        return f
    return register


def on_timeout():
    def register(f):
        # There is no filtering condition (it always activates if registered)
        global_event_handlers[f] = Trigger(Timeout, lambda e: True, f)
        return f
    return register


def handler_to_trigger(f):
    '''checks whether f is a function and it was registered to a Trigger.
    If so, it returns the trigger.
    '''
    try:
        if f in global_event_handlers:
            return global_event_handlers[f]
        else:
            return None
    except TypeError:
        # if f is unhashable, it's definetly not a funciton
        return None


class StateTrackingDefaultdictWrapper(defaultdict):
    '''This is a wrapper for variables stored in a State object so
    if something in them change, the original State also gets changed'''
    def __init__(self, obj, owner):
        '''owner here is the State or a parent StateVariable'''
        super(StateTrackingDefaultdictWrapper, self).__init__(
            obj.default_factory, obj)
        self._owner = owner

    def __setitem__(self, name, value):
        super(StateTrackingDefaultdictWrapper, self).__setitem__(name, value)
        self._raise_state_changed()

    def _raise_state_changed(self):
        '''recursively forwards the call to the owner'''
        self._owner._raise_state_changed()


class StateTrackingDictionaryWrapper(dict):
    '''This is a wrapper for variables stored in a State object so
    if something in them change, the original State also gets changed'''
    def __init__(self, obj, owner):
        '''owner here is the State or a parent StateVariable'''
        super(StateTrackingDictionaryWrapper, self).__init__(obj)
        self._owner = owner

    def __setitem__(self, name, value):
        super(StateTrackingDictionaryWrapper, self).__setitem__(name, value)
        self._raise_state_changed()

    def _raise_state_changed(self):
        '''recursively forwards the call to the owner'''
        self._owner._raise_state_changed()


class State(object):
    '''Holds the state variables for a Task or a world and raises events when
    they change'''
    def __init__(self, owner):
        '''owner is the Taks or World whose state we keep track of'''
        super(State, self).__setattr__('_owner', owner)
        super(State, self).__setattr__('logger',
                                        logging.getLogger(__name__))

    def __setattr__(self, name, value):
        '''intercept every time a value is updated to raise the associated event
        '''
        # wrap the variable in an StateVariable to report whether it changes
        if isinstance(value, defaultdict):
            self.logger.info("Wrapping variable {0} as a defaultdict"
                             .format(value))
            value = StateTrackingDefaultdictWrapper(value, self)
        elif isinstance(value, dict):
            self.logger.info("Wrapping variable {0} as a dict".format(value))
            value = StateTrackingDictionaryWrapper(value, self)
        # apply the assignment operation
        super(State, self).__setattr__(name, value)
        # raise a StateChanged
        self._raise_state_changed()

    def _raise_state_changed(self):
        self._owner._raise_state_changed()


class ScriptSet(object):
    def __init__(self, env):
        self._env = env
        self.init()
        # a bit ugly, but there are worse things in life
        self.state_updated = Observable()

    def init(self):
        self._started = False
        self._ended = False
        # this is where all the state variables should be kept
        self.state = State(self)

    def has_started(self):
        return self._started

    def has_ended(self):
        return self._ended

    def start(self):
        self._started = True
        self._ended = False

    def end(self):
        self._ended = True

    def dyn_add_handler(self, handler):
        '''deregisters and registers back all the triggers in the task
        in case some have been updated/removed/added'''
        trigger = handler_to_trigger(handler)
        if trigger:
            self._env._register_task_trigger(self, trigger)

    def get_triggers(self):
        triggers = []
        for fname in dir(self):
            try:
                # We try to extract the function object that was registered
                f = getattr(self, fname).im_func
                trigger = handler_to_trigger(f)
                if trigger:
                    triggers.append(trigger)
            except AttributeError:
                pass
        return triggers

    def _raise_state_changed(self):
        self._env.raise_state_changed()
        # notify (outside) observers
        self.state_updated(self)

    def __str__(self):
        return str(self.__class__.__name__)

    # ### API for the scripts ###
    def set_reward(self, reward, message='', priority=1):
        self._env.set_reward(reward, message, priority)

    def set_message(self, message, priority=1):
        self._env.set_message(message, priority)

    def clear_input_channel(self):
        self._env._input_channel.clear()


class World(ScriptSet):
    def __init__(self, env):
        super(World, self).__init__(env)

    def start(self):
        super(World, self).start()
        self._env.raise_event(WorldStart())

    def init(self):
        super(World, self).init()
        self._env.raise_event(WorldInit())


# Base class for tasks
class Task(ScriptSet):
    def __init__(self, env, max_time, world=None):
        super(Task, self).__init__(env)
        self._world = world
        self._max_time = max_time

    def get_world(self):
        return self._world

    def check_timeout(self, t):
        assert t <= self._max_time, '{0} > {1}'.format(t, self._max_time)
        if t == self._max_time:
            self._env.event_manager.raise_event(Timeout())
            self._ended = True
            return True
        return False

    def start(self):
        super(Task, self).start()
        self._env.raise_event(Start())

    def init(self):
        super(Task, self).init()
        self._env.raise_event(Init())

    def deinit(self):
        self._env.raise_event(Ended())

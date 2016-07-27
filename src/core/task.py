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
from core.events import Trigger
from collections import defaultdict, namedtuple
import logging
import re

# These are the possible types of events (with their parameters, if any)
Start = namedtuple('Start', ())
Ended = namedtuple('Ended', ())
WorldStart = namedtuple('WorldStart', ())
Init = namedtuple('Init', ())
WorldInit = namedtuple('WorldInit', ())
Timeout = namedtuple('Timeout', ())

SequenceReceived = namedtuple('SequenceReceived', ('sequence',))
OutputSequenceUpdated = namedtuple('OutputSequenceUpdated',
                                   ('output_sequence',))
OutputMessageUpdated = namedtuple('OutputMessageUpdated',
                                   ('output_message',))


# horrible way of making second_state optional
class StateChanged(namedtuple('StateChanged', ('state', 'second_state'))):
    def __new__(cls, state, second_state=None):
        return super(StateChanged, cls).__new__(cls, state, second_state)


# helper methods for handling received messages
class MessageReceived():
    def __init__(self, message):
        self.message = message
        # this instance variable gets assigned the outcome of the
        # trigger's condition
        self.condition_outcome = None

    def is_message(self, msg, suffix=''):
        return self.message[-(len(msg) + len(suffix)):-len(suffix)] == msg and\
            suffix == self.message[-len(suffix):]

    def get_match(self, ngroup=0):
        return self.condition_outcome.group(ngroup)

    def get_match_groups(self):
        return self.condition_outcome.groups()

# Event handlers are annotated through decorators and are automatically
# registered by the environment on Task startup

# Implementation trick to remember the type of event and the filtering condition
# that is informed through the decorators.
# We map the annotated methods to their corresponding triggers, so when we start
# a task, we can scan through its memebers and find the trigger here.
global_event_handlers = {}


def method_to_func(f):
    try:
        return f.im_func
    except AttributeError:
        return f


# Decorator for the Start of Task event handler
def on_start():
    def register(f):
        f = method_to_func(f)
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(Start, lambda e: True, f)
        return f
    return register


# Decorator for the End of Task event handler
def on_ended():
    def register(f):
        f = method_to_func(f)
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(Ended, lambda e: True, f)
        return f
    return register


# Decorator for the World Start event handler
def on_world_start():
    def register(f):
        f = method_to_func(f)
        # The filtering condition is always True
        global_event_handlers[f] = Trigger(WorldStart, lambda e: True, f)
        return f
    return register


# Decorator for the Init event handler
def on_init():
    def register(f):
        f = method_to_func(f)
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
        f = method_to_func(f)
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
        f = method_to_func(f)
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
        f = method_to_func(f)
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
        f = method_to_func(f)
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
        f = method_to_func(f)
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
        f = method_to_func(f)
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
        return self._owner._raise_state_changed()


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
        return self._owner._raise_state_changed()


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
        return self._owner._raise_state_changed()


class ScriptSet(object):
    def __init__(self, env):
        self._env = env
        self.init()
        # a bit ugly, but there are worse things in life
        self.state_updated = Observable()
        # remember dynamically register handlers to destroy their triggers
        self.dyn_handlers = set()

    def init(self):
        self._started = False
        self._ended = False
        # this is where all the state variables should be kept
        self.state = State(self)

    def clean_dynamic_handlers(self):
        for h in self.dyn_handlers:
            del global_event_handlers[h]
        self.dyn_handlers = set()

    def has_started(self):
        return self._started

    def has_ended(self):
        return self._ended

    def start(self):
        self._started = True
        self._ended = False

    def end(self):
        self._ended = True

    def add_handler(self, handler):
        '''
        Adds and registers a handler.
        '''
        trigger = handler_to_trigger(handler)
        if trigger:
            self._env._register_task_trigger(self, trigger)
            self.dyn_handlers.add(handler)

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
        ret = self._env.raise_state_changed()
        if self.has_started():
            # notify (outside) observers
            self.state_updated(self)
        return ret

    def __str__(self):
        return str(self.__class__.__name__)

    # ### API for the scripts ###
    def set_reward(self, reward, message='', priority=0):
        self._env.set_reward(reward, message, priority)

    def set_message(self, message, priority=0):
        self._env.set_message(message, priority)

    def ignore_last_char(self):
        '''
        Replaces the last character in the input channel with a silence.
        '''
        self._env._input_channel.set_deserialized_buffer(
            self._env._input_channel.get_text()[:-1] +
            self._env._serializer.SILENCE_TOKEN
        )


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
        # if we are still in the process of outputting a message,
        # let it finish
        if t >= self._max_time and self._env._output_channel.is_empty():
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

    # ### API for the scripts ###
    def get_time(self):
        '''Gets the environment's task time'''
        return self._env._task_time

    def set_reward(self, reward, message='', priority=1):
        '''Assigns a reward to the learner and ends the task.
        Args:
            reward: numerical reward given to the learner
            message: optional message to be given with the reward
            priotity: the priority of the message. If there is another
                message on the output stream and the priority is lower than it,
                the message will be blocked.'''
        super(Task, self).set_reward(reward, message, priority)

    def set_message(self, message, priority=1):
        super(Task, self).set_message(message, priority)

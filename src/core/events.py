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
from collections import namedtuple
import logging

# When a task is started, it will register a set of triggers
# which, for a specific kind of event (see below) and a further given
# filtering condition, it will call the specified event_handler function
Trigger = namedtuple('Trigger', ('type', 'condition', 'event_handler'))

# These are the possible types of events (with their parameters, if any)
Start = namedtuple('Start', ())
Ended = namedtuple('Ended', ())
WorldStart = namedtuple('WorldStart', ())
Init = namedtuple('Init', ())
WorldInit = namedtuple('WorldInit', ())
Timeout = namedtuple('Timeout', ())


# horrible way of making second_state optional
class StateChanged(namedtuple('StateChanged', ('state', 'second_state'))):
    def __new__(cls, state, second_state=None):
        return super(StateChanged, cls).__new__(cls, state, second_state)


MessageReceived = namedtuple('MessageReceived', ('message',))
SequenceReceived = namedtuple('SequenceReceived', ('sequence',))
OutputSequenceUpdated = namedtuple('OutputSequenceUpdated',
                                   ('output_sequence',))
OutputMessageUpdated = namedtuple('OutputMessageUpdated',
                                   ('output_message',))


class EventManager:
    def __init__(self):
        self.triggers = {}
        self.logger = logging.getLogger(__name__)

    def register(self, observer, trigger):
        '''
        Register a trigger (a tuple containing an
        ActivationCondition -a function/functor- and an EventHandler
        - another function/functor-)
        '''
        # initialize a list for each type of event (it's just an optimizaiton)
        if trigger.type not in self.triggers:
            self.triggers[trigger.type] = []
        self.logger.debug(
            "Registering Trigger for {0} event with handler {1} of object of "
            "type {2}".format(trigger.type.__name__, trigger.event_handler,
                              observer.__class__.__name__))
        # save the trigger
        self.triggers[trigger.type].append((observer, trigger))

    def deregister(self, observer, trigger):
        self.triggers[trigger.type].remove((observer, trigger))

    def clear(self):
        '''
        Deregisters all triggers
        '''
        self.triggers.clear()

    def raise_event(self, event):
        handled = False
        # check if we have any trigger at all of this type of event
        if event.__class__ in self.triggers:
            # for all the triggers registered for this type of event
            for observer, trigger in self.triggers[event.__class__]:
                # check if the filtering condition is a go
                if trigger.condition(event):
                    self.logger.debug('{0} handled by {1}'.format(
                        event, trigger.event_handler))
                    # call the event handler
                    trigger.event_handler(observer, event)
                    # remember we handled the event and
                    # keep on processing other events
                    handled = True
        return handled

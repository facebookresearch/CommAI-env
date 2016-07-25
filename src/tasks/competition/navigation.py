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
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_init
import tasks.competition.messages as msg
from tasks.competition.objects_properties import global_properties
import random

# use the set of objects from the objects-properties association tasks.
objects = set(obj for basket, objects in global_properties.items()
                  for obj in objects)


TIME_CHAR = 8
TIME_VERB = (len("Say 'I xxxxxxxxxxxx' to xxxxxxxxxxxx.") +
             len("You xxxxxxxxxxxxed.")) * TIME_CHAR
TIME_TURN = (len("I turn right.") + len("You turned.")) * TIME_CHAR
TIME_MOVE = (len("I move forward.") + len("You moved.")) * TIME_CHAR
TIME_PICK = (len("I pick up the xxxxxxxxxxxx.") +
             len("You picked up the xxxxxxxxxxxx.")) * TIME_CHAR
TIME_GIVE = (len("I give you an xxxxxxxxxxxx.") +
             len("You gave me an xxxxxxxxxxxx.")) * TIME_CHAR


class TurningTask(Task):
    def __init__(self, env, world):
        super(TurningTask, self).__init__(
            env=env, max_time=3 * TIME_TURN, world=world)

    @on_init()
    def on_init(self, event):
        self.state.init_dir = self.get_world().state.learner_direction
        self.target_turn = random.choice(['left', 'right'])
        if self.target_turn == 'right':
            self.state.target_direction = \
                self.get_world().get_clockwise_direction(1)
        else:
            self.state.target_direction = \
                self.get_world().get_clockwise_direction(-1)

    @on_start()
    def on_start(self, event):
        self.set_message("Turn {0}.".format(self.target_turn))

    @on_state_changed(
        lambda ws, ts: ws.learner_direction == ts.target_direction)
    def on_moved(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class MovingTask(Task):
    def __init__(self, env, world):
        super(MovingTask, self).__init__(
            env, max_time=3 * TIME_MOVE, world=world)

    @on_init()
    def on_init(self, event):
        self.state.initial_pos = self.get_world().state.learner_pos
        dp = self.get_world().valid_directions[
            self.get_world().state.learner_direction]
        self.state.dest_pos = self.state.initial_pos + dp

    @on_start()
    def on_start(self, event):
        self.set_message("Move forward.")

    @on_state_changed(lambda ws, ts: ws.learner_pos == ts.dest_pos)
    def on_moved(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class MovingRelativeTask(Task):
    def __init__(self, env, world):
        super(MovingRelativeTask, self).__init__(
            env=env, max_time=2 * TIME_TURN + 2 * TIME_MOVE, world=world)

    # initialize state variables
    @on_init()
    def on_init(self, event):
        self.state.init_dir = self.get_world().state.learner_direction
        self.state.initial_pos = self.get_world().state.learner_pos
        self.target_turn = random.choice(['left', 'right'])
        if self.target_turn == 'right':
            self.state.target_dir = \
                self.get_world().get_clockwise_direction(1)
        else:
            self.state.target_dir = \
                self.get_world().get_clockwise_direction(-1)
        dp = self.get_world().valid_directions[self.state.target_dir]
        self.state.dest_pos = self.state.initial_pos + dp

    @on_start()
    def on_start(self, event):
        self.set_message("Move {0}.".format(self.target_turn))

    @on_state_changed(lambda ws, ts: ws.learner_pos == ts.dest_pos)
    def on_moved(self, event):
        self.set_reward(1)


class MovingAbsoluteTask(Task):
    def __init__(self, env, world):
        super(MovingAbsoluteTask, self).__init__(
            env=env, max_time=8 * TIME_TURN + 4 * TIME_MOVE, world=world)

    # initialize state variables
    @on_init()
    def on_init(self, event):
        self.state.init_dir = self.get_world().state.learner_direction
        self.state.initial_pos = self.get_world().state.learner_pos
        self.target_turn = random.choice(['left', 'right'])
        if self.target_turn == 'right':
            self.state.target_dir = \
                self.get_world().get_clockwise_direction(1)
        else:
            self.state.target_dir = \
                self.get_world().get_clockwise_direction(-1)
        dp = self.get_world().valid_directions[self.state.target_dir]
        self.state.dest_pos = self.state.initial_pos + dp

    @on_start()
    def on_start(self, event):
        self.set_message("You are facing {0}, move {1}.".format(
            self.state.init_dir, self.state.target_dir))

    @on_state_changed(lambda ws, ts: ws.learner_pos == ts.dest_pos)
    def on_moved(self, event):
        self.set_reward(1)


class PickUpTask(Task):

    def __init__(self, env, world):
        super(PickUpTask, self).__init__(
            env=env, max_time=50 * TIME_CHAR + 2 * TIME_PICK, world=world)

    @on_init()
    def on_init(self, event):
        self.target_obj = random.choice(objects)
        ws = self.get_world().state
        ld = ws.learner_direction
        lp = ws.learner_pos
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        self.get_world().put_entity(lp + ld, self.target_obj, True, True)

        self.add_handler(
            on_state_changed(lambda ws, ts:
                             ws.learner_inventory[self.target_obj] ==
                             ts.initial_count + 1)
            (self.on_object_picked_up.im_func))

    @on_start()
    def on_start(self, event):
        self.set_message("You have {indef_object} next to you. "
                         "Pick up the {object}.".format(
                             indef_object=indef_article(self.target_obj),
                             object=self.target_obj))

    def on_object_picked_up(self, event):
        self.set_reward(1, "You picked up the {0}.".format(self.target_obj))


def indef_article(x):
    if x[0] in 'aeiou':
        return 'an ' + x
    else:
        return 'a ' + x


class PickUpAroundTask(Task):

    def __init__(self, env, world):
        super(PickUpAroundTask, self).__init__(
            env=env, max_time=50 * TIME_CHAR + 2 * TIME_PICK +
            4 * TIME_MOVE + 4 * TIME_TURN, world=world)

    @on_init()
    def on_init(self, event):
        self.target_obj = random.choice(objects)
        self.direction = random.choice(self.get_world().valid_directions.keys())
        ws = self.get_world().state
        p = ws.learner_pos + self.get_world().valid_directions[self.direction]
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        self.get_world().put_entity(p, self.target_obj, True, True)

        self.add_handler(
            on_state_changed(lambda ws, ts:
                             ws.learner_inventory[self.target_obj] ==
                             ts.initial_count + 1)
            (self.on_object_picked_up.im_func))

    @on_start()
    def on_start(self, event):
        self.set_message("There is {0} {1} from you. Pick up the {0}.".format(
                         indef_article(self.target_obj), self.direction))

    def on_object_picked_up(self, event):
        self.set_reward(1, "You picked up the {0}.".format(self.target_obj))


class PickUpInFrontTask(Task):

    def __init__(self, env, world):
        super(PickUpInFrontTask, self).__init__(
            env=env, max_time=50 * TIME_CHAR + 2 * TIME_PICK, world=world)

    @on_init()
    def on_init(self, event):
        self.target_obj = random.choice(objects)
        ws = self.get_world().state
        p = ws.learner_pos + self.get_world().valid_directions[
            ws.learner_direction]
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        self.get_world().put_entity(p, self.target_obj, True, True)

        self.add_handler(
            on_state_changed(lambda ws, ts:
                             ws.learner_inventory[self.target_obj] ==
                             ts.initial_count + 1)
            (self.on_object_picked_up.im_func))

    @on_start()
    def on_start(self, event):
        self.set_message("There is {0} in front of you. Pick up the {0}."
                         .format(indef_article(self.target_obj)))

    def on_object_picked_up(self, event):
        self.set_reward(1, "You picked up the {0}.".format(self.target_obj))


class GiveTask(Task):

    def __init__(self, env, world):
        super(GiveTask, self).__init__(
            env=env, max_time=50 * TIME_CHAR + 2 * TIME_GIVE, world=world)

    @on_init()
    def on_init(self, event):
        self.target_obj = random.choice(objects)
        ws = self.get_world().state
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        ws.learner_inventory[self.target_obj] += 1

    @on_start()
    def on_start(self, event):
        self.set_message("I gave you {0}. Give it back to me by saying "
                          "\"I give you {0}\"."
                          .format(indef_article(self.target_obj)))

    @on_message("I give you (an? (\w+))\.$")
    def on_give_me_object(self, event):
        if event.get_match(1) == indef_article(self.target_obj):
            ws = self.get_world().state
            ws.learner_inventory[self.target_obj] -= 1
            self.set_reward(1, "You gave me {0}.".format(
                indef_article(self.target_obj)))
        elif event.get_match(2) == self.target_obj:
            self.set_message("Wrong article.")
        elif event.get_match(2) != self.target_obj:
            self.set_message("I have asked you to give me {0}, not {1}."
                             .format(indef_article(self.target_obj),
                                     indef_article(event.get_match(2))))


class PickUpAroundAndGiveTask(Task):

    def __init__(self, env, world):
        super(PickUpAroundAndGiveTask, self).__init__(
            env=env, max_time=50 * TIME_CHAR + 4 * TIME_PICK + 4 * TIME_GIVE +
            4 * TIME_MOVE + 4 * TIME_TURN,
            world=world)

    @on_init()
    def on_init(self, event):
        self.target_obj = random.choice(objects)
        self.direction = random.choice(self.get_world().valid_directions.keys())
        ws = self.get_world().state
        p = ws.learner_pos + self.get_world().valid_directions[self.direction]
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        self.get_world().put_entity(p, self.target_obj, True, True)
        self.object_picked_up = False
        self.add_handler(
            on_state_changed(lambda ws, ts:
                             ws.learner_inventory[self.target_obj] ==
                             ts.initial_count + 1)
            (self.on_object_picked_up.im_func))

    @on_start()
    def on_start(self, event):
        self.set_message("There is {0} {1} from you."
                         " Pick it up and give it to me.".format(
                             indef_article(self.target_obj), self.direction))

    def on_object_picked_up(self, event):
        self.object_picked_up = True

    # FIXME: make this a verb of the world?
    @on_message("I give you (an? (\w+))\.$")
    def on_give_me_object(self, event):
        self.set_message("dsdfs")
        if event.get_match(1) == indef_article(self.target_obj):
            if self.object_picked_up:
                ws = self.get_world().state
                ws.learner_inventory[self.target_obj] -= 1
                self.set_reward(1, "You gave me {0}.".format(
                    indef_article(self.target_obj)))
            else:
                self.set_message("You have to pick up the {0} first."
                                 .format(self.target_obj))
        elif event.get_match(2) == self.target_obj:
            self.set_message("Wrong article.")
        elif event.get_match(2) != self.target_obj:
            self.set_message("I have asked you to give me {0}, not {1}."
                             .format(indef_article(self.target_obj),
                                     indef_article(event.get_match(2))))
        else:
            self.set_message(event.get_match(1))


def pluralize(obj, c):
    if c == 1:
        return obj
    else:
        return obj + 's'


# TODO: also accept numbers written in letters
class CountingInventoryTask(Task):

    def __init__(self, env, world):
        super(CountingInventoryTask, self).__init__(
            env=env, max_time=100 * TIME_CHAR,
            world=world)

    @on_start()
    def on_start(self, event):
        self.target_obj = random.choice(objects)
        self.set_message("How many {0} do you have?".format(
                         pluralize(self.target_obj, 2)))
        # Perhaps we should standardize some feedback state variable
        self.feedback_given = False

    @on_message("\.$")
    def on_something_said(self, event):
        count = self.get_world().state.learner_inventory[self.target_obj]
        # TODO: add letter version of the number here
        if event.is_message(str(count) + '.'):
            self.set_reward(1, "Correct!")
        else:
            if not self.feedback_given:
                self.set_message("No, you have {0} {1}.".format(count,
                                 pluralize(self.target_obj, count)))
                self.feedback_given = True
            else:
                self.set_reward(0, "Sorry, that's wrong!")


# TODO: also accept numbers written in letters
class CountingInventoryGivingTask(Task):

    def __init__(self, env, world):
        super(CountingInventoryGivingTask, self).__init__(
            env=env, max_time=10000 * TIME_CHAR,
            world=world)
        self.stop_propagation = None

    @on_start()
    def on_start(self, event):
        self.target_obj = random.choice(objects)
        self.set_message("How many {0} do you have?".format(
                         pluralize(self.target_obj, 2)))
        # Perhaps we should standardize some feedback state variable
        self.stage = 0

    @on_message("\.$")
    def on_something_said(self, event):
        # FIXME: move this check to the event proccessing
        # This check ensures that this event doesn't get activated
        # at the same time as "I give you an X."
        if self.stop_propagation == event:
            return
        count = self.get_world().state.learner_inventory[self.target_obj]
        # TODO: add letter version of the number here
        if self.stage == 3:
            if event.is_message(str(count) + '.'):
                self.set_reward(1, "Correct!")
            else:
                self.set_message("Sorry, that's wrong!")
        elif self.stage == 0 or self.stage == 1:
            msg = ''
            if event.is_message(str(count) + '.'):
                msg += "Correct!"
                ws = self.get_world().state
                if self.stage == 0:
                    ws.learner_inventory[self.target_obj] += 1
                    msg += " I gave you {0}."\
                        " How many {1} do you have now?".format(
                            indef_article(self.target_obj),
                            pluralize(self.target_obj, 2))
                    self.stage = 1
                elif self.stage == 1:
                    msg += " Now give the {0} back to me.".format(
                        self.target_obj)
                    self.stage = 2
            else:
                msg += "Sorry, that's wrong!"
            self.set_message(msg)

    # FIXME: make this a verb of the world?
    @on_message("I give you (an? (\w+))\.$")
    def on_give_me_object(self, event):
        if self.stage != 2:
            self.set_message('I haven\'t asked you to give me anything.')
        else:
            if event.get_match(1) == indef_article(self.target_obj):
                ws = self.get_world().state
                ws.learner_inventory[self.target_obj] -= 1
                self.set_message("Good! You gave me {0}. "
                                 "How many {1} do you have now?".format(
                                     indef_article(self.target_obj),
                                     pluralize(self.target_obj, 2)))
                self.stage = 3
                # FIXME: change for an event.stop_propagation()
                self.stop_propagation = event
                # FIXME: we need an event.stop_propagation() thingy for this to
                # work!
            elif event.get_match(2) == self.target_obj:
                self.set_message("Wrong article.")
            elif event.get_match(2) != self.target_obj:
                self.set_message("I have asked you to give me {0}, not {1}."
                                 .format(indef_article(self.target_obj),
                                         indef_article(event.get_match(2))))

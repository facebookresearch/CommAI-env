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
    on_state_changed, on_timeout, on_output_message, on_ended
import tasks.competition.messages as msg
from tasks.competition.base import BaseTask
from tasks.competition.objects_properties import global_properties
import random

# use the set of objects from the objects-properties association tasks.
objects = list(set(obj for basket, objects in global_properties.items()
                   for obj in objects))
dirs = ['east', 'west', 'north', 'south']

TIME_CHAR = 8
TIME_VERB = (len("Say 'I xxxxxxxxxxxx' to xxxxxxxxxxxx.") +
             len("You xxxxxxxxxxxxed.")) * TIME_CHAR
TIME_TURN = (len("I turn right.") + len("You turned.")) * TIME_CHAR
TIME_MOVE = (len("I move forward.") + len("You moved.")) * TIME_CHAR
TIME_PICK = (len("I pick up the xxxxxxxxxxxx.") +
             len("You picked up the xxxxxxxxxxxx.")) * TIME_CHAR
TIME_GIVE = (len("I give you an xxxxxxxxxxxx.") +
             len("You gave me an xxxxxxxxxxxx.")) * TIME_CHAR


class TurningTask(BaseTask):
    def __init__(self, world):
        super(TurningTask, self).__init__(
            max_time=3 * TIME_TURN, world=world)

    @on_start()
    def on_start(self, event):
        # during initalization of task, save the direction the learner is facing
        self.state.init_dir = self.get_world().state.learner_direction
        # randomly choose a target direction and save it too
        self.target_turn = random.choice(['left', 'right'])
        if self.target_turn == 'right':
            self.state.target_direction = \
                self.get_world().get_clockwise_direction(1)
        else:
            self.state.target_direction = \
                self.get_world().get_clockwise_direction(-1)

        # ask the learner to turn in the target direction
        self.set_message("Turn {0}.".format(self.target_turn))

    @on_state_changed(
        lambda ws, ts: ws.learner_direction == ts.target_direction)
    def on_moved(self, event):
        # reward the learner when it's facing the right direction
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class MovingTask(BaseTask):
    def __init__(self, world):
        super(MovingTask, self).__init__(
            max_time=3 * TIME_MOVE, world=world)

    @on_start()
    def on_start(self, event):
        # during initalization task, save the learner's position
        self.state.initial_pos = self.get_world().state.learner_pos
        # save the destination position one step forward from the learner is
        dp = self.get_world().valid_directions[
            self.get_world().state.learner_direction]
        self.state.dest_pos = self.state.initial_pos + dp

        # ask the learner to move forward
        self.set_message("Move forward.")

    @on_state_changed(lambda ws, ts: ws.learner_pos == ts.dest_pos)
    def on_moved(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class MovingRelativeTask(BaseTask):
    def __init__(self, world):
        super(MovingRelativeTask, self).__init__(
            max_time=2 * TIME_TURN + 2 * TIME_MOVE, world=world)

    @on_start()
    def on_start(self, event):
        # during initalization task, save the direction the learner is facing
        self.state.init_dir = self.get_world().state.learner_direction
        # randomly choose a target direction and save the position
        # one step forward in that direction
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

        # Ask the learner to move in a particular direction (left or right)
        self.set_message("Move {0}.".format(self.target_turn))

    @on_state_changed(lambda ws, ts: ws.learner_pos == ts.dest_pos)
    def on_moved(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class MovingAbsoluteTask(BaseTask):
    def __init__(self, world):
        super(MovingAbsoluteTask, self).__init__(
            max_time=8 * TIME_TURN + 4 * TIME_MOVE, world=world)

    @on_start()
    def on_start(self, event):
        # during initalization task, save the direction the learner is facing
        self.state.init_dir = self.get_world().state.learner_direction
        # randomly choose a target direction and save the position
        # one step forward in that direction
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

        # Ask the learner to move in a particular absolute direction
        # (north, east, south, west)
        self.set_message("You are facing {0}, move {1}.".format(
            self.state.init_dir, self.state.target_dir))

    @on_state_changed(lambda ws, ts: ws.learner_pos == ts.dest_pos)
    def on_moved(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class PickUpTask(BaseTask):

    def __init__(self, world):
        super(PickUpTask, self).__init__(
            max_time=50 * TIME_CHAR + 2 * TIME_PICK, world=world)

    @on_start()
    def on_start(self, event):
        # choose some random object
        self.target_obj, = random.sample(objects, 1)
        # find the cell in front of the learner
        ws = self.get_world().state
        ld = self.get_world().valid_directions[ws.learner_direction]
        lp = ws.learner_pos
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        # place the object there
        self.get_world().put_entity(lp + ld, self.target_obj, True, True)

        self.add_handler(
            on_state_changed(lambda ws, ts:
                             ws.learner_inventory[self.target_obj] ==
                             ts.initial_count + 1)
            (self.on_object_picked_up))

        self.set_message("You have {indef_object} in front of you. "
                         "Pick up the {object}.".format(
                             indef_object=msg.indef_article(self.target_obj),
                             object=self.target_obj))

    def on_object_picked_up(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class PickUpAroundTask(BaseTask):

    def __init__(self, world):
        super(PickUpAroundTask, self).__init__(
            max_time=50 * TIME_CHAR + 2 * TIME_PICK +
            4 * TIME_MOVE + 4 * TIME_TURN, world=world)

    @on_start()
    def on_start(self, event):
        # choose a random object
        self.target_obj, = random.sample(objects, 1)
        # find a random cell around the learner
        self.direction = random.choice(list(self.get_world().valid_directions
                                            .keys()))
        ws = self.get_world().state
        p = ws.learner_pos + self.get_world().valid_directions[self.direction]
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        # place the object there
        self.get_world().put_entity(p, self.target_obj, True, True)

        self.add_handler(
            on_state_changed(lambda ws, ts:
                             ws.learner_inventory[self.target_obj] ==
                             ts.initial_count + 1)
            (self.on_object_picked_up))

        self.set_message("There is {indef_object} {direction} from you, "
                         "pick up the {object}.".format(
                             indef_object=msg.indef_article(self.target_obj),
                             direction=self.direction,
                             object=self.target_obj))

    def on_object_picked_up(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class PickUpInFrontTask(BaseTask):
    max_steps_forward = 10

    def __init__(self, world):
        super(PickUpInFrontTask, self).__init__(
            max_time=50 * TIME_CHAR + 2 * TIME_PICK +
            PickUpInFrontTask.max_steps_forward * TIME_MOVE, world=world)

    @on_start()
    def on_start(self, event):
        # choose a random object
        self.target_obj, = random.sample(objects, 1)
        ws = self.get_world().state
        # select a random number of steps
        self.n = random.randint(1, PickUpInFrontTask.max_steps_forward)
        # place the object that number of steps in front of the learner
        p = ws.learner_pos + self.n * self.get_world().valid_directions[
            ws.learner_direction]
        self.state.initial_count = ws.learner_inventory[self.target_obj]
        self.get_world().put_entity(p, self.target_obj, True, True)

        self.add_handler(
            on_state_changed(lambda ws, ts:
                             ws.learner_inventory[self.target_obj] ==
                             ts.initial_count + 1)
            (self.on_object_picked_up))

        self.set_message("There is {indef_object} {n} steps forward, "
                         "pick up the {object}."
                         .format(
                             indef_object=msg.indef_article(self.target_obj),
                             n=msg.number_to_string(self.n),
                             object=self.target_obj))

    def on_object_picked_up(self, event):
        self.set_reward(1, "You picked up the {0}.".format(self.target_obj))

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class GivingTask(BaseTask):

    def __init__(self, world):
        super(GivingTask, self).__init__(
            max_time=50 * TIME_CHAR + 2 * TIME_GIVE, world=world)

    @on_start()
    def on_start(self, event):
        ws = self.get_world().state
        # pick a random object
        self.state.target_obj, = random.sample(objects, 1)
        # give one of it to the learner
        ws.learner_inventory[self.state.target_obj] += 1
        # save how many objects of this we have
        self.state.initial_count = ws.teacher_inventory[self.state.target_obj]
        # inform the world that we can expect to receive such an object
        ws.teacher_accepts.add(self.state.target_obj)

        self.set_message("I gave you {indef_object}. Give it back to me "
                         "by saying \"I give you {indef_object}\"."
                          .format(indef_object=msg.indef_article(
                              self.state.target_obj)))

    # if I have one more of the target object, the learner solved the task.
    @on_state_changed(
        lambda ws, ts: ws.teacher_inventory[ts.target_obj] ==
        ts.initial_count + 1)
    def on_give_me_object(self, event):
        self.set_reward(1)

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class PickUpAroundAndGiveTask(BaseTask):

    def __init__(self, world):
        super(PickUpAroundAndGiveTask, self).__init__(
            max_time=50 * TIME_CHAR + 4 * TIME_PICK + 4 * TIME_GIVE +
            4 * TIME_MOVE + 4 * TIME_TURN,
            world=world)

    @on_start()
    def on_start(self, event):
        ws = self.get_world().state
        # pick a random object
        target_obj, = random.sample(objects, 1)
        self.state.target_obj = target_obj
        # save how many objects of this we have
        self.state.initial_count = ws.teacher_inventory[target_obj]
        # save how many instances of the object the learner intially had
        self.state.learner_initial_count = ws.learner_inventory[target_obj]
        # choose some random direction
        self.direction = random.choice(list(self.get_world().valid_directions
                                            .keys()))
        # measure a cell one step in that direction
        self.obj_pos = ws.learner_pos + \
            self.get_world().valid_directions[self.direction]
        # put an object in the given position
        self.get_world().put_entity(self.obj_pos, target_obj, True, True)
        # initialize a variable to check if the object has been picked up
        self.object_picked_up = False
        # inform the world that we can expect to receive such an object
        ws.teacher_accepts.add(self.state.target_obj)

        self.set_message("There is {indef_object} {direction} from you."
                         " Pick it up and give it to me.".format(
                             indef_object=msg.indef_article(
                                 self.state.target_obj),
                             direction=self.direction))

    @on_state_changed(lambda ws, ts:
                      ws.learner_inventory[ts.target_obj] ==
                      ts.learner_initial_count + 1)
    def on_object_picked_up(self, event):
        self.object_picked_up = True

    # if I have one more of the target object, the learner solved the task
    # if it also picked up the object in the grid.
    @on_state_changed(
        lambda ws, ts: ws.teacher_inventory[ts.target_obj] ==
        ts.initial_count + 1)
    def on_give_me_object(self, event):
        if self.object_picked_up:
            self.set_reward(1)
        else:
            self.set_message("You have to pick up the {object} first."
                             .format(object=self.state.target_obj))

    @on_timeout()
    def fail_learner(self, event):
        # cleaning up
        if not self.object_picked_up:
            self.get_world().remove_entity(self.obj_pos)
        self.set_message(random.choice(msg.timeout))

    @on_ended()
    def on_ended(self, event):
        # cleanup
        self.get_world().state.teacher_accepts.remove(self.state.target_obj)

#
# Counting + Proprioception
#


class CountingInventoryTask(BaseTask):

    def __init__(self, world):
        super(CountingInventoryTask, self).__init__(
            max_time=100 * TIME_CHAR,
            world=world)

    @on_start()
    def on_start(self, event):
        self.target_obj, = random.sample(objects, 1)
        self.set_message("How many {0} do you have?".format(
                         msg.pluralize(self.target_obj, 2)))

    @on_message("(\w+)\.$")
    def on_something_said(self, event):
        # find out the correct answer
        count = self.get_world().state.learner_inventory[self.target_obj]
        # get the answer of the learner and parse it
        answer = event.get_match(1)
        num_answer = msg.string_to_number(answer)
        if num_answer == count:
            self.set_reward(1, "Correct!")
        else:
            self.set_message("{negative_feedback} "
                             "You have {count} {objects}.".format(
                                 negative_feedback=random.choice(msg.failed),
                                 count=count,
                                 objects=msg.pluralize(self.target_obj,
                                                       count)))

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))


class CountingInventoryGivingTask(BaseTask):

    def __init__(self, world):
        super(CountingInventoryGivingTask, self).__init__(
            max_time=1000 * TIME_CHAR,
            world=world)

    @on_start()
    def on_start(self, event):
        self.failed = False
        self.time_gave_me_object = None
        self.state.target_obj, = random.sample(objects, 1)
        self.state.initial_count = \
            self.get_world().state.learner_inventory[self.state.target_obj]

        self.set_message("How many {0} do you have?".format(
                         msg.pluralize(self.state.target_obj, 2)))
        self.stages = ['initial-query', 'one-more-query', 'waiting-give-back',
                       'final-query']
        self.stage = 'initial-query'

    @on_message("(\w+)\.$")
    def on_answer_query(self, event):
        # if we are waiting for an object, then we don't expect an answer
        # to a query
        if self.stage == 'waiting-give-back':
            return
        # if you just gave me an object, then this is not the
        # answer for a query
        if self.time_gave_me_object == self.get_time():
            return
        # short variable for the world state
        ws = self.get_world().state
        # we check if the learner's answer matches the number of instances
        # it has of the given object
        count = ws.learner_inventory[self.state.target_obj]
        # get the answer of the learner and parse it
        answer = event.get_match(1)
        try:
            num_answer = msg.string_to_number(answer)
        except ValueError:
            num_answer = None
        # check if the learner has failed
        self.failed = self.failed or num_answer != count
        # get a feedback response
        feedback = random.choice(msg.congratulations) if num_answer == count \
                    else random.choice(msg.failed)
        if self.stage == 'initial-query':
            ws.learner_inventory[self.state.target_obj] += 1
            self.set_message(
                "{feedback} I gave you {indef_object}. "
                "How many {objects} do you have now?".format(
                    indef_object=msg.indef_article(self.state.target_obj),
                    objects=msg.pluralize(self.state.target_obj, 2),
                    feedback=feedback))
            self.stage = 'one-more-query'
        elif self.stage == 'one-more-query':
            self.set_message("{feedback} Now give the {object} back to me."
                             .format(object=self.state.target_obj,
                                     feedback=feedback))
            ws.teacher_accepts.add(self.state.target_obj)
            self.stage = 'waiting-give-back'
        elif self.stage == 'final-query':
            # reward the learner if it replied correctly all the questions
            if not self.failed:
                self.set_reward(1, feedback)
            else:
                self.set_reward(0, feedback)

    # if I have one more of the target object, the learner solved the task
    # if it also picked up the object in the grid.
    @on_state_changed(
        lambda ws, ts: ws.teacher_inventory[ts.target_obj] ==
        ts.initial_count + 1)
    def on_gave_me_target_object(self, event):
        if self.stage == 'waiting-give-back':
            self.time_gave_me_object = self.get_time()
            self.set_message(
                "Good! You gave me {indef_object}. "
                "How many {objects} do you have now?".format(
                    indef_object=msg.indef_article(self.state.target_obj),
                    objects=msg.pluralize(self.state.target_obj, 2)))
        self.stage = 'final-query'

    @on_timeout()
    def fail_learner(self, event):
        self.set_message(random.choice(msg.timeout))

    @on_ended()
    def on_ended(self, event):
        if self.stage in ['waiting-give-back', 'final-query']:
            # cleanup
            self.get_world().state.teacher_accepts.remove(self.state.target_obj)


class LookTask(BaseTask):
    # look in a predifined direction.
    def __init__(self, world):
        super(LookTask, self).__init__(max_time=1000, world=world)

    @on_start()
    def on_start(self, event):
        self.dir = random.choice(dirs)
        dir = self.get_world().state.learner_direction
        self.set_message("Look to the " + self.dir + "," +
                         " you are currently facing " + dir + ".")

    @on_message(r"I look\.$")
    def on_message(self, event):
        dir = self.get_world().state.learner_direction
        if dir == self.dir:
            self.set_reward(1, "Congratulations! "
                            "You are looking in the right direction.")


class LookAroundTask(Task):
    # the learner must look around his current position

    def __init__(self, world):
        super(LookAroundTask, self).__init__(max_time=5000, world=world)

    @on_start()
    def on_start(self, event):
        self.visited_dirs = {'east': False, 'west': False,
                             'north': False, 'south': False}
        self.ndir = 0
        dir = self.get_world().state.learner_direction
        self.set_message("Look around. You are facing " + dir + ".")
        self.state.learner_pos = self.get_world().state.learner_pos

    @on_state_changed(lambda ws, ts: ws.learner_pos != ts.learner_pos)
    def on_moved(self, event):
        self.set_reward(0, "You are not allowed to move.")

    @on_message(r"I look\.$")
    def on_message(self, event):
        dir = self.get_world().state.learner_direction
        if dir in self.visited_dirs and not self.visited_dirs[dir]:
            self.visited_dirs[dir] = True
            self.ndir += 1
            ddir = len(self.visited_dirs) - self.ndir
            if ddir == 0:
                self.set_reward(1, "Congratulations!")
            else:
                self.set_message(str(ddir) + " directions to go.")
        elif dir in self.visited_dirs:
            self.set_message("You already look here.")


class FindObjectAroundTask(Task):
    # set 4 objects around the learner, ask to find one of them.
    def __init__(self, world):
        super(FindObjectAroundTask, self).__init__(max_time=10000,
                                                   world=world)
        self.dir2obj = [0, 1, 2, 3]
        random.shuffle(self.dir2obj)

    @on_start()
    def on_start(self, event):
        # random assignment of object to location
        self.state.learner_pos = self.get_world().state.learner_pos
        pos = self.state.learner_pos
        pe = self.get_world().put_entity
        for i in range(0, len(dirs)):
            np = pos + self.get_world().valid_directions[dirs[i]]
            pe(np, objects[self.dir2obj[i]], True, True)
        self.dir = random.choice(self.dir2obj)
        self.obj = objects[self.dir2obj[self.dir]]
        self.instructions_completed = False
        self.set_message("Pick the " + self.obj + " next to you.")
        obj_count = self.get_world().state.learner_inventory[self.obj]
        self.add_handler(
            on_state_changed(
                lambda ws, ts: ws.learner_inventory[self.obj] == obj_count + 1)
            (self.on_object_picked.im_func)
        )

    @on_ended()
    def on_ended(self, event):
        pos = self.state.learner_pos
        for i in range(0, len(dirs)):
            np = pos + self.get_world().valid_directions[dirs[i]]
            self.get_world().remove_entity(np)

    def on_object_picked(self, event):
        self.set_reward(1, 'Well done!')

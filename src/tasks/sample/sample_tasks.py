# -*- coding: utf-8

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
from worlds.grid_world import Point, Span
import random


class RepeatingCharTask(Task):
    def __init__(self):
        super(RepeatingCharTask, self).__init__(max_time=100)

    @on_start()
    def on_start(self, event):
        self.target_char = chr(ord('a') + random.randint(0, 26))
        self.set_message(self.target_char)

    # on non-silent character
    @on_message("[^ ]")
    def on_message(self, event):
        if event.is_message(self.target_char):
            self.set_reward(1, "")
        else:
            self.set_reward(0, "")


class YesNoTask(Task):
    def __init__(self):
        super(YesNoTask, self).__init__(max_time=1000)

    @on_start()
    def on_start(self, event):
        random_obj = ''.join(chr(ord('a') + random.randint(0, 26))
                             for i in range(5))
        random_prop = ''.join(chr(ord('a') + random.randint(0, 26))
                              for i in range(5))
        self.coin_toss = random.randint(0, 1)
        self.set_message("{0} is {1}. Is {0} {2}?".format(
            random_obj, random_prop if self.coin_toss else "not " + random_prop,
            random_prop
        ))

    # on non-silent character
    @on_message("yes|no")
    def on_message(self, event):
        if self.coin_toss and event.get_match() == 'yes':
            self.set_reward(1, "")
        elif not self.coin_toss and event.get_match() == 'no':
            self.set_reward(1, "")
        else:
            self.set_reward(0, "")


class BeSilentTask(Task):
    def __init__(self):
        super(BeSilentTask, self).__init__(max_time=1000)

    @on_start()
    def on_start(self, event):
        self.set_message("Please, be quiet.")

    @on_sequence(r'1')
    def on_bitread(self, event):
        # if the learner produces a one, it loses
        self.set_reward(0, '')

    @on_timeout()
    def on_timeout(self, event):
        # if it reached timeout without loosing, it wins
        self.set_reward(1, '')


class RepeatingPhraseTask(Task):
    def __init__(self):
        super(RepeatingPhraseTask, self).__init__(max_time=1000)
        self.state.sample_state = 1

    @on_start()
    def on_start(self, event):
        # For illustrative purposes only, we defer the instructions to a
        # script that is executed when this variable takes the value 2
        self.state.sample_state = 2
        # Don't hear the input coming from the learner until the instructions
        # are over.
        self.instructions_completed = False

    # This handler gets executed when the sample state changes to 2
    @on_state_changed(lambda s: s.sample_state == 2)
    def on_state_changed(self, event):
        self.state.sample_state = 1
        self.set_message("Say 'I am not Mr Robot'.")

    @on_output_message(r"\.")
    def on_finished_instructions(self, event):
        self.instructions_completed = True

    @on_message()
    def on_any_message(self, event):
        if not self.instructions_completed:
            # we forget the input if the instructions are not completed yet
            self.ignore_last_char()

    # This handler gets exeuted whenever the learner says anything containing
    # the string "I am not a Robot" (thus, a mimicking learner will be given
    # credit)
    @on_message(r"I am not Mr Robot$")
    def on_correct_message(self, event):
        if self.instructions_completed:
            self.set_reward(1, "Correct")

    # This handler gets executed if the learner didn't solve the task in
    # 10000 steps
    @on_timeout()
    def on_timeout(self, event):
        self.set_message("Sorry, time is out.")


class SampleConflictingMessagesTask(Task):
    def __init__(self):
        super(SampleConflictingMessagesTask, self).__init__(max_time=1000)

    @on_start()
    def on_start(self, event):
        self.set_message("Say my name")

    @on_message("Say$")
    def on_disrespect(self, event):
        self.set_message("I'm Heisenberg, you don't give me orders.", 5)

    @on_message(r"my name$")
    def on_some_message(self, event):
        # Send a low priority message that will be blocked
        self.set_message("Are you repeating everything I say?", 1)

    @on_message(r"Heisenberg$")
    def on_keyword_message(self, event):
        # The priority parameter only applies for the message for now
        # In this case, the message will be blocked.
        self.set_reward(1, "You're Goddamn right.", priority=5)


class MovingTask(Task):
    def __init__(self, world):
        super(MovingTask, self).__init__(max_time=1000, world=world)

    # initialize state variables
    @on_start()
    def on_start(self, event):
        self.state.initial_pos = self.get_world().state.learner_pos
        dp = self.get_world().valid_directions[
            self.get_world().state.learner_direction]
        self.state.dest_pos = self.state.initial_pos + dp

        self.set_message("Say 'I move forward.'")

    # notice that we get the task state and the world state
    @on_state_changed(lambda ws, ts: ws.learner_pos == ts.dest_pos)
    def on_moved(self, event):
        self.set_reward(1)


class TurnLeftTask(Task):
    def __init__(self, world):
        super(TurnLeftTask, self).__init__(max_time=1000, world=world)
        self.cd = ['north', 'east', 'south', 'west']

    @on_start()
    def on_start(self, event):
        self.state.init_direction = self.get_world().state.learner_direction
        dest_index = ((self.cd.index(self.state.init_direction)) - 1) % 4
        self.state.dest_direction = self.cd[dest_index]

        self.set_message("Say 'I turn left.'")

    @on_state_changed(lambda ws, ts: ws.learner_direction == ts.dest_direction)
    def on_turned(self, event):
        self.set_reward(1)


class TurnRightTask(Task):
    def __init__(self, world):
        super(TurnRightTask, self).__init__(max_time=1000, world=world)
        self.cd = ['north', 'east', 'south', 'west']

    @on_start()
    def on_start(self, event):
        self.state.init_direction = self.get_world().state.learner_direction
        dest_index = ((self.cd.index(self.state.init_direction)) + 1) % 4
        self.state.dest_direction = self.cd[dest_index]

        self.set_message("Say 'I turn right.'")

    @on_state_changed(lambda ws, ts: ws.learner_direction == ts.dest_direction)
    def on_turned(self, event):
        self.set_reward(1)


class LookAroundTask(Task):
    def __init__(self, world):
        super(LookAroundTask, self).__init__(max_time=1000, world=world)

    @on_start()
    def on_start(self, event):
        self.set_message("Look around.")

    @on_message(u"I look.")
    def on_message(self, event):
        self.set_reward(1)


class PickAnApple(Task):
    def __init__(self, world):
        super(PickAnApple, self).__init__(max_time=10000, world=world)

    @on_ended()
    def cleanup(self, event):
        # remove the objects that were laid by this task
        # (the apple may not be there anymore, but it doesn't matter)
        self.get_world().remove_entity(self.block_pos)
        self.get_world().remove_entity(self.apple_pos)

    @on_start()
    def on_start(self, event):
        d = 2
        self.state.starting_apples = \
            self.get_world().state.learner_inventory['apple']
        # drop an apple
        self.apple_pos = self.get_world().state.learner_pos + Span(
            random.randint(-d, d), random.randint(-d, d))
        self.get_world().put_entity(self.apple_pos, 'apple', True, True)
        # drop an untraversable block
        # drop an apple
        self.block_pos = self.get_world().state.learner_pos + Span(
            random.randint(-d, d), random.randint(-d, d))
        if self.block_pos == self.apple_pos:
            self.block_pos = self.block_pos + Span(0, 1)
        self.get_world().put_entity(self.block_pos, 'block', False, False)
        self.set_message("Pick up an apple.")

    @on_state_changed(lambda ws, ts: ws.learner_inventory['apple'] >
                      ts.starting_apples)
    def on_apple_picked(self, event):
        self.set_reward(1, 'Enjoy!')


class UnicodeTask(Task):
    def __init__(self):
        super(UnicodeTask, self).__init__(max_time=1000)

    @on_start()
    def on_start(self, event):
        self.set_message('a in Hebrew is א. How do you say a in Hebrew?')

    # on non-silent character
    @on_message(u"א$")
    def on_message(self, event):
        self.set_reward(1, "Correct!")

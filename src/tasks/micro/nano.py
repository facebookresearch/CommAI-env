from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from core.task import on_start, on_message, on_timeout, on_output_message, Task  # , on_sequence

# The following tasks us the following bit-based vocabulary:
# stay_quiet 01
# space 00
# period 10
# say 11

# in task0, the learner must only produce the 0 bit until the end of the task
class Task0(Task):
    def __init__(self):
        super(Task0, self).__init__(
            max_time=1000)

    @on_start()
    def give_instructions(self, event):
        self.set_message('011000')

    @on_output_message(r'1000')
    def reward_at_end(self, event):
        self.set_reward(1)

    @on_message(r'1')
    def punish_not_quiet(self, event):
        self.set_reward(-1)

# in task1, the learner must produce 1 right after the environment stops speaking
# (and 0 while env is talking)
class Task1(Task):
    def __init__(self):
        super(Task1, self).__init__(
            max_time=1000)

    @on_start()
    def give_instructions(self, event):
        self.finished_talking=False
        self.set_message('1111000')

    @on_output_message(r'1000')
    def set_finished_talking_flag(self, event):
        self.finished_talking=True

    @on_message(r'.')
    def check_right_response(self, event):
        if event.is_message('1'):
            if (self.finished_talking):
                self.set_reward(1)
            else:
                self.set_reward(-1)
        elif (self.finished_talking):
            self.set_reward(-1)

# task11 is like task1, but not the learner must produce a 11 bit sequence
class Task11(Task):
    def __init__(self):
        super(Task11, self).__init__(
            max_time=1000)

    @on_start()
    def give_instructions(self, event):
        self.finished_talking=False
        self.learner_turn_counter=0
        self.set_message('11111000')

    @on_output_message(r'1000')
    def set_finished_talking_flag(self, event):
        self.finished_talking=True

    @on_message(r'.')
    def check_right_response(self, event):
        if event.is_message('1'):
            if (self.finished_talking):
                if (self.learner_turn_counter==0):
                    self.learner_turn_counter += 1
                else:
                    self.set_reward(1)
            else:
                self.set_reward(-1)
        elif (self.finished_talking):
            self.set_reward(-1)

# task10 is like task11, but not the learner must produce a 10 bit sequence
class Task10(Task):
    def __init__(self):
        super(Task10, self).__init__(
            max_time=1000)

    @on_start()
    def give_instructions(self, event):
        self.finished_talking=False
        self.learner_turn_counter=0
        self.set_message('11101000')

    @on_output_message(r'1000')
    def set_finished_talking_flag(self, event):
        self.finished_talking=True

    @on_message(r'.')
    def check_right_response(self, event):
        if event.is_message('1'):
            if (self.finished_talking and self.learner_turn_counter==0):
                    self.learner_turn_counter += 1
            else:
                self.set_reward(-1)
        elif (self.finished_talking):
            if (self.learner_turn_counter>0):
                self.set_reward(1)
            else:
                self.set_reward(-1)

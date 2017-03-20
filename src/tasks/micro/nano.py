from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from core.task import on_start, on_message, on_timeout, on_output_message, Task

# The following tasks us the following bit-based vocabulary:
# stay_quiet 01
# space 00
# period 10
# say 11

default_patient = False
class NanoTask(Task):
    def __init__(self, max_time=1000, patient=default_patient):
        super(NanoTask, self).__init__(
            max_time=max_time)
        self.patient = patient

    def get_default_output(self):
        # Pad with 0s at the end
        return '0'

    @on_start()
    def reset_received_reward(self, event):
        self.received_reward = False

    def set_reward(self, reward):
        if self.patient:
            if not self.received_reward:
                self.received_reward = reward
        else:
            super(NanoTask, self).set_reward(reward)

    @on_timeout()
    def on_timeout(self, timeout):
        if self.patient:
            assert self.received_reward
            # import pdb; pdb.set_trace()
            super(Task, self).set_reward(self.received_reward)

# in task0, the learner must only produce the 0 bit until the end of the task
class Task0(NanoTask):
    def __init__(self, patient=default_patient):
        super(Task0, self).__init__(
            max_time=6, patient=patient)

    @on_start()
    def give_instructions(self, event):
        self.set_message('011000')

    @on_output_message(r'1000')
    def reward_at_end(self, event):
        self.finished_talking = True
        self.set_reward(1)

    @on_message(r'1')
    def punish_not_quiet(self, event):
        self.set_reward(-1)


# in task1, the learner must produce 1 right after the environment stops speaking
# (and 0 while env is talking)
class Task1(NanoTask):
    def __init__(self, patient=default_patient):
        super(Task1, self).__init__(
            max_time=8, patient=patient)

    @on_start()
    def give_instructions(self, event):
        self.finished_talking = False
        self.set_message('1111000')

    @on_output_message(r'1000')
    def set_finished_talking_flag(self, event):
        self.finished_talking = True

    @on_message(r'.')
    def check_right_response(self, event):
        if event.is_message('1'):
            if (self.finished_talking):
                self.set_reward(1)
            else:
                self.set_reward(-1)
        elif self.finished_talking:
            self.set_reward(-1)


# task11 is like task1, but not the learner must produce a 11 bit sequence
class Task11(NanoTask):
    def __init__(self, patient=default_patient):
        super(Task11, self).__init__(
            max_time=10, patient=patient)

    @on_start()
    def give_instructions(self, event):
        self.finished_talking = False
        self.learner_turn_counter = 0
        self.set_message('11111000')

    @on_output_message(r'1000')
    def set_finished_talking_flag(self, event):
        self.finished_talking = True

    @on_message(r'.')
    def check_right_response(self, event):
        if event.is_message('1'):
            if (self.finished_talking):
                if (self.learner_turn_counter == 0):
                    self.learner_turn_counter += 1
                else:
                    self.set_reward(1)
            else:
                self.set_reward(-1)
        elif (self.finished_talking):
            self.set_reward(-1)


# task10 is like task11, but not the learner must produce a 10 bit sequence
class Task10(NanoTask):
    def __init__(self, patient=default_patient):
        super(Task10, self).__init__(
            max_time=10, patient=patient)

    @on_start()
    def give_instructions(self, event):
        self.finished_talking = False
        self.learner_turn_counter = 0
        self.set_message('11101000')

    @on_output_message(r'1000')
    def set_finished_talking_flag(self, event):
        self.finished_talking = True

    @on_message(r'.')
    def check_right_response(self, event):
        if event.is_message('1'):
            if (self.finished_talking and self.learner_turn_counter == 0):
                    self.learner_turn_counter += 1
            else:
                self.set_reward(-1)
        elif (self.finished_talking):
            if (self.learner_turn_counter > 0):
                self.set_reward(1)
            else:
                self.set_reward(-1)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from core.task import Task, on_start, on_message, on_timeout, on_output_message
from tasks.competition.base import BaseTask
import logging
import random
import math

# TODO
# Require full stop at end
# Refactor all simple tasks into seqmantask where you just write
#   the get response string and max time and proposed string hooks
# Generate the classes and compositions programmatically

# The small composition task use the following vocabulary:
# V reverse function
# P repeat function
# O rotate function
# C concatenate function
# 0/1 alphabet for argument strings

# constant to keep same input string length across tasks
max_string_length = 12


def to_odd(n):
    return (math.floor(n / 2) * 2) + 1


def to_even(n):
    return (math.floor(n / 2) * 2) + 2


def repeat_sequence(repetitions,sequence):
    repeated_sequence = ""
    for i in range(repetitions):
        repeated_sequence += sequence
    return repeated_sequence


def reverse_sequence(sequence):
    return sequence[::-1]


def rotate_sequence(steps,sequence):
    string_length = len(sequence)
    if (steps >= string_length):
        steps = steps % string_length
    if (steps<0):
        raise ValueError('rotation step count (' + str(steps) + ') must be non-negative')
    rotated_sequence = ""
    for i in range(string_length):
        if (i >= steps):
            rotated_sequence += sequence[i - steps]
        else:
            rotated_sequence += sequence[i - steps + string_length]
    return rotated_sequence


class SeqManTask(BaseTask):
    def __init__(self, max_string_length=6, world=None, max_time=0):
        super(SeqManTask, self).__init__(world=world, max_time=0)
        self.odd = None
        self.max_string_length = max_string_length

    def get_random_01_sequence(self, L):
        maxL = random.randint(1, L)
        if self.odd is not None:
            maxL = int(to_odd(maxL)if self.odd else to_even(maxL))

        random_string = ""
        for _ in range(maxL):
            random_string += str(random.randrange(2))
        return random_string

    @on_message(r".$")
    def check_response(self, event):
        if (self.response_check):
#            self.logger.info("current counter:" + str(self.response_counter))
            if (event.is_message(self.response_string[self.response_counter])):
                if (self.response_counter == (len(self.response_string) - 1)):
                    self.set_reward(1)
                else:
                    self.response_counter = self.response_counter + 1
            else:
                self.set_reward(-1)

    @on_output_message(r'\.$')
    def set_response_check(self, event):
        self.response_check = True
        self.response_counter = 0

    def set_response_string(self, rstr, msg):
        if not rstr.endswith('.'):
            rstr += '.'
        print('message', msg)
        print('response', rstr)
        self.response_string = rstr
        self._max_time = 8 * len(msg) + 8 * len(rstr) - 8


class ReverseXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ReverseXTask, self).__init__(max_string_length=max_string_length,
                                            world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        message = "V" + proposed_string + "."
        self.set_message(message)
        self.set_response_string(reverse_sequence(proposed_string), message)


class OddReverseXTask(ReverseXTask):
    def __init__(self, max_string_length=6, world=None):
        super(OddReverseXTask, self).__init__(max_string_length=max_string_length,
                                              world=world)
        self.odd = True


class EvenReverseXTask(ReverseXTask):
    def __init__(self, max_string_length=6, world=None):
        super(EvenReverseXTask, self).__init__(max_string_length=max_string_length,
                                               world=world)
        self.odd = False


class RepeatNXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None, n_odd=None):
        super(RepeatNXTask, self).__init__(max_string_length=max_string_length,
                                           world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)
        self.n_odd = n_odd

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        repetitions = random.randint(1, 5)

        if self.n_odd is not None:
            repetitions = int(to_odd(repetitions) if self.n_odd
                                                    else to_even(repetitions))

        message = "P" + str(repetitions) + "," + proposed_string + "."
        self.set_message(message)
        self.set_response_string(
            repeat_sequence(repetitions, proposed_string), message)


class OddRepeatNXTask(RepeatNXTask):
    def __init__(self, max_string_length=6, world=None):
        super(OddRepeatNXTask, self).__init__(max_string_length=max_string_length,
                                              world=world, n_odd=True)


class EvenRepeatNXTask(RepeatNXTask):
    def __init__(self, max_string_length=6, world=None):
        super(EvenRepeatNXTask, self).__init__(max_string_length=max_string_length,
                                                world=world, n_odd=False)


class RotateRXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None, n_odd=None):
        super(RotateRXTask, self).__init__(max_string_length=max_string_length,
                                            world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)
        self.n_odd = n_odd

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        steps = random.randint(1, len(proposed_string))

        if self.n_odd is not None:
            steps = int(to_odd(steps) if self.n_odd else to_even(steps))

        message = "O" + str(steps) + "," + proposed_string + "."
        self.set_message(message)
        self.set_response_string(rotate_sequence(steps, proposed_string), message)


class OddRotateRXTask(RotateRXTask):
    def __init__(self, max_string_length=6, world=None):
        super(OddRotateRXTask, self).__init__(max_string_length=max_string_length,
                                              world=world, n_odd=True)


class EvenRotateRXTask(RotateRXTask):
    def __init__(self, max_string_length=6, world=None):
        super(EvenRotateRXTask, self).__init__(max_string_length=max_string_length,
                                               world=world, n_odd=False)


class ConcatenateXYTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ConcatenateXYTask, self).__init__(max_string_length=max_string_length,
                                                world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string_1 = self.get_random_01_sequence(self.max_string_length)
        proposed_string_2 = self.get_random_01_sequence(self.max_string_length)
        message = "C" + proposed_string_1 + "," + proposed_string_2 + "."
        self.set_message(message)
        self.set_response_string(proposed_string_1 + proposed_string_2, message)


################################################################################
# Composed tasks from here...

class ReverseRepeatNXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ReverseRepeatNXTask, self).__init__(max_string_length=max_string_length,
                                                  world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        repetitions = random.randint(1,4)
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        message = "VP" + str(repetitions) + "," + proposed_string + "."
        self.set_message(message)
        self.set_response_string(reverse_sequence(repeat_sequence(repetitions,proposed_string)), message)


class ReverseRotateRXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ReverseRotateRXTask, self).__init__(max_string_length=max_string_length,
                                                  world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        steps = random.randint(1, len(proposed_string))
        message = "VO" + str(steps) + "," + proposed_string + "."
        self.set_message(message)
        self.set_response_string(reverse_sequence(rotate_sequence(steps, proposed_string)), message)


class ReverseConcatenateXYTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ReverseConcatenateXYTask, self).__init__(max_string_length=max_string_length,
                                                       world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string_1 = self.get_random_01_sequence(self.max_string_length)
        proposed_string_2 = self.get_random_01_sequence(self.max_string_length)
        message = "VC" + proposed_string_1 + "," + proposed_string_2 + "."
        self.set_message(message)
        self.set_response_string(reverse_sequence(proposed_string_1 + proposed_string_2), message)


class RepeatNReverseXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(RepeatNReverseXTask, self).__init__(max_string_length=max_string_length,
                                                  world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        repetitions = random.randint(1,4)
        message = "P" + str(repetitions) + ",V" + proposed_string + "."
        self.set_message(message)
        self.set_response_string(reverse_sequence(repeat_sequence(
                                repetitions, proposed_string)), message)


class RepeatNRotateRXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(RepeatNRotateRXTask, self).__init__(max_string_length=max_string_length,
                                                  world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        repetitions = random.randint(1, 4)
        steps = random.randint(1, len(proposed_string))
        message = "P" + str(repetitions) + ",O" + str(steps) + "," + proposed_string + "."
        self.set_message(message)
        self.set_response_string(repeat_sequence(repetitions, rotate_sequence(steps, proposed_string)), message)


class RepeatNConcatenateXYTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(RepeatNConcatenateXYTask, self).__init__(max_string_length=max_string_length,
                                                       world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string_1 = self.get_random_01_sequence(self.max_string_length)
        proposed_string_2 = self.get_random_01_sequence(self.max_string_length)
        repetitions = random.randint(1,4)
        message = "P" + str(repetitions) + ",C" + proposed_string_1 + "," + proposed_string_2 + "."
        self.set_message(message)
        self.set_response_string(repeat_sequence(repetitions, proposed_string_1 + proposed_string_2), message)


class RotateRReverseXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(RotateRReverseXTask, self).__init__(max_string_length=max_string_length,
                                                  world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        steps = random.randint(1,len(proposed_string))
        message = "O" + str(steps) + ",V" + proposed_string + "."
        self.set_message(message)
        self.set_response_string(rotate_sequence(steps,reverse_sequence(proposed_string)), message)


class RotateRRepeatNXTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(RotateRRepeatNXTask, self).__init__(max_string_length=max_string_length,
                                                   world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string = self.get_random_01_sequence(self.max_string_length)
        repetitions = random.randint(1,4)
        steps = random.randint(1,len(proposed_string)*repetitions)
        message = "O" + str(steps) + ",P" + str(repetitions) + "," + proposed_string + "."
        self.set_message(message)
        self.set_response_string(rotate_sequence(steps,repeat_sequence(repetitions,proposed_string)), message)


class RotateRConcatenateXYTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(RotateRConcatenateXYTask, self).__init__(max_string_length=max_string_length,
                                                        world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string_1 = self.get_random_01_sequence(self.max_string_length)
        proposed_string_2 = self.get_random_01_sequence(self.max_string_length)
        steps = random.randint(1,len(proposed_string_1)+len(proposed_string_2))
        message = "O" + str(steps) + ",C" + proposed_string_1 + "," + proposed_string_2 + "."
        self.set_message(message)
        self.set_response_string(rotate_sequence(steps,proposed_string_1+proposed_string_2), message)


class ConcatenateReverseXReverseYTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ConcatenateReverseXReverseYTask, self).__init__(max_string_length=max_string_length,
                                                              world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string_1 = self.get_random_01_sequence(self.max_string_length)
        proposed_string_2 = self.get_random_01_sequence(self.max_string_length)
        message = "CV" + proposed_string_1 + ",V" + proposed_string_2 + "."
        self.set_message(message)
        self.set_response_string(reverse_sequence(proposed_string_1) + reverse_sequence(proposed_string_2), message)


class ConcatenateRepeatNXRepeatMYTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ConcatenateRepeatNXRepeatMYTask, self).__init__(max_string_length=max_string_length,
                                                              world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string_1 = self.get_random_01_sequence(self.max_string_length)
        repetitions_1 = random.randint(1,4)
        proposed_string_2 = self.get_random_01_sequence(self.max_string_length)
        repetitions_2 = random.randint(1,4)
        message = "CP" + str(repetitions_1) + "," + proposed_string_1 + ",P" + \
                str(repetitions_2) + "," + proposed_string_2 + "."
        self.set_message(message)
        self.set_response_string(
            repeat_sequence(repetitions_1, proposed_string_1) +
            repeat_sequence(repetitions_2, proposed_string_2),
            message)


class ConcatenateRotateRXRotateSYTask(SeqManTask):
    def __init__(self, max_string_length=6, world=None):
        super(ConcatenateRotateRXRotateSYTask, self).__init__(max_string_length=max_string_length,
                                                              world=world, max_time=0)
        # NB: max_time will be dynamically adjusted below
#        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.response_check = False
        proposed_string_1 = self.get_random_01_sequence(self.max_string_length)
        steps_1 = random.randint(1,len(proposed_string_1))
        proposed_string_2 = self.get_random_01_sequence(self.max_string_length)
        steps_2 = random.randint(1,len(proposed_string_2))
        message = "CO" + str(steps_1) + "," + proposed_string_1 + ",O" + \
                str(steps_2) + "," + proposed_string_2 + "."
        self.set_message(message)
        self.set_response_string(
            rotate_sequence(steps_1, proposed_string_1) +
            rotate_sequence(steps_2, proposed_string_2),
            message)

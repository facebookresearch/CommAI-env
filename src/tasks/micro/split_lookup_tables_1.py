from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from core.task import on_start, on_message, on_timeout, on_output_message
from tasks.competition.base import BaseTask
import logging
import random
import math
import string

# NB: wit this random seed, always the same takss will be generated!
task_seed = 1111
random.seed(task_seed)

logger = logging.getLogger(__name__)
logger.info("Lookup table task seed: {}".format(task_seed))


# This module instantiates a set of atomic and composed lookup table
# tasks.

# Each atomic lookup table task maps a binary string of length L to
# another string of the same length. The mappings are bijective, that
# is, each input string is associated to one and only one output
# string. Moreover, we guarantee that no 2 atomic tasks of the same length
# instantiate the same bijection.

# The maximum string length for which tasks are generated is
# controlled by the LONGEST_STRING_LENGTH constant--see below where it
# is defined for constraints to be respected when setting it. We set
# the minimum string length to 2.

# The constant NUMBER_OF_TASKS determines how many tasks are generated
# for each string length: again, see below for constraints on its
# range.

# Finally, the MAX_COMPOSITION_COUNT function determines the maximum
# sequence of composition applications that is considered when
# generating all possible compositions.

# From the point of view of the learner, tasks are letter-coded (with
# the idea that letters are reserved for task descriptions, digits for
# the actual task arguments). An atomic task begins with a task
# description in the following format. The task type is denoted by the
# string n (for non-composed). The latter is followed by string length
# which is denoted by a letter, starting with a for the minimum length
# of 2, b for 3, etc. This is followed by a letter denoting the task
# number (a for the first task, b for the second etc.). The
# description is ended by a colon, followed by the actual input
# string, and a period. For example:

# nbb:100.

# is an instance of the second atomic task of string length 3.

# There are two kinds of composed tasks. In functionally composed
# tasks, each lookup task in the specified sequence is applied to the
# output of the previous task. In concatenative composition, each
# lookup in the specified task sequence is applied to the task input,
# and the outputs are concatenated.

# Composed task naming follows similar conventions to those of atomic
# tasks, with f and c as prefixes for functional and concatenative
# tasks, respectively, and the string length code followed by the
# codes of the sequence of tasks in the composition. For example:

# faaba:01.

# is an instance of a functional length-2 task composed of the
# sequence of atomic length-2 tasks 1, 2 and 1 again.

# caaba:01.

# is the corresponding concatenative task.

# The tasks are given arguably more human-readabe names for listing
# them in configuration files, according to the following conventions.

# Atomic task names are prefixed by the string "LookupTask" followed
# by RL (where L stands for string length), followed by DT (where T is
# the task code). For example, the second atomic task of string length 2 is
# called LookupTaskR2D2 (incidentally, the possibility of naming a
# task after R2D2 is what motivated the naming conventions).

# Composed tasks use the same naming conventions, except that now the
# prefix will be FuncLookupTask or CatLookupTask (depending on the
# type of composition), and that T will now be and
# underscore-delimited sequence of tasks, in order of
# application). For example, FuncLookupTaskR3D1_1_4 is the
# functionally composed task of string length 3 given by applying the
# length-3 task number 1 to the input, then again the same task, and
# then the length-3 task number 4. The equivalent concatenative task
# is named CatLookupTaskR3D1_1_4

# In this version of the lookup tasks, each composed task has a "test" counterpart. Two
# random input sequences are reserved for the latter. For example, it
# might be that, for FuncLookupTaskR2D2_1, the input strings 00 and 10 are randomly
# selected as the ones for testing. This means that two tasks are automatically
# generated, one called FuncLookupTaskR2D2_1, whose instances will only have
# inputs 01 and 11; and FuncLookupTestTaskR2D2_1, whose inputs wll be 00 and 10.
# Note that the split is reflected in the human-readable naming of the tasks, but
# from the point of view of the learner the two tasks are indistinguishable.

# Positive reward is passed to the learner when it finishes a task
# successfully. As soon as the learner makes a mistake, it gets
# negative reward and the task is ended.

# More precisely, what the learner says while the environment/teacher
# is presenting the task is ignored. As soon as the environment
# produces the end-of-message symbol (period) the learner must produce
# the response. The learner gets no reward at each step in which it
# produces the right token, and +1 reward when it completes the right
# response. If the learner produces a wrong token, it gets -1 reward
# and the episode ends immediately. The learner can also "buy" time,
# by producing a maximum of MAX_PONDERING PONDERING_TOKENs (see below
# for how these variables are currently set and to change
# them). During pondering, the learner gets no reward. Note that, as
# soon as the learner produces a non-pondering token, it can no longer
# revert to pondering.

# CONSTANTS SET HERE

# what's the longest string length we will consider
LONGEST_STRING_LENGTH = 3
# the value above should not be larger than 53, as we are using the
# ASCII letters (lower and upper case) to label the tasks by length
# (and we start counting from 2)

# how many tasks do we want to generate for each string length
NUMBER_OF_TASKS = 8
# NB: value above cannot be larger than 24, or we won't be able to generate
# enough distinct tasks for the 2-length case
# NB: a fortiori, it should not be larger than 52, but if the
# constraint above becomes obsolete, still the value should not be
# larger than 52, as we use the ASCII letters (lower and upper case)
# to label the task variants

# how many compositions are going to be maximally performed
MAX_COMPOSITION_COUNT = 2
# note that a composition count of 0 corresponds to atomic tasks only,
# 1 to compositions of two tasks, etc

# the following constants regulate tolerance for a "pondering" phase
# in which the learner is allowed to produce a "silence" token
PONDERING_TOKEN = "p"
MAX_PONDERING = 5


# generating a dictionary of distinct permutations for each possible
# length--we do this before generating the tasks because the atomic
# and composed tasks should share the same permutations
shuffled_index_repository = {}
for string_length in range(2, LONGEST_STRING_LENGTH + 1):
    number_of_strings = 2**string_length
    list_of_seen_shuffles = []
    shuffled_index_repository[string_length] = {}
    temp_shuffle = list(range(number_of_strings))
    max_tasks = min(math.factorial(number_of_strings), NUMBER_OF_TASKS)
    for current_task_id in range(1, max_tasks + 1):
        random.shuffle(temp_shuffle)
        while (temp_shuffle in list_of_seen_shuffles):
            random.shuffle(temp_shuffle)
        list_of_seen_shuffles.append(temp_shuffle[:])
        shuffled_index_repository[string_length][current_task_id] = temp_shuffle[:]


# the following class is implementing the impatient teacher--it should
# be moved somewhere else, as it shared with other tasks (although for
# the time being the pondering option is only considered for these
# tasks)
class SeqManTask(BaseTask):
    def __init__(self, world=None, max_time=0):
        super(SeqManTask, self).__init__(world=world, max_time=0)

    @on_timeout()
    def punish_timeout(self, event):
        self.set_reward(-1)

    @on_message(r".$")
    def check_response(self, event):
        if (self.response_check):
            # self.logger.info("current counter:" + str(self.response_counter))
            if (event.is_message(self.response_string[self.response_counter])):
                if (self.response_counter == (len(self.response_string) - 1)):
                    self.set_reward(1)
                else:
                    self.produced_non_pondering_token = True
                    self.response_counter = self.response_counter + 1
            else:
                if (not (event.is_message(PONDERING_TOKEN) and not
                            self.produced_non_pondering_token)):
                    self.set_reward(-1)

    @on_output_message(r'\.$')
    def set_response_check(self, event):
        self.response_check = True
        self.produced_non_pondering_token = False
        self.response_counter = 0

    def set_response_string(self, rstr, msg):
        if not rstr.endswith('.'):
            rstr += '.'
        # print('message', msg)
        # print('response', rstr)
        self.response_string = rstr
        #        self._max_time = 8 * len(msg) + 8 * len(rstr) + 8 * MAX_PONDERING - 8
        self._max_time = len(msg) + len(rstr) + MAX_PONDERING


# template for simple or composed lookup tasks
class BaseLookupTask(SeqManTask):
    def __init__(self, world=None):
        super(BaseLookupTask, self).__init__(world=world, max_time=0)
        random.seed()

    def generate_fixed_length_binary_string(self, fixed_length, input_integer):
        return bin(input_integer)[2:].zfill(fixed_length)

    def get_value_string(self, key_code):
        ''' Returns the target value string for the given key_code '''

        output_values = [key_code]
        composition_count = len(self.tasks_to_be_composed) - 1

        for i in range(composition_count + 1):
            task_number = self.tasks_to_be_composed[i]
            # If the compositiona type is functional or procedural, the key code
            # for current task is the output of the last task, otherwise it's
            # the selected_index.
            if (self.comp_type == "functional" or
                    self.comp_type == "procedural"):
                key_code = output_values[-1]
            else:
                key_code = output_values[0]
            output_values.append(
                shuffled_index_repository[self.string_length][task_number][key_code])

        # If the composition type is functional, the expected string is the last
        # output value, otherwise it's a concatenation of all the output values.
        if self.comp_type == "functional":
            value_string = self.generate_fixed_length_binary_string(
                self.string_length, output_values[-1])
        else:
            output_strings = [self.generate_fixed_length_binary_string(
                self.string_length, e) for e in output_values[1:]]
            value_string = "".join(output_strings)

        return value_string

    def get_task_name(self):
        ''' Returns the task name, e.g. "nba"'''

        # Concatenate the task codes for a final task name.
        composition_count = len(self.tasks_to_be_composed) - 1
        task_name = self.comp_type[0].upper() + \
                    string.ascii_uppercase[self.string_length - 1]
        for i in range(composition_count + 1):
            task_number = self.tasks_to_be_composed[i]
            task_name += string.ascii_letters[task_number - 1]

        return task_name

    def get_next_episode(self):
        # string_length assumed
        number_of_strings = 2**self.string_length

        # Select the index (row in the mapping table)
        selected_index = random.randint(0, number_of_strings - 1)
        while ((self.test_case and not(selected_index in self.test_index_set)) or
                (not(self.test_case) and selected_index in self.test_index_set)):
            selected_index = random.randint(0, number_of_strings - 1)

        # Convert the selected index into a binary string
        key_string = self.generate_fixed_length_binary_string(
            self.string_length, selected_index)

        # Generate the final message
        message = self.get_task_name() + ':' + key_string + "."

        # Lookup & generate (in case of compositions) the target value string
        # for the selected index
        value_string = self.get_value_string(selected_index)

        return message, value_string

    @on_start()
    def give_instructions(self, event):
        self.response_check = False

        message, value_string = self.get_next_episode()

        self.set_message(message)
        self.set_response_string(value_string, message)


# looping over compositions, tasks and string lengths
task_combinations = []
i = 0
while (i <= MAX_COMPOSITION_COUNT):

    # Generate all possible task combinations of a given length i
    task_combinations.append([])
    for current_task in range(1, NUMBER_OF_TASKS + 1):
        if i == 0:
            task_combinations[i].append([current_task])
        else:
            for task_combination in task_combinations[i - 1]:
                enlarged_task_combination = task_combination[:]
                enlarged_task_combination.append(current_task)
                task_combinations[i].append(enlarged_task_combination)

    # For each task combination, generate the respective task classes
    for task_combination in task_combinations[i]:
        for string_length in range(1, LONGEST_STRING_LENGTH + 1):
            # For one task combinations, create an atomic lookup task
            if i == 0:
                # we generate the non-composed task
                comp_type = "none"
                name = "LookupTaskR{}D{}".format(string_length, task_combination[0])
                LookupTask = type(name, (BaseLookupTask,), {
                    "tasks_to_be_composed": task_combination,
                    "string_length": string_length,
                    "comp_type": comp_type,
                    "test_case": False,
                    "test_index_set": set()})
                globals()[name] = LookupTask
            else:
                # the composed tasks
                # picking two random indices that will be left out for the test
                # version of the task
                test_indices = list(range(2**string_length))
                random.shuffle(test_indices)
                test_index_set = set(test_indices[:2])

                # proper functional composition
                comp_type="functional"
                name = "FuncLookupTaskR{}D{}".format(
                    string_length, '_'.join(str(e) for e in task_combination))
                FuncLookupTask = type(name, (BaseLookupTask,), {
                    "tasks_to_be_composed": task_combination,
                    "string_length": string_length,
                    "comp_type": comp_type,
                    "test_case": False,
                    "test_index_set": test_index_set})
                globals()[name] = FuncLookupTask
                name = "FuncLookupTestTaskR{}D{}".format(
                    string_length, '_'.join(str(e) for e in task_combination))
                FuncLookupTestTask = type(name, (BaseLookupTask,), {
                    "tasks_to_be_composed": task_combination,
                    "string_length": string_length,
                    "comp_type": comp_type,
                    "test_case": True,
                    "test_index_set": test_index_set})
                globals()[name] = FuncLookupTestTask

                # concatenation
                comp_type="concatenation"
                name = "CatLookupTaskR{}D{}".format(
                    string_length, '_'.join(str(e) for e in task_combination))
                CatLookupTask = type(name, (BaseLookupTask,), {
                    "tasks_to_be_composed": task_combination,
                    "string_length": string_length,
                    "comp_type": comp_type,
                    "test_case": False,
                    "test_index_set": test_index_set})
                globals()[name] = CatLookupTask
                name = "CatLookupTestTaskR{}D{}".format(
                    string_length, '_'.join(str(e) for e in task_combination))
                CatLookupTestTask = type(name, (BaseLookupTask,), {
                    "tasks_to_be_composed": task_combination,
                    "string_length": string_length,
                    "comp_type": comp_type,
                    "test_case": True,
                    "test_index_set": test_index_set})
                globals()[name] = CatLookupTestTask

                # functional composition with intermediate results
                comp_type = "procedural"
                name = "ProcLookupTaskR{}D{}".format(
                    string_length, '_'.join(str(e) for e in task_combination))
                ProcLookupTask = type(name, (BaseLookupTask,), {
                    "tasks_to_be_composed": task_combination,
                    "string_length": string_length,
                    "comp_type": comp_type,
                    "test_case": False,
                    "test_index_set": test_index_set})
                globals()[name] = ProcLookupTask
                name = "ProcLookupTestTaskR{}D{}".format(
                    string_length, '_'.join(str(e) for e in task_combination))
                ProcLookupTestTask = type(name, (BaseLookupTask,), {
                    "tasks_to_be_composed": task_combination,
                    "string_length": string_length,
                    "comp_type": comp_type,
                    "test_case": True,
                    "test_index_set": test_index_set})
                globals()[name] = ProcLookupTestTask

    i += 1

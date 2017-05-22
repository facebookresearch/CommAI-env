from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from core.task import Task, on_start, on_message, on_timeout, on_output_message
from tasks.competition.base import BaseTask
import logging
import random
import math
import string

# This module instantiates a set of atomic and composed lookup table tasks.

# Each atomic lookup table task maps a binary string of length L to
# another string of the same length. The mappings are bijective, that
# is, each input string is associated to one and only one output
# string. Moreover, we guarantee that no 2 tasks of the same length
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
# description in the following format. The task string length is
# denoted by a letter, starting at a for the minimum length of 2, b
# for 3, etc. This is followed by a letter denoting the task number (a
# for the first task, b for the second etc.). The description is ended
# by a colon, followed by the actual input string. For example:

# bb:100

# is an instance of the second task of string length 3.

# Composed task naming follows similar conventions, with the string
# length code followed by the codes of the sequence of tasks in the
# composition. For example:

# aaba:01

# is an instance of a length-2 task composed of the sequence of atomic
# length-2 tasks 1, 2 and 1 again.

# The tasks are given arguably more human-readabe names for listing
# them in configuration files, according to the following conventions.

# All task names are prefixed by the string "LookupTask" followed by
# RL (where L stands for string length), followed by DT (where T is an
# underscore-delimited sequence of tasks, in order of
# application). For example, the second task of string length 2 is
# called LookupTaskR2D2 (incidentally, the possibility of naming a
# task after R2D2 is what motivated the naming conventions).
# LookupCompTaskR3D1_1_4 is the composed task of string length 3 given
# by applying the length-3 task number 1, then again the same task,
# and then the length-3 task number 4.


# what's the longest string length we will consider
LONGEST_STRING_LENGTH=8
# the value above should not be larger than 53, as we are using the
# ASCII letters (lower and upper case) to label the tasks by length
# (and we start counting from 2)

# how many tasks do we want to generate for each string length
NUMBER_OF_TASKS = 4
# NB: value above cannot be larger than 24, or we won't be able to generate enough distinct
# tasks for the 2-length case
# NB: a fortiori, it should not be larger than 52, but if the
# constraint above becomes obsolete, still the value should not be
# larger than 52, as we use the ASCII letters (lower and upper case)
# to label the task variants

# how many compositions are going to be maximally performed
MAX_COMPOSITION_COUNT=2
# note that a composition count of 0 corresponds to atomic tasks only,
# 1 to compositions of two tasks, etc

# generating a dictionary of distinct permutations for each possible
# length--we do this before generating the tasks because the atomic
# and composed tasks should share the same permutations
shuffled_index_repository={}
for string_length in range(2,LONGEST_STRING_LENGTH+1):
    number_of_strings=2**string_length
    list_of_seen_shuffles = []
    shuffled_index_repository[string_length] = {}
    temp_shuffle = range(number_of_strings)
    for current_task_id in range(1,NUMBER_OF_TASKS+1):
        random.shuffle(temp_shuffle)
        while (temp_shuffle in list_of_seen_shuffles):
            random.shuffle(temp_shuffle)
        list_of_seen_shuffles.append(temp_shuffle[:])
        shuffled_index_repository[string_length][current_task_id]=temp_shuffle[:]


# the following class is implementing the impatient teacher--it should
# be moved somewhere else, as it shared with other tasks
class SeqManTask(BaseTask):
    def __init__(self, world=None, max_time=0):
        super(SeqManTask, self).__init__(world=world, max_time=0)

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

# template for simple or composed lookup tasks
class BaseLookupTask(SeqManTask):
    def __init__(self, world=None):
        super(BaseLookupTask, self).__init__(world=world, max_time=0)

    def generate_fixed_length_binary_string(self,fixed_length,input_integer):
        return bin(input_integer)[2:].zfill(fixed_length)

    @on_start()
    def give_instructions(self,event):
        self.response_check = False
        # string_length assumed
        number_of_strings = 2**self.string_length
        # tasks_to_be_composed list assumed
        composition_count = len(self.tasks_to_be_composed)-1
        task_name =  string.ascii_letters[self.string_length-2]
        key_code = random.randint(0,number_of_strings-1)
        next_key_code = key_code
        key_string = self.generate_fixed_length_binary_string(self.string_length,key_code)
        for i in range(composition_count+1):
            key_code = next_key_code
            task_number = self.tasks_to_be_composed[i]
            task_name += string.ascii_letters[task_number-1]
            next_key_code = shuffled_index_repository[self.string_length][task_number][key_code]
        value_string = self.generate_fixed_length_binary_string(self.string_length,next_key_code)
        task_name += ":"
        # debug
#        message = task_name + value_string + "_" + key_string + "."
        message = task_name + key_string + "."
        self.set_message(message)
        self.set_response_string(value_string, message)


# looping over compositions, tasks and string lengths
task_combinations = []
i=0
while (i<=MAX_COMPOSITION_COUNT):
    task_combinations.append([])
    for current_task in range(1,NUMBER_OF_TASKS+1):
        if i==0:
            task_combinations[i].append([current_task])
        else:
            for task_combination in task_combinations[i-1]:
                enlarged_task_combination = task_combination[:]
                enlarged_task_combination.append(current_task)
                task_combinations[i].append(enlarged_task_combination)
    for task_combination in task_combinations[i]:
        for string_length in range(2,LONGEST_STRING_LENGTH+1):
            name = "LookupTaskR" + str(string_length) + "D" + '_'.join(str(e) for e in task_combination)
            LookupTask = type(name,(BaseLookupTask,),{"tasks_to_be_composed":task_combination,"string_length":string_length})
            globals()[name]=LookupTask
    i+=1

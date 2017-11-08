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
from collections import defaultdict
import random


def check_intervals(I_s, I_b):
    """
    check if the interval I_s is within I_b
    """
    smaller, bigger = I_s
    if smaller >= I_b[0] and bigger <= I_b[1]:
        return True
    else:
        return False


def check_continuity(Intvs):
    """
    verify that there is continuity in the list Intvs
    """
    I1 = Intvs[:-1]
    I2 = Intvs[1:]
    continuous = True
    for (a, b) in zip(I1, I2):
        continuous = (eval(a)[-1] + 1 == eval(b)[0])
        if not(continuous):
            break
    return continuous


def dic_interval_task(intervals, tasks):
    '''
    Construct the dictionary {interval:[available_tasks]} for training
    and testing mode
    '''
    import itertools
    import collections
    # Create disjoint intervals (for each one we have a list of
    # available tasks)
    flat_intervals = list(set(list(itertools.chain(*intervals))))
    flat_intervals.sort()
    assert flat_intervals[0] == 0
    seperate_intervals = [[x, y] for x, y in  itertools.izip(flat_intervals, flat_intervals[1:])]
    task_intervals = collections.OrderedDict()
    for I in seperate_intervals:
        for count, task_interval in enumerate(intervals):
            if check_intervals(I, task_interval):
                if str(I) in task_intervals:
                    task_intervals[str(I)].append(tasks[count])
                else:
                    task_intervals[str(I)] = [tasks[count]]
    assert check_continuity(task_intervals.keys())
    return task_intervals


class RandomTaskScheduler:
    '''
    A Scheduler provides new tasks every time is asked.
    This is a random scheduler
    '''
    def __init__(self, tasks):
        self.tasks = tasks

    def get_next_task(self, train_mode=True):
        # pick a random task
        return random.choice(self.tasks)

    def step(self, reward, train_mode=True):
        # whatever
        pass


class SequentialTaskScheduler:
    '''
    A Scheduler provides new tasks every time is asked.
    This is a random scheduler
    '''
    def __init__(self, tasks):
        self.tasks = tasks
        self.i = 0

    def get_next_task(self, train_mode=True):
        # pick a random task
        ret = self.tasks[self.i]
        self.i = (self.i + 1) % len(self.tasks)
        return ret

    def step(self, reward, train_mode=True):
        # whatever
        pass


class IncrementalTaskScheduler:
    '''
    Switches to the next task type sequentially
    After the current task was successfully learned N times
    '''

    def __init__(self, tasks, success_threshold=2):
        self.tasks = tasks
        self.task_ptr = 0
        self.reward_count = 0
        self.success_threshold = success_threshold

    def get_next_task(self, train_mode=True):
        if self.reward_count == self.success_threshold:
            self.reward_count = 0
            self.task_ptr = (self.task_ptr + 1) % len(self.tasks)
        return self.tasks[self.task_ptr]

    def step(self, reward, train_mode=True):
        self.reward_count += reward

# TODO: Create a BatchedScheduler that takes as an argument another
#       scheduler and just repeats the given tasks N times.


class DependenciesTaskScheduler:
    '''
    Takes a dependency graph between the tasks and randomly allocates between
    the ones that are at the root, or are dependent on other tasks that
    have been solved (based on a threshold)
    '''

    def __init__(self, tasks, tasks_dependencies, unlock_threshold=10):
        '''
        Args:
            tasks: a list of Task objects
            tasks_dependencies: list of ordered pairs of Task objects (t1,t2)
                if t2 depends on t1 to be completed.
            unlock_threshold: total cumulative reward needed for a
                task to be considered solved.
        '''
        self.tasks = tasks
        # a dictionary containing rewards per task
        self.rewards = defaultdict(int)
        # saves the last task that has been given to the learner
        self.last_task = None
        self.unlock_threshold = unlock_threshold
        self.solved_tasks = set()
        self.tasks_dependencies = tasks_dependencies
        # set of the tasks that are available to the learner
        self.available_tasks = set()
        # initially these are the tasks that have no dependencies on them
        self.find_available_tasks()

    def get_next_task(self, train_mode=True):
        self.last_task = self.pick_new_task()
        return self.last_task

    def step(self, reward, train_mode=True):
        # remember the amount of times we have solved the task
        # using the name of the class to have a hashable value
        task_name = self.get_task_id(self.last_task)
        self.rewards[task_name] += reward
        if self.rewards[task_name] >= self.unlock_threshold:
            self.solved_tasks.add(task_name)
            # refresh the list of available tasks
            self.find_available_tasks()

    def get_task_id(self, task):
        return task.__class__.__name__

    def solved(self, task):
        return self.get_task_id(task) in self.solved_tasks

    def find_available_tasks(self):
        for t in self.tasks:
            task_available = True
            for t1, t2 in self.tasks_dependencies:
                if t2 == t and not self.solved(t1):
                    task_available = False
                    break
            if task_available:
                self.available_tasks.add(t)

    def pick_new_task(self):
        return random.sample(self.available_tasks, 1)[0]


class IntervalTaskScheduler:
    '''
    Switches to the next task type sequentially
    After the current task was successfully learned N times
    '''

    def __init__(self, tasks, intervals, tasks_test=None):
        '''
        Args:
            tasks: a list of Task objects
            intervals: list of intervals [i1...in] where ik = [jk1,jk2].
        '''
        self.tasks = tasks
        self.task_intervals = dic_interval_task(intervals, tasks)
        self.iterations = 0
        self.num_interval = 0
        self.find_available_tasks()

        self.tasks_test = tasks_test

    def get_next_task(self, train_mode=True):
        if train_mode:
            return random.choice(self.available_tasks)
        else:
            return random.choice(self.tasks_test)

    def step(self, reward, train_mode=True):
        if train_mode:
            self.iterations += 1
            self.find_available_tasks()

    def find_available_tasks(self):
        itrls = self.task_intervals.keys()
        if self.iterations > eval(itrls[-1])[-1]:
            exit()
        else:
            if self.iterations > eval(itrls[self.num_interval])[-1]:
                self.num_interval += 1
            self.available_tasks = self.task_intervals[itrls[self.num_interval]]

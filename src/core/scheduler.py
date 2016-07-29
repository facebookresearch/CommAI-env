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


class RandomTaskScheduler:
    '''
    A Scheduler provides new tasks every time is asked.
    This is a random scheduler
    '''
    def __init__(self, tasks):
        self.tasks = tasks

    def get_next_task(self):
        # pick a random task
        return random.choice(self.tasks)

    def reward(self, reward):
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

    def get_next_task(self):
        # pick a random task
        ret = self.tasks[self.i]
        self.i = (self.i + 1) % len(self.tasks)
        return ret

    def reward(self, reward):
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

    def get_next_task(self):
        if self.reward_count == self.success_threshold:
            self.reward_count = 0
            self.task_ptr = (self.task_ptr + 1) % len(self.tasks)
        return self.tasks[self.task_ptr]

    def reward(self, reward):
        self.reward_count += 1

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

    def get_next_task(self):
        self.last_task = self.pick_new_task()
        return self.last_task

    def reward(self, reward):
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

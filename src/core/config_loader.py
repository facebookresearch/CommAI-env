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
import json
import os


class JSONConfigLoader:
    '''
    Loads a set of tasks and a schedule for them from a JSON file::

        {
          "tasks":
          {
            "<task_id>": {
                "type": "<task_class>",
            },
            "<task_id>": {
                "type": "<task_class>",
                "world": "<world_id>"
            }
            "...": "..."
          },
          "worlds":
          {
            "<world_id>": {
              "type": "<world_class>",
            }
          },
          "scheduler":
            {
              "type": "<scheduler_class>",
              "args": {
                  "<scheduler_arg>": <scheduler_arg_value>,
                }
            }
        }

    The scheduler scheduler_arg_value could be a container including
    task ids, which will be replaced by the concrete tasks instances.
    '''
    def create_tasks(self, tasks_config_file):
        '''
        Given a json configuartion file, it returns a scheduler object
        set up as described in the file.
        '''
        config = json.load(open(tasks_config_file))
        # instantiate the worlds (typically there is only one)
        worlds = dict((world_id, self.instantiate_world(world_config['type']))
                      for world_id, world_config in config['worlds'].items())
        # map each task
        # instantiate the tasks with the world (if any)
        tasks = dict((task_id, self.instantiate_task(task_config['type'],
                                                     worlds,
                                                     task_config.get(
                                                         'world', None)))
                      for task_id, task_config in config['tasks'].items())
        # retrieve what type of scheduler we need to create
        scheduler_class = get_class(config['scheduler']['type'])
        # prepare the arguments to instantiate the scheduler
        scheduler_args = {}
        for arg_name, arg_value in config['scheduler']['args'].items():
            # all arguments that begin with the name tasks are taken as
            # collections of ids that should be mapped to the corresponding
            # tasks object
            if arg_name.startswith('tasks'):
                scheduler_args[arg_name] = map_tasks(arg_value, tasks)
            else:
                scheduler_args[arg_name] = arg_value
        # return a scheduler with its corresponding arguments
        return scheduler_class(**scheduler_args)

    def instantiate_world(self, world_class):
        '''
        Return a world object given the world class
        '''
        C = get_class(world_class)
        try:
            return C()
        except Exception as e:
            raise RuntimeError("Failed to instantiate world {0} ({1})".format(
                world_class, e))

    def instantiate_task(self, task_class, worlds, world_id=None):
        '''
        Returns a task object given the task class and the world where it
        runs (if any)
        '''
        C = get_class(task_class)
        try:
            if world_id:
                return C(worlds[world_id])
            else:
                return C()
        except Exception as e:
            raise RuntimeError("Failed to instantiate task {0} ({1})".format(
                task_class, e))


class PythonConfigLoader:
    '''
        Loads a python file containing a stand-alone function called
        `create_tasks` that returns a TaskScheduler object.
    '''
    def create_tasks(self, tasks_config_file):
        # make sure we have a relative path
        tasks_config_file = os.path.relpath(tasks_config_file)
        if tasks_config_file.startswith('..'):
            raise RuntimeError("The task configuration file must be in the "
                               "same directory as the competition source.")
        # just in case, remove initial unneeded "./"
        if tasks_config_file.startswith('./'):
            tasks_config_file = tasks_config_file[2:]
        # transform the config file path into a module path
        tasks_config_module = os.path.splitext(
            tasks_config_file)[0].replace('/', '.')
        mod = __import__(tasks_config_module, fromlist=[''])
        return mod.create_tasks()


def get_class(name):
    components = name.split('.')
    mod = __import__('.'.join(components[:-1]), fromlist=[components[-1]])
    mod = getattr(mod, components[-1])
    return mod


def map_tasks(arg, tasks):
    try:
        # if arg is a task, return the task object
        return tasks[arg]
    except KeyError:
        # arg is a hashable type, but we cannot map it to a task
        raise RuntimeError("Coudln't find task id '{0}'.".format(arg))
    # unhashable type
    except TypeError:
        # we treat arg as a collection that should be mapped
        return list(map(lambda x: map_tasks(x, tasks), arg))

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
import os
import logging
import logging.config
import operator
from optparse import OptionParser
from core.environment import Environment
from core.config_loader import JSONConfigLoader, PythonConfigLoader
import learners
from core.session import Session
from view.console import ConsoleView, BaseView


def main():
    setup_logging()
    op = OptionParser("Usage: %prog [options] "
                      "(tasks_config.json | tasks_config.py)")
    op.add_option('-o', '--output', default='results.out',
                  help='File where the simulation results are saved.')
    op.add_option('--scramble', action='store_true', default=False,
                  help='Randomly scramble the words in the tasks for '
                  'a human player.')
    op.add_option('-w', '--show-world', action='store_true', default=False,
                  help='shows a visualization of the world in the console '
                  '(mainly for debugging)')
    op.add_option('-d', '--time-delay', default=0, type=float,
                  help='adds some delay between each timestep for easier'
                  ' visualization.')
    op.add_option('-l', '--learner',
                  default='learners.human_learner.HumanLearner',
                  help='Defines the type of learner.')
    op.add_option('-v', '--view',
                  default='BaseView',
                  help='Viewing mode.')
    op.add_option('-s', '--serializer',
                  default='core.serializer.StandardSerializer',
                  help='Sets the encoding of characters into bits')
    op.add_option('--learner-cmd',
                  help='The cmd to run to launch RemoteLearner.')
    op.add_option('--learner-port',
                  default=5556,
                  help='Port on which to accept remote learner.')
    op.add_option('--max-reward-per-task',
                  default=10, type=int,
                  help='Maximum reward that we can give to a learner for'
                  ' a given task.')
    opt, args = op.parse_args()
    if len(args) == 0:
        op.error("Tasks schedule configuration file required.")
    # retrieve the task configuration file
    tasks_config_file = args[0]
    logger = logging.getLogger(__name__)
    logger.info("Starting new evaluation session")
    # we choose how the environment will produce and interpret
    # the bit signal
    serializer = create_serializer(opt.serializer)
    # create a learner (the human learner takes the serializer)
    learner = create_learner(opt.learner, serializer, opt.learner_cmd,
                                opt.learner_port)
    # create our tasks and put them into a scheduler to serve them
    task_scheduler = create_tasks_from_config(tasks_config_file)
    # construct an environment
    env = Environment(serializer, task_scheduler, opt.scramble,
                      opt.max_reward_per_task)
    # a learning session
    session = Session(env, learner, opt.time_delay)
    # setup view
    view = create_view(opt.view, opt.learner, env, session, serializer,
                        opt.show_world)
    try:
        # send the interface to the human learner
        learner.set_view(view)
    except AttributeError:
        # this was not a human learner, nothing to do
        pass
    try:
        view.initialize()
        # ok guys, talk
        session.run()
    except BaseException:
        view.finalize()
        save_results(session, opt.output)
        raise
    else:
        view.finalize()


def getc(typename):
    # TODO: move into some misc aux functions module
    # dynamically load the class given by typename
    # separate the module from the class name
    path = typename.split('.')
    mod, cname = '.'.join(path[:-1]), path[-1]
    # import the module (and the class within it)
    m = __import__(mod, fromlist=[cname])
    c = getattr(m, cname)
    if not c:
        raise RuntimeError("type {0} not found in module {1}".format(cname,
                                                                     mod))
    return c


def create_view(view_type, learner_type, env, session, serializer, show_world):
    if learner_type.startswith('learners.human_learner') \
            or view_type == 'ConsoleView':
        return ConsoleView(env, session, serializer, show_world)
    else:
        View = getc('view.console.%s' % view_type)
        return View(env, session)


def create_learner(learner_type, serializer, learner_cmd, learner_port=None):
    c = getc(learner_type)
    if learner_type.startswith('learners.human_learner'):
        return c(serializer)
    else:
        # instantiate the learner
        return c(learner_cmd, learner_port) if 'RemoteLearner' in str(c) else c()


def create_serializer(serializer_type):
    c = getc(serializer_type)
    return c()


def create_tasks_from_config(tasks_config_file):
    ''' Returns a TaskScheduler based on either:

        - a json configuration file.
        - a python module with a function create_tasks that does the job
        of returning the task scheduler.
    '''
    fformat = tasks_config_file.split('.')[-1]
    if fformat == 'json':
        config_loader = JSONConfigLoader()
    elif fformat == 'py':
        config_loader = PythonConfigLoader()
    else:
        raise RuntimeError("Unknown configuration file format '.{fformat}' of"
                           " {filename}"
                           .format(fformat=fformat,
                                   filename=tasks_config_file))
    return config_loader.create_tasks(tasks_config_file)


def save_results(session, output_file):
    if session.get_total_time() == 0:
        # nothing to save
        return
    with open(output_file, 'w') as fout:
        print('* General results', file=fout)
        print('Average reward: {avg_reward}'.format(
            avg_reward=session.get_total_reward() / session.get_total_time()),
            file=fout)
        print('Total time: {time}'.format(time=session.get_total_time()),
               file=fout)
        print('Total reward: {reward}'.format(
            reward=session.get_total_reward()),
            file=fout)
        print('* Average reward per task', file=fout)
        for task, t in sorted(session.get_task_time().items(),
                              key=operator.itemgetter(1)):
            r = session.get_reward_per_task()[task]
            print('{task_name}: {avg_reward}'.format(
                task_name=task, avg_reward=r / t),
                file=fout)
        print('* Total reward per task', file=fout)
        for task, r in sorted(session.get_reward_per_task().items(),
                              key=operator.itemgetter(1), reverse=True):
            print('{task_name}: {reward}'.format(task_name=task, reward=r),
                  file=fout)
        print('* Total time per task', file=fout)
        for task, t in sorted(session.get_task_time().items(),
                              key=operator.itemgetter(1)):
            print('{task_name}: {time}'.format(task_name=task, time=t),
                  file=fout)
        print('* Number of trials per task', file=fout)
        for task, r in sorted(session.get_task_count().items(),
                              key=operator.itemgetter(1)):
            print('{task_name}: {reward}'.format(task_name=task, reward=r),
                  file=fout)


def setup_logging(
    default_path='logging.ini',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        logging.config.fileConfig(default_path)
    else:
        logging.basicConfig(level=default_level)

if __name__ == '__main__':
    main()

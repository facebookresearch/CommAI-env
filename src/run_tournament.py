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
from core.serializer import StandardSerializer
from core.environment import Environment
from tasks_config import create_tasks
from learners.human_learner import HumanLearner
from core.session import Session
from view.console import ConsoleView


def main():
    setup_logging()
    op = OptionParser()
    op.add_option('-o', '--output', dest='output', default='results.out',
                  help='File where the simulation results are saved.')
    op.add_option('--scramble', dest='scramble', action='store_true',
                  default=False,
                  help='Randomly scramble the words in the tasks for '
                  'a human player.')
    ops, args = op.parse_args()

    logger = logging.getLogger(__name__)
    logger.info("Starting new tournament")
    # we choose how the environment will produce and interpret
    # the bit signal
    serializer = StandardSerializer()
    # we'll have a mechanism to instantiate many types of learner later
    learner = HumanLearner(serializer)
    # construct an environment
    env = Environment(serializer, ops.scramble)
    # create our tasks and put them into a scheduler to serve them
    task_scheduler = create_tasks(env)
    # a learning session
    session = Session(env, learner, task_scheduler)
    # console interface
    view = ConsoleView(env, session, serializer)
    # send the interface to the human learner
    learner.set_view(view)
    try:
        view.initialize()
        # ok guys, talk
        session.run()
    except BaseException:
        view.finalize()
        save_results(session, ops.output)
        raise
    else:
        view.finalize()


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

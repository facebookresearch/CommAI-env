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
import json
import logging
import logging.config
from core.serializer import StandardSerializer
from core.environment import Environment
from tasks_config import create_tasks
from learners.sample_learners import SampleMemorizingLearner
from learners.human_learner import HumanLearner
from core.session import Session
from view.console import ConsoleView


def main():
    logger = logging.getLogger(__name__)
    logger.info("Starting new tournament")
    setup_logging()
    # we choose how the environment will produce and interpret
    # the bit signal
    serializer = StandardSerializer()
    # construct an environment
    env = Environment(serializer)
    # we'll have a mechanism to instantiate many types of learner later
    learner = HumanLearner(serializer)
    # create our tasks and put them into a scheduler to serve them
    task_scheduler = create_tasks(env)
    # a learning session
    session = Session(env, learner, task_scheduler)
    # console interface
    view = ConsoleView(env, session)
    # send the interface to the human learner
    learner.set_view(view)
    try:
        view.initialize()
        # ok guys, talk
        session.run()
    except BaseException:
        view.finalize()
        raise
    else:
        view.finalize()


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

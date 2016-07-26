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
import sys
import logging
from core.serializer import StandardSerializer, IdentitySerializer
from core.environment import Environment
from tasks_config import create_tasks, create_tasks_incremental
from learners.sample_learners import SampleRandomWordsLearner
from learners.sample_learners import RandomCharacterLearner
from learners.sample_learners import SampleMemorizingLearner
from learners.human_learner import HumanLearner
from core.session import Session, ExternalSession
from view.console import ConsoleView


def init_logger(default_path='logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'):
    logger = logging.getLogger(__name__)
    logger.info("Starting new tournament")

    """
        Logging config
    """
    # Python 2.6 doesn't have decent config utilities, so using the basic config
    logging.basicConfig(level=default_level)


def build_tournament(serializer, learner):
    init_logger()
    env = Environment(serializer)
    task_scheduler = create_tasks_incremental(env)
    session = Session(env, learner, task_scheduler)
    view = ConsoleView(env, session)
    return session, view


def run_tournament(session, view):
    try:
        view.initialize()
        session.run()
    except BaseException:
        view.finalize()
        raise
    else:
        view.finalize()


def human_learner():
    serializer = StandardSerializer()
    learner = HumanLearner(serializer)
    session, view = build_tournament(serializer, learner)
    learner.set_view(view)
    run_tournament(session, view)


def memorizing_learner():
    serializer = StandardSerializer()
    learner = SampleMemorizingLearner()
    session, view = build_tournament(serializer, learner)
    run_tournament(session, view)


def random_words_learner():
    serializer = StandardSerializer()
    learner = SampleRandomWordsLearner()
    session, view = build_tournament(serializer, learner)
    run_tournament(session, view)

def random_character_learner():
    serializer = IdentitySerializer()
    learner = RandomCharacterLearner()
    session, view = build_tournament(serializer, learner)
    session.set_sleep(0.1)
    run_tournament(session, view)

def external_learner():
    serializer = IdentitySerializer()
    env = Environment(serializer)
    task_scheduler = create_tasks_incremental(env)
    env.set_task_scheduler(task_scheduler)
    return env



if __name__ == '__main__':
    _learners = {
            'human': human_learner,
            'memorizing': memorizing_learner,
            'random_words': random_words_learner,
            'random_char': random_character_learner
                }
    learner_type = sys.argv[1]
    _learners[learner_type]()

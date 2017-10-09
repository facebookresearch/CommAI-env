from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import torch
import json
import argparse
from collections import defaultdict
import math

parser = argparse.ArgumentParser(description='Summary statistics from CommAI '
                                 'Learner json files')
parser.add_argument("--success", nargs='+', help="simulation results file")
parser.add_argument("--learner", nargs='+', help="learner log")

args = parser.parse_args()

task_ponderings = defaultdict(int)
task_presentations = defaultdict(int)

for i, success_f in enumerate(args.success):
    learner_f = args.learner[i]
    learner_log = torch.load(learner_f)

    with open(success_f, 'r') as f:
        raw_data = json.load(f)

    num_episodes = len(learner_log['action'])
    for episode in range(num_episodes):
        input = learner_log['input'][episode]
        actions = learner_log['action'][episode]

        teacher_dot = input.index(2)
        pondering = 0
        did_pondering = False
        for character in actions[teacher_dot:]:
            if character == 3:
                did_pondering = True
                pondering += 1
            elif did_pondering:
                break

        task = ''
        for key in raw_data['S']:
            if not math.isnan(raw_data['S'][key][episode]):
                task = key
                break
        assert task != ''

        task_ponderings[task] += pondering
        task_presentations[task] += 1

for task in sorted(task_ponderings.keys()):
    print('{}\t{}'.format(task, task_ponderings[task] / task_presentations[task]))

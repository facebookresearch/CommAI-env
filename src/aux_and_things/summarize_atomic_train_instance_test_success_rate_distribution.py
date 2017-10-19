from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import argparse
import json
import math
import numpy as np
import re
from collections import defaultdict

parser = argparse.ArgumentParser(description='Summary statistics from CommAI '
                                 'Learner json files')
parser.add_argument("--window", type=int, default=100,
                    help="window size for running accuracy")
parser.add_argument("--success_threshold", type=float, default=0.95,
                    help="minimum running accuracy considered successful")
parser.add_argument("--failure_time", type=int, default=10000000,
                    help="nominal time step assigned to tasks that were not "
                    "learned within the simulation")
parser.add_argument("--composition_type", default="Func",
                    help="Type of composition: Func [default], Cat, Proc")
parser.add_argument("input_json_files", nargs='+', help="simulation results files")


args = parser.parse_args()

# Distribution of times required to learn the task
success_time_distribution = defaultdict(list)
success_time_dist_comp = defaultdict(list)
# Distribution of times the task was presented
presentation_counts = defaultdict(list)

for input_json_file in args.input_json_files:
    with open(input_json_file, 'r') as f:
        raw_data = json.load(f)

    for task in raw_data['S'].keys():
        # If the task is compositional, check whether it's train/test
        # for summary statistics
        task_category = ''
        if re.search(args.composition_type, task):
            if (re.search("Test", task)):
                task_category = "ComposedTest"
            else:
                task_category = "ComposedTrain"
        else:
            task_category = 'Atomic'

        cleaned_list = [x for x in raw_data['S'][task] if not math.isnan(x)]
        current_index = args.window - 1
        success_threshold_met = False
        time_to_succeed = args.failure_time
        while ((current_index < len(cleaned_list)) and not(success_threshold_met)):
            reference_accuracy = 0
            if (current_index >= args.window):
                reference_accuracy = cleaned_list[current_index - args.window]
            accuracy = ((cleaned_list[current_index] - reference_accuracy) /
                        float(args.window))
            current_index += 1

            if (accuracy >= args.success_threshold):
                success_threshold_met = True
                time_to_succeed = current_index

        presentation_counts[task].append(len(cleaned_list))
        success_time_distribution[task].append(time_to_succeed)
        if task_category != '':
            success_time_dist_comp[task_category].append(time_to_succeed)

################### Print summary statistics ###################
print('Success threshold: {}, window size: {}'.format(args.success_threshold,
                                                      args.window))

print('\nSummary of compositional tasks:')
for task_category in sorted(success_time_dist_comp.keys()):
    time_to_succeed = success_time_dist_comp[task_category]
    first_quartile = np.percentile(time_to_succeed, 25, interpolation='midpoint')
    median = np.percentile(time_to_succeed, 50, interpolation='midpoint')
    third_quartile = np.percentile(time_to_succeed, 75, interpolation='midpoint')
    sorted_distribution = "\t".join(map(str, np.sort(time_to_succeed)))
    print('\t'.join([task_category, str(first_quartile), str(median),
                     str(third_quartile), sorted_distribution]))

print('\nAll tasks:')
for task in sorted(success_time_distribution.keys()):
    time_to_succeed = success_time_distribution[task]
    first_quartile = np.percentile(time_to_succeed, 25, interpolation='midpoint')
    median = np.percentile(time_to_succeed, 50, interpolation='midpoint')
    third_quartile = np.percentile(time_to_succeed, 75, interpolation='midpoint')
    sorted_distribution = "\t".join(map(str, np.sort(time_to_succeed)))
    print('\t'.join([task, str(first_quartile), str(median),
                     str(third_quartile), sorted_distribution]))

print('\nNumber of presentations:')
for task in sorted(presentation_counts.keys()):
    presentation_count = presentation_counts[task]
    first_quartile = np.percentile(presentation_count, 25, interpolation='midpoint')
    median = np.percentile(presentation_count, 50, interpolation='midpoint')
    third_quartile = np.percentile(presentation_count, 75, interpolation='midpoint')
    sorted_distribution = "\t".join(map(str, np.sort(presentation_count)))
    print('\t'.join([task, str(first_quartile), str(median),
                     str(third_quartile), sorted_distribution]))

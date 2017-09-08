import argparse
import json
import math
import numpy as np
import re
parser = argparse.ArgumentParser(description='Summary statistics from CommAI Learner json files')

parser.add_argument("--window", help="window size for running accuracy", type=int, default=100)
parser.add_argument("--success_threshold", help="minimum running accuracy considered successful", type=float, default=0.95)
parser.add_argument("--failure_time", help="nominal time step assigned to tasks that were not learned within the simulation", type=int, default=10000000)
parser.add_argument("--atomic_count", help="number of atomic tasks", type=int, default=4)
parser.add_argument("--train_count", help="number of composed tasks in training phase", type=int, default=10)

parser.add_argument("input_json_files", help="config files followed by simulation results files", nargs='+')


args = parser.parse_args()

train_composed_tasks = {}
test_composed_tasks = {}
success_time_distribution = {}

for input_json_file in args.input_json_files:

    experiment_number = int(re.findall('_([0-9]+)_',input_json_file)[-1])
    raw_data=json.load(open(input_json_file))

    if (re.search('tasks_config',input_json_file)):
        # processing tasks config files
        train_composed_tasks[experiment_number] = set()
        test_composed_tasks[experiment_number] = set()

        for i in range(args.atomic_count,args.atomic_count+args.train_count):
            train_composed_tasks[experiment_number].add(raw_data['scheduler']['args']['tasks'][i])

        for i in range(args.atomic_count+args.train_count,len(raw_data['scheduler']['args']['tasks'])):
            test_composed_tasks[experiment_number].add(raw_data['scheduler']['args']['tasks'][i])
    else: # processing results files
        for task in raw_data['S'].keys():
            task_category = task
            if task_category in train_composed_tasks[experiment_number]:
                task_category = "ComposedTrain"
            elif task_category in test_composed_tasks[experiment_number]:
                task_category = "ComposedTest"
            if task_category not in success_time_distribution:
                success_time_distribution[task_category]=[]
            cleaned_list = [x for x in raw_data['S'][task] if (math.isnan(x)==False)]
            current_index = args.window-1
            success_threshold_met = False
            time_to_succeed = args.failure_time
            while ((current_index<len(cleaned_list)) and not(success_threshold_met)):
                reference_accuracy = 0
                if (current_index >= args.window):
                    reference_accuracy = cleaned_list[current_index-args.window]
                accuracy=(cleaned_list[current_index]-reference_accuracy)/float(args.window)
                current_index=current_index+1
                if (accuracy>=args.success_threshold):
                    success_threshold_met = True
                    time_to_succeed = current_index
            success_time_distribution[task_category].append(time_to_succeed)

for task_category in success_time_distribution:
    first_quartile = np.percentile(success_time_distribution[task_category],25,interpolation='midpoint')
    median = np.percentile(success_time_distribution[task_category],50,interpolation='midpoint')
    third_quartile = np.percentile(success_time_distribution[task_category],75,interpolation='midpoint')
    sorted_distribution = "\t".join(map(str,np.sort(success_time_distribution[task_category])))
    print(task_category + "\t" + str(first_quartile) + "\t" + str(median) + "\t"
          + str(third_quartile) + "\t" + sorted_distribution)

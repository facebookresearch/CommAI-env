import argparse
import json
import math
import numpy as np
parser = argparse.ArgumentParser(description='Summary statistics from CommAI Learner json files')

parser.add_argument("--window", help="window size for running accuracy", type=int, default=100)
parser.add_argument("--success_threshold", help="minimum running accuracy considered successful", type=float, default=0.95)
parser.add_argument("--failure_time", help="nominal time step assigned to tasks that were not learned within the simulation", type=int, default=100000)

parser.add_argument("input_json_files", help="files contaiing simulation results", nargs='+')

args = parser.parse_args()

success_time_distribution = {}

for input_json_file in args.input_json_files:
    raw_data=json.load(open(input_json_file))

    for task in raw_data['S'].keys():
        if task not in success_time_distribution:
            success_time_distribution[task]=[]
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
        success_time_distribution[task].append(time_to_succeed)

for task in success_time_distribution:
    first_quartile = np.percentile(success_time_distribution[task],25,interpolation='midpoint')
    median = np.percentile(success_time_distribution[task],50,interpolation='midpoint')
    third_quartile = np.percentile(success_time_distribution[task],75,interpolation='midpoint')
    sorted_distribution = "\t".join(map(str,np.sort(success_time_distribution[task])))
    print(task + "\t" + str(first_quartile) + "\t" + str(median) + "\t"
          + str(third_quartile) + "\t" + sorted_distribution)

import argparse
import json
import math

parser = argparse.ArgumentParser(description='First point in which each task is mastered from CommAI Learner json files')

parser.add_argument("--window", help="window size for which task must be successful to consider it mastered at the onset of the window", type=int, default=100)
parser.add_argument("--success_threshold", help="minimum running accuracy considered successful", type=float, default=0.95)
parser.add_argument("--failure_score", help="nominal mastering score assigned to tasks that were not mastered within the simulation", type=int, default=0)

parser.add_argument("input_json_files", help="simulation results files", nargs='+')


args = parser.parse_args()

for input_json_file in args.input_json_files:

    raw_data=json.load(open(input_json_file))

    for task in raw_data['S'].keys():
        cleaned_list = [x for x in raw_data['S'][task] if (math.isnan(x)==False)]
        reference_accuracy = 0
        current_index = 0
        success_threshold_met = False
        mastering_point = args.failure_score
        while ((current_index+args.window)<=len(cleaned_list) and not(success_threshold_met)):
            accuracy=(cleaned_list[current_index+args.window-1]-reference_accuracy)/float(args.window)
            reference_accuracy = cleaned_list[current_index]
            current_index = current_index + 1
            if (accuracy>=args.success_threshold):
                success_threshold_met = True
                mastering_point = current_index
        print input_json_file + "\t" + task + "\t" + str(mastering_point)

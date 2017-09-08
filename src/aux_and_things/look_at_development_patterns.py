import json
import math
import sys

data=json.load(open(sys.argv[1]))

for task in data['S'].keys():
    print("analyzing task " + str(task))
    total_task_episodes = 0
    last_is_nan = True
    for task_number,success_count in enumerate(data['S'][task]):
        if not (math.isnan(success_count)):
            if (last_is_nan):
                print("task active at " + str(task_number))
            last_is_nan = False
            total_task_episodes = total_task_episodes + 1
        else:
            if not (last_is_nan):
                print("task inactive at " + str(task_number))
            last_is_nan = True
    print("total task episodes for task " + task + ": " + str(total_task_episodes))

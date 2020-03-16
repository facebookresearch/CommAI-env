# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

#!/usr/bin/env python
import argparse
import sys
sys.path.append('analysis')
import display_results as dr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('id')
    ap.add_argument('--results-file', action='store_true')
    args = ap.parse_args()

    df_data = dr.get_results()
    row = df_data.loc[args.id]
    if args.results_file:
        print(row['results_file'])
    else:
        command_line = "python main.py " + dr.row_to_command_line(df_data, row)
        print(command_line)



if __name__ == '__main__':
    main()

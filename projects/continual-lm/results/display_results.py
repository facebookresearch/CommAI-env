# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

#!/usr/bin/env python
import sys
sys.path.append('..')
sys.path.append('.')
import argparse
import config
from pathlib import Path
import glob
import os.path
from configparser import ConfigParser
import pandas as pd
import json
import tqdm
import numpy as np
import math

pd.options.display.max_rows = 999 
pd.options.display.width = 0
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clear-cache', action='store_true', default=False)
    ap.add_argument('--log-path')
    ap.add_argument('--mean', action='store_true', default=False)
    args = ap.parse_args()
    if args.clear_cache:
        ans = input("You are about to clear the results cache. Are you sure? [y]/n: ") or "y"
        if ans != "y":
            args.clear_cache = False
    else:
        sys.stderr.write('warning: using cached results when available\n')
    df_data = get_results(args.log_path, args.clear_cache)
    display_results(df_data, args.mean)

def get_results(log_path=None, clear_cache=False):
    if log_path is None:
        log_path = Path(config.logs_dir)/'cluster-run'
    else:
        log_path = Path(log_path)
    assert log_path.exists(), f"{log_path} does not exist"
    df_configs = read_configs(log_path)
    df_data = add_results(df_configs, clear_cache)
    df_data = df_data.rename_axis('path').reset_index()
    df_data.path = df_data.path.apply(lambda x: os.path.basename(x))
    df_data = df_data.set_index('path')
    return df_data

def read_configs(log_path):
    configs = {}
    for config_file in glob.glob(str(log_path / '**/config.ini'), recursive=True):
        config_file = Path(config_file)
        config_dir = config_file.parent
        results_file = config_dir/'general_pp.jsonl'
        if (results_file).is_file():
            configs[str(config_dir)] = read_config_file(config_file)
            configs[str(config_dir)]['results_file'] = results_file
    df = pd.DataFrame.from_dict(configs, orient = 'index')
    df['data'] = df['data'].apply(lambda path: os.path.basename(path))
    #df = df.drop_duplicates(keep='last')
    return df

def add_results(df_configs, clear_cache):
    results = {}
    for config_dir in tqdm.tqdm(df_configs.index, desc='parsing results'):
        results[config_dir] = read_results(Path(config_dir)/'general_pp.jsonl', clear_cache)
    df_results = pd.DataFrame.from_dict(results, orient = 'index')
    df_data = pd.concat([df_configs, df_results], axis=1, sort=True)
    return df_data

def get_loss_history_for_row(row):
    filename = row['results_file']
    parsed_results = parse_results(filename)
    loss_history = get_loss_history(parsed_results)
    return loss_history

def read_results(filename, clear_cache):
    results_cache_filename = filename.parent/'results_cache.json'
    if not clear_cache and results_cache_filename.is_file():
        return json.load(open(results_cache_filename))
    parsed_results = parse_results(filename)
    results = extract_measures(parsed_results)
    json.dump(results, open(results_cache_filename, 'w'))
    return results

def get_loss_history(parsed_results):
    losses = np.array([r['loss'] for r in parsed_results])
    return losses

def get_switch_times(parsed_results):
    sequences = np.array([r['sequence'] for r in parsed_results])
    sequences_ids, switch_times = np.unique(sequences, return_index=True)
    return switch_times

def get_domain_history(parsed_results, switch_times):
    domain_history = np.array([parsed_results[t]['domain'] for t in switch_times])
    return domain_history

def get_domain_names(parsed_results):
    domain_names = {}
    for r in parsed_results:
        domain_names[r['domain']] = r['domain_name']
    return domain_names

def parse_results(filename):
    with open(filename) as f:
        parsed_results = []
        for line in f:
            parsed_line = json.loads(line)
            if parsed_line['sequence'] >= 50:
                parsed_results.append(parsed_line)
    if not parsed_results or parsed_line['sequence'] <  99:
        return []
    return parsed_results

def calc_surprisal_intensity(losses, _):
    return np.mean(losses[:10])

def calc_surprisal_duration(losses, prev_loss):
    duration = 0
    #loss_avg = np.average(losses)
    for i in range(len(losses)):
        if losses[i] < prev_loss:
            break
        duration += 1
    return duration

def get_mean_loss_by_domain(parsed_results):
    losses_by_domain = stitch_losses_by_domain(parsed_results)
    domain_names = get_domain_names(parsed_results)
    return {domain_names[d]: np.mean(losses) for d, losses in losses_by_domain.items()}

def stitch_losses_by_domain(parsed_results):
    loss_history = get_loss_history(parsed_results)
    switch_times = get_switch_times(parsed_results)
    dom_names = get_domain_history(parsed_results, switch_times)
    loss_per_domain = {}
    for i in range(len(switch_times)-1):
        if dom_names[i] not in loss_per_domain:
            loss_per_domain[dom_names[i]] = []
        local_losses = loss_history[switch_times[i]:switch_times[i+1]]
        loss_per_domain[dom_names[i]].extend(local_losses)
    loss_per_domain[dom_names[-1]].extend(loss_history[switch_times[-1]:])
    return loss_per_domain

def get_surprisal_by_domain(parsed_results, surprisal_measure):
    loss_history = get_loss_history(parsed_results)
    switch_times = get_switch_times(parsed_results)
    dom_names = get_domain_history(parsed_results, switch_times)
    real_domain_names = get_domain_names(parsed_results)
    surprisal_per_domain = {}
    avg_surprisal_per_domain = {}
    prev_losses = {}
    for i in range(len(switch_times)-1):
        if dom_names[i] not in surprisal_per_domain:
            surprisal_per_domain[dom_names[i]] = []
        local_losses = loss_history[switch_times[i]:switch_times[i+1]]
        if dom_names[i] in prev_losses:
            surprisal_per_domain[dom_names[i]].append(surprisal_measure(local_losses, prev_losses[dom_names[i]]))
        prev_losses[dom_names[i]] = np.mean(local_losses)
    #surprisal_per_domain[dom_names[-1]].append(surprisal_measure(local_losses))
    all_surprisals = []
    for el in surprisal_per_domain:
        avg_surprisal_per_domain[real_domain_names[el]] = np.average(surprisal_per_domain[el])
        all_surprisals.extend(surprisal_per_domain[el])
    gen_avg_surprisal = np.average(all_surprisals)
    return gen_avg_surprisal, avg_surprisal_per_domain

def extract_measures(parsed_results):
    loss_history = get_loss_history(parsed_results)
    if len(loss_history) == 0:
        return {}
    loss_per_domain = stitch_losses_by_domain(parsed_results)
    loss = np.mean(loss_history)
    std_per_domain = {domain: np.std(d_losses) for domain, d_losses in loss_per_domain.items()}
    def autocorr(x):
        return np.corrcoef(x[1:], x[:-1])[0,1]
    autocorr_per_domain = {domain: autocorr(d_losses) for domain, d_losses in loss_per_domain.items()}
    std = np.mean(list(std_per_domain.values()))
    autocorr = np.mean(list(autocorr_per_domain.values()))
    total_pp = np.exp(loss) if loss < 20 else float('inf')
    results = {'loss': loss, 'total_pp': total_pp,
            'std': std,
            'autocorr': autocorr}
    loss_by_domain = get_mean_loss_by_domain(parsed_results)
    surprisal_intensity, surprisal_intensity_per_domain = get_surprisal_by_domain(parsed_results, calc_surprisal_intensity)
    results['surprisal_intensity'] = np.exp(surprisal_intensity)
    surprisal_duration, surprisal_duration_per_domain = get_surprisal_by_domain(parsed_results, calc_surprisal_duration)
    results['surprisal_duration'] = surprisal_duration
    for domain, dloss in loss_by_domain.items():
        results[f'loss_{domain}'] = dloss
        results[f'total_pp_{domain}'] = np.exp(dloss) if loss < 20 else float('inf')
    for domain, dsurprisal in surprisal_intensity_per_domain.items():
        results[f'surprisal_intensity_{domain}'] = np.exp(dsurprisal)
    for domain, dsurprisal in surprisal_duration_per_domain.items():
        results[f'surprisal_duration_{domain}'] = dsurprisal
    return results

def read_config_file(filename):
    config = {}
    fin = open(filename, 'r')
    for count, line in enumerate(fin):
        if count % 3 == 0:
            key = line[1:-2]
        if count % 3 == 1:
            els = line.strip().split()
            val = els[-1]
            config[key] = val
    return config

def get_id(filename):
    return int(filename.parent.name)

def display_results(df_data, mean):
    pd.options.display.float_format = '{:,.3g}'.format
    pd.set_option('display.max_columns', 500)
    df_grouped = get_df_grouped(df_data, mean)
    uniform_values = {}
    # for col in df_grouped.columns:
    #     some_col_value = df_grouped.reset_index()[col].iloc[0]
    #     if ((df_grouped[col] == some_col_value).all()):
    #         uniform_values[col] = some_col_value
    #         df_grouped = df_grouped.drop(col, axis=1)
    print(df_grouped)
    for k, v in uniform_values.items():
        print(f"{k: <20}\t{v}")

arch_hyperparameters ={'moe':  ['lang_switch', 'total_length', 'architecture', 'lr', 
        'weights_trainer', 'learn_iterations', 'weights_trainer_lr', 
        'weights_trainer_annealing', 'weight_normalization'],
'clone': ['lang_switch', 'total_length', 'architecture', 'lr', 
        'weights_trainer', 'learn_iterations', 'weights_trainer_lr', 
        'weights_trainer_annealing', 'consolidation_period', 'max_stm_size', 
        'max_memory_size', 'ltm_deallocation', 'stm_initialization'],
'static' : ['lang_switch', 'total_length', 'architecture', 'nhid', 'lr', 
        'learn_iterations'],
'static_per_domain' : ['lang_switch', 'total_length', 'architecture', 'nhid', 'lr', 
        'learn_iterations']}
def get_test_results_for_dev_hyperparams(df_data, dev_best, test_data):
    test_rows = []
    missing_rows = []
    for i, row in dev_best.iterrows():
        data_row = df_data.loc[row.path]
        selected = df_data.reset_index()
        selected = selected[selected['data'] == test_data]
        for h in arch_hyperparameters[data_row['architecture']]:
            val = data_row[h]
            selected = selected.loc[selected[h] == val]
        if selected.empty:
            missing_rows.append(data_row)
            continue
        assert selected.ndim == 1 or (selected.iloc[0]['total_pp'] == selected['total_pp']).all() or np.isnan(selected.iloc[0]['total_pp']) or (selected.iloc[0]['architecture'] ==  'static')
        test_rows.append(selected.iloc[0])
    return pd.DataFrame(test_rows), pd.DataFrame(missing_rows)



def get_df_grouped(df_data, mean=False):
    show = ['lr', 
            'weights_trainer', 'learn_iterations', 'weights_trainer', 'weights_trainer_lr', 
            'weights_trainer_annealing', 'consolidation_period', 'max_stm_size', 
            'max_memory_size', 'ltm_deallocation', 'stm_initialization', 'weight_normalization' ]
    show = ['surprisal_intensity', 'surprisal_duration']
    group_by = ['data', 'total_length', 'lang_switch', 'architecture', 'nhid', 'weights_trainer', 'learn_iterations']
    #pp_cols = [c for c in df_data.columns if c.startswith('total_pp')]
    #loss_cols = [c for c in df_data.columns if c.startswith('loss')]
    #surp_cols = [c for c in df_data.columns if c.startswith('surp')]
    #show.extend(pp_cols)
    #show.extend(loss_cols)
    #show.extend(surp_cols)
    show = [c for c in set(show) if c not in group_by]
    merit = 'total_pp'
    df_grouped = df_data.groupby(group_by)
    df_data['z_score'] = df_grouped.total_pp.apply(lambda x: (x -x.mean()) /x.std())
    #df_data = df_data[abs(df_data['z_score']) < 2]
    df_grouped = df_data.groupby(group_by)
    if mean:
        df_grouped = df_grouped.mean()
    else:
        df_grouped = df_grouped.apply(lambda x: x.loc[x[merit] == x[merit].min(), [merit] + show])
    df_grouped = df_grouped.drop_duplicates(subset=[merit])[[merit]+show]
                    #.sort_values(merit)
    return df_grouped

def row_to_command_line(df_data, dr_run, make_test=False):
    args = []
    for c in dr_run.index:
        if c in ['log_dir', 'results_file', 'save']:
            continue
        if c in ['loss', 'pos_spikyness', 'neg_spikyness', 'total_pp', 'autocorr', 'std']:
            continue
        if c in ['cluster_run', 'cluster_run_name'] and not make_test: 
            continue
        if c.startswith('loss') or c.startswith('total_pp'):
            continue
        val = dr_run.loc[c]
        if val == 'None':
            continue
        if val == 'nan':
            continue
        if isinstance(val, float) and math.isnan(val):
            continue
        if val == 'False':
            continue
        if val == 'NA':
            continue
        if val == 'True':
            val = ''
        try:
            if float(val) == int(float(val)):
                val = str(int(float(val)))
        except:
            pass
        if c not in df_data.columns:
            continue
        if c == 'data':
            if make_test:
                val = val[:-len("dev")] + "test"
            data_path = '/checkpoint/germank/growing-rnn/data/'
            val = os.path.join(data_path, val)
        if ((val == df_data.loc[:,c]) | df_data.loc[:,c].isna() ).all():
            dr_run = dr_run.drop(c, axis=0)
        else:
            c = c.replace('_', '-')
            args.append((c,val))
    command_line_args = " ".join(f"--{k} {v}" for k,v in args)
    return command_line_args

if __name__ == '__main__':
    main()

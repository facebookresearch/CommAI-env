# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

print('Loading...')
import argparse
import os
import time
from collections import defaultdict, Counter
import itertools
import pickle
import math
from pathlib import Path
from pool import Pool
from pool_observer import PoolObserver
from pool_annealer import PoolAnnealer
from expression import Expression
from raw_log_pool_observer import RawLogPoolObserver
from raw_log_replay_pool import RawLogReplayPool
import json
import sys
import random
import numpy as np
import traceback
import logging
import tqdm

os.environ['PYTHONHASHSEED'] = "0"  # disable random hashing
sys.setrecursionlimit(10**6) 
logging.basicConfig(level=logging.WARNING)

def get_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reactions', type=int, default=int(1e6))
    ap.add_argument('--generations', type=int)
    ap.add_argument('--time', type=int, default=int(1e6))
    ap.add_argument('--timeout', type=int, default=10, 
            help='Max. time in seconds to compute one single generation.')
    ap.add_argument('--tape-size', type=int, default=10000)
    ap.add_argument('--report-every', type=int, default=10000,
            help='Number of expressions computed after which metrics are reported')
    ap.add_argument('--raw-logger', default=False, action='store_true',
            help='Save reactions in raw format')
    ap.add_argument('--raw-logger-checkpoint-interval', type=int,
            help='Number of iterations every which the raw logger dumps all '
            'expressions')
    ap.add_argument('--food-size', type=int, default=3,
            help='Size of the food set expressions')
    ap.add_argument('--w-reduce', type=float, default=15)
    ap.add_argument('--w-break', type=float, default=10)
    ap.add_argument('--w-combine', type=float, default=10)
    ap.add_argument('--p-reduce', type=float, default=-1)
    ap.add_argument('--p-break', type=float, default=-1)
    ap.add_argument('--p-combine', type=float, default=-1)
    ap.add_argument('--pool-reduce-regime', choices=['random', 'priority'],
            default='priority')
    ap.add_argument('--growth-rate', type=int)
    ap.add_argument('--growth-period', type=int)
    ap.add_argument('--break-position', choices=['top', 'random'], default='top')
    ap.add_argument('--combination-method', choices=['consense', 'unilateral'], default='consense')
    ap.add_argument('--randomize-probabilities', action='store_true', default=False)
    ap.add_argument('--normalize', action='store_true', default=False)
    ap.add_argument('--perf-max-sample-reductions', type=int, default=250,
            help='How many reductions of an expression to compute when sampling')
    ap.add_argument('--annealing', type=float, default=0)
    ap.add_argument('--feed', action='store_true', default=False)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--replay', 
            help='Replay from log')
    ap.add_argument('--load')
    ap.add_argument('--save')
    ap.add_argument('--log-dir')
    ap.add_argument('-v', '--verbose', action='store_true', default=False)
    ap.add_argument('-vv', '--very_verbose', action='store_true', default=False)
    args = ap.parse_args()
    return args

def main():
    print('Initializing...')
    args = get_args()
    if args.verbose:
        logging.getLogger().setLevel(level=logging.INFO)
    if args.very_verbose:
        logging.getLogger().setLevel(level=logging.DEBUG)
    if args.seed > 0: 
        random.seed(args.seed)
        np.random.seed(args.seed)
    else:
        args.seed = random.seed()
    args = adjust_action_probs(args)
    if args.log_dir:
        args.log_dir = with_slurm_id(args.log_dir)
        Path(args.log_dir).mkdir(parents=True, exist_ok=True)
        save_args(args, args.log_dir)
    if args.replay:
        pool = RawLogReplayPool(args.replay)
    else:
        pool = Pool(args.tape_size, args.p_reduce, args.p_combine,
                args.p_break, args.perf_max_sample_reductions, 
                args.break_position, args.pool_reduce_regime,
                args.food_size if args.feed else None,
                args.combination_method)
        if args.annealing:
            pool.register_step_observer(PoolAnnealer(args.annealing))
        if args.load:
            pool.load(args.load)
    if args.report_every:
        pool_observer = PoolObserver(args.report_every, 
                Path(args.log_dir) / 'log.jsonl' if args.log_dir else None,
                food_size=args.food_size,
                history_size=args.tape_size)
        pool.register_step_observer(pool_observer)
        pool.register_reaction_observer(pool_observer)
    if args.log_dir and args.raw_logger:
        raw_logger = RawLogPoolObserver(pool, 
            Path(args.log_dir) / 'raw_log.jsonl', 
            args.raw_logger_checkpoint_interval)
    if not args.log_dir and not args.report_every:
        sys.stderr.write('WARNING: not reporting simulation trace\n')
    try:
        print('Running Simulation...')
        run_simulation(pool, args)
    except TimeoutError:
        print("TIMEOUT")
    except KeyboardInterrupt:
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb, limit=-1)
        print('Interrupted by the user.')
    if args.save:
        if args.log_dir:
            save = Path(args.log_dir) / args.save
        else:
            save = args.save
        print(f'Saving last state to {args.save}.')
        pool.save(save)
    print('Resulting pool:')
    print(pool)

def run_simulation(pool, args):
    if args.generations:
        t = tqdm.tqdm(total=args.generations)
        def update_progressbar(i):
            t.update(1)
        pool.generation_computed.register(update_progressbar)
        pool.evolve_generations(args.generations)
        pool.generation_computed.deregister(update_progressbar)
    else:
        t = tqdm.tqdm(total=args.reactions)
        def update_progressbar(self, i):
            t.update(1)
        pool.step_computed.register(update_progressbar)
        pool.evolve(args.reactions, args.timeout)
        pool.step_computed.deregister(update_progressbar)

def with_slurm_id(log_dir):
    job_id = os.environ.get('SLURM_JOB_ID', 'local')
    return str(Path(log_dir) / str(job_id))

def save_args(args, log_dir):
    filename = Path(log_dir) / 'args.json'
    json.dump(vars(args), open(filename, 'w'))

def adjust_action_probs(args):
    if args.randomize_probabilities:
        args.p_reduce = random.random()
        args.p_combine = (1 - args.p_reduce) * random.random()
        args.p_break = 1 - args.p_reduce - args.p_combine
        print(f'p_reduce={args.p_reduce}, p_combine = {args.p_combine}, p_break = {args.p_break}')
    else:
        if args.normalize:
            Z = args.w_reduce + args.w_combine + args.w_break
            args.p_reduce = args.w_reduce / Z
            args.p_combine = args.w_combine / Z
            args.p_break = args.w_break / Z
        p_actions = ['p_reduce', 'p_combine', 'p_break']
        free_mass = 1 - sum(getattr(args, k) for k in p_actions if getattr(args, k) != -1)
        free_count = sum(1 for k in p_actions if getattr(args, k) == -1)
        for k in p_actions:
            v = getattr(args, k)
            if v == -1:
                v = free_mass / free_count
                sys.stderr.write(f'Setting {k} to {v:.4f}\n')
                setattr(args, k, v)
    return args
main()

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import configparser
import os
import numpy
import math
import torch
import json
import datetime
import time

def create_log_folder(path):
    if path.endswith('logs/'):
        dirlist = [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]
        new_dir = str(len(dirlist) + 1)
        os.makedirs(os.path.join(path, new_dir), exist_ok=True)
        return os.path.join(path, new_dir)
    else:
        os.makedirs(path, exist_ok=True)
        return path

def write_config_file(path, args):
    conf_file = os.path.join(path, 'config.ini')
    config = configparser.ConfigParser()
    for section in vars(args).keys():
        print(section)
        config.add_section(section)
        value = vars(args)[section]
        if value == 'True': value = 'yes'
        elif value == 'False': value = 'no'
        config.set(section, '', str(value))
    #print(conf_file)
    with open(conf_file, 'w') as configfile:
        config.write(configfile)


def get_grow_vector(args, domains, grow_type, lim=22):
    grow_block = [args.lang_switch * i for i in range(domains)]
    grow_steps = []
    grow_steps.extend(grow_block)
    if grow_type == 'linear':
        for i in range(domains, lim, domains):
            for el in grow_block:
                grow_steps.append(i * args.lang_switch + el)
    if grow_type == 'exp':
        exp = 2
        i = domains
        while len(grow_steps) < lim:
            for el in grow_block:
                grow_steps.append(i * args.lang_switch + el)
            i *= exp
    nr_batches = args.learn_iterations / (args.bptt * args.batch_size)
    grow_steps = [nr_batches * x for x in grow_steps]
    return grow_steps

def write_batch_ppl(detail_fout, out, target, batch_nr):
    #print(out.get_device())
    #print(target.get_device())
    loss_per_item = numpy.exp(torch.nn.CrossEntropyLoss(reduce = False)(out.cpu(), target.cpu()).data.numpy())
    #print(loss_per_item)
    detail_fout.write(str(batch_nr))
    for el in loss_per_item:
        detail_fout.write('\t' + str(el))
    detail_fout.write('\n')
    #detail_fout.flush()

def write_general_ppl(gen_fout, gen_json_fout, args, data_index, lr, loss, domain_id, domain, sequence_index, sequence_length, training = True):
    if training:
        log = ('| sequence {:9d} | lr {:02.5f} | loss {:5.3f} | ppl {:8.3f} | domain {}\n'
            .format(data_index, lr, loss, math.exp(loss), domain))
    else:
        log = ('dev domain {} | sequence {:9d} | lr {:02.5f} | loss {:5.3f} | ppl {:8.3f}\n'
            .format(domain, data_index, lr, loss, math.exp(loss)))
    gen_fout.write(log)
    data_row = {'loss': loss, 'lr': lr, 'domain': domain_id, 'domain_name': domain, 'position': data_index, 'sequence': sequence_index, 'sequence_length': int(sequence_length)}
    gen_json_fout.write(json.dumps(data_row))
    gen_json_fout.write('\n')
    #gen_fout.flush()

def get_rolling_loss(loss_hist, w=100):
    if len(loss_hist) < w:
        return float("nan")
    return sum(loss_hist[-w:]) / len(loss_hist[-w:])

def format_eta(global_start_time, pos, total):
    remaining_frac = (total-pos)/total
    remaining_time = int((time.time() - global_start_time) / pos * (total-pos))
    return datetime.timedelta(seconds=remaining_time)

def load_shadow_losses(shadow_run_path):
    with open(shadow_run_path) as f:
        parsed_results = []
        for line in f:
            parsed_line = json.loads(line)
            parsed_results.append(parsed_line)
    losses = [r['loss'] for r in parsed_results]
    return losses

def load_shadow_positions(shadow_run_path):
    with open(shadow_run_path) as f:
        parsed_results = []
        for line in f:
            parsed_line = json.loads(line)
            parsed_results.append(parsed_line)
    positions = [r['position'] for r in parsed_results]
    return positions

class WeightsLogger(object):
    def __init__(self, learner, output_filename):
        self.fout = open(output_filename, 'w')
        self.last_weights = None
        self.this_timestep_weights_logged = False
        learner.weights_updated.register(self.weights_updated)
        learner.weights_added.register(self.weights_added)
        learner.weights_removed.register(self.weights_removed)
        try:
            learner.weights_copied.register(self.weights_copied)
            learner.weights_moved.register(self.weights_moved)
            learner.ltm_size_updated.register(self.on_ltm_size_updated)
        except AttributeError:
            import sys; sys.stderr.write('Warning: not logging weights copying/moving.')

    def timestep_updated(self, time_id, global_position):
        self.log_line({'type': 'timestep_update', 'id': time_id, 'global_position': global_position})
        self.this_timestep_weights_logged = False

    def domain_switched(self, sequence_index, domain_id, domain_name):
        self.log_line({'type' : 'domain_switch', 'sequence': sequence_index,'id': domain_id, 'name': domain_name})

    def weights_updated(self, weights):
        if not self.this_timestep_weights_logged:
            weights = weights.detach().cpu().numpy()
            if self.last_weights is not None and (weights == self.last_weights).all():
                return
            self.log_line({'type': 'update', 'weights': list(map(float, weights))})
            self.this_timestep_weights_logged = True

    def weights_added(self, idx, val):
        self.log_line({'type': 'add', 'index': int(idx)})

    def weights_removed(self, idx):
        self.log_line({'type': 'remove', 'index': int(idx)})

    def weights_copied(self, source, dest):
        self.log_line({'type': 'copy', 'source': int(source), 'dest': int(dest)})

    def weights_moved(self, source, dest):
        self.log_line({'type': 'move', 'source': int(source), 'dest': int(dest)})

    def on_ltm_size_updated(self, ltm_size):
        self.log_line({'type': 'ltm', 'size': ltm_size})

    def log_line(self, data):
        self.fout.write(json.dumps(data))
        self.fout.write('\n')

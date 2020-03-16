# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import numpy as np
sys.path.append(os.getcwd())
#reload(sys)
import argparse
import time
import math
import torch
torch.backends.cudnn.enabled = False
from torch.autograd import Variable
import numpy
import data
import learner
from learner_factory import get_learner
import log_utils
import itertools
import random
from observer import Observable


parser = argparse.ArgumentParser(
    description='Vanilla RNN/LSTM Language Model with incremental batching')
parser.add_argument('--data', type=str,
                    default='data',
                    help='location of the data corpus')
parser.add_argument('--keep-list', type=str, default='vocab/',
                    help='keep list to construct vocabulary, to be stored in '
                    'the data directory')
parser.add_argument('--model-level', choices=['word', 'char'], default='char',
                    help='if the language model is character/word level')
parser.add_argument('--model', type=str, default='LSTM',
                    help='type of recurrent net (RNN_TANH, RNN_RELU, LSTM, GRU)')
parser.add_argument('--emsize', type=int, default=200,
                    help='size of word embeddings')
parser.add_argument('--nhid', type=int, default=200,
                    help='number of hidden units per layer')
parser.add_argument('--nhead', type=int, default=10,
                    help='number of attention heads for transformer')
parser.add_argument('--transformer-warmup', type=int, default=4000,
                    help='warmup steps for the transformer model')
parser.add_argument('--nlayers', type=int, default=2,
                    help='number of layers')
parser.add_argument('--lr', type=float, default=0.001,
                    help='initial learning rate')
parser.add_argument('--clip', type=float, default=1.0,
                    help='gradient clipping')
parser.add_argument('--learn-iterations', type=int, default=1,
                    help='number of iterations that the model is trained for on any given input')
parser.add_argument('--batch-size', type=int, default=10, metavar='N',
                    help='batch size')
parser.add_argument('--bptt', type=int, default=20,
                    help='backpropagation through time length')
parser.add_argument('--window', type=int, default=100,
                    help='window length for the linguistic stream batches')
parser.add_argument('--lang-switch', type=int, default=1e4,
                    help='how often it changes the domain (in charcters)')
parser.add_argument('--total-length', type=int, default=int(1e6),
                    help='Total expected length (number of switches is deduced from this)')
parser.add_argument('--dropout', type=float, default=0.2,
                    help='dropout applied to layers (0 = no dropout)')
parser.add_argument('--tied', action='store_true',
                    help='tie the word embedding and softmax weights')
parser.add_argument('--optimizer', type=str, default="Adam",
                    help='optimizer choice: SGD (default) or Adam')
parser.add_argument('--seed', type=int, default=1111,
                    help='random seed')
parser.add_argument('--cuda', action='store_true',
                    help='use CUDA')
parser.add_argument('--save', type=str, default='model.pt',
                    help='[Use --log-dir to set the model destination dir]')
parser.add_argument('--architecture', choices=['static', 'moe', 'static_per_domain', 'transformer'], 
                    default='moe',
                    help='Type of architecture between simple LSTM (static), '
                    'PoE (moe), Ind. LSTM (static_per_domain) and Transformer (transformer)')
parser.add_argument('--log-dir', type=str, default='logs',
                    help='Output metrics logs directory')
parser.add_argument('--cluster-run', action='store_true',
                    help='Use when this is a slurm cluster run to save logs '
                    'under different directories for each job id')
parser.add_argument('--cluster-run-name',
                    help='Store cluster runs under a common subdirectory')
parser.add_argument('--max-memory-size', type=int, default=30,
                    help='the maximum numbers of modules')
parser.add_argument('--max-ltm-size', type=int, default=None,
                    help='the maximum number of modules in the ltm. '
                    'The ltm grows incrementally until reaching full capacity')
parser.add_argument('--stm-size', type=int, default=None,
                    help='the total number of modules in the stm.')
parser.add_argument('--generate-length', type=int, default=100,
                    help='the length of the generated text')
parser.add_argument('--consolidation-period', type=float, default=None,
                    help='number of tokens after switch for cloning')
parser.add_argument('--consolidation-threshold', type=float, default=None,
                    help='weight difference to trigger a consolidation')
parser.add_argument('--weights-lstm-nhid', type=int, default=10)
parser.add_argument('--clear-lstm-hidden', action='store_true', default=False,
                    help='Reset the weights producing LSTM hidden vector')
parser.add_argument('--weights-trainer', choices=['grad', 'random', 'greedy', 'lstm', 'fixed'])
parser.add_argument('--residual-weights-trainer', choices=['grad', 'random', 'greedy', 'lstm'])
parser.add_argument('--ltm-reinstatement', choices=['fifo', 'relevance', 'none'], default = 'relevance',
                    help='policy to move from ltm to stm')
parser.add_argument('--stm-consolidation', choices=['fifo', 'relevance', 'none'], default = 'relevance',
                    help='policy to set the weights of modules entering the stm')
parser.add_argument('--weights-trainer-iterations', type=int, default=1,
                    help='how many softmax runs over the combination')
parser.add_argument('--weights-trainer-lr', type=float, default=0.001,
                    help='the learning rate of the combination layer')
parser.add_argument('--weights-trainer-annealing', type=float, default=0.0,
                    help='the annealing rate of the combination layer')
parser.add_argument('--max-sequences', type=int, default=None,
                    help='only considers the k first sequences (for debugging purposes)')
parser.add_argument('--first-sequence', type=int, default=None,
                    help='discard the first k sequences (for debugging purposes)')
parser.add_argument('--report-every', type=int, default=10,
                    help='number of batches every which to print a report in stdout')
parser.add_argument('--debug-train-weights-before-predict', action='store_true', default=False,
                    help='if the combination weights are updated before backprop')
parser.add_argument('--debug-reveal-domain', action='store_true', default=False,
                    help='give away the domain corresponding to the current sequence')
parser.add_argument('--weight-normalization', action='store_true', default=False,
                    help='if the contribution weights should be normalized')
parser.add_argument('--load-from', 
                    help='load model from a saved checkpoint (only for debugging)') 
parser.add_argument('--shadow-run', help='Compare losses to those of another run')
parser.add_argument('--log-weights', help='filename where to store the weight history')
args = parser.parse_args()

print("selected options:")
for arg in args.__dict__.items():
    print("\t".join(map(str, arg)))

if args.cluster_run:
    args.log_dir = os.path.join(args.log_dir, "cluster-run")
    if args.cluster_run_name:
        args.log_dir = os.path.join(args.log_dir, args.cluster_run_name)
    slurm_id = os.environ.get('SLURM_JOB_ID')
    args.log_dir = os.path.join(args.log_dir, slurm_id)


args.log_dir = log_utils.create_log_folder(args.log_dir)
args.save = os.path.join(args.log_dir, 'model.pt')
log_utils.write_config_file(args.log_dir, args)
gen_fout = open(args.log_dir + '/general_pp.txt', 'w')
gen_json_fout = open(args.log_dir + '/general_pp.jsonl', 'w')
detail_fout = open(args.log_dir + '/detailed_pp.txt', 'w')
generate_f = open(args.log_dir + '/generated_text.txt', 'w')

# Set the random seed manually for reproducibility.
random.seed(args.seed)
torch.manual_seed(args.seed)
np.random.seed(args.seed)
if torch.cuda.is_available():
    if not args.cuda:
        print("WARNING: You have a CUDA device, so you should probably run with --cuda")
    else:
        torch.cuda.manual_seed(args.seed)


###############################################################################
# Load data
###############################################################################

print('Creating corpus...')
corpora = data.MultiCorpora(args.data, args.model_level)

###############################################################################
# Build the model
###############################################################################

vocsize = len(corpora.vocabulary)
print('Vocabulary size:', vocsize)
print('Creating learner...')
learner = get_learner(args, vocsize)
print('Number of parameters:', learner.get_num_parameters())
if args.cuda:
    learner.cuda()
if args.load_from:
    learner.load_from(torch.load(args.load_from))

domain_switched = Observable()
timestep_updated = Observable()
learner.train_mode()
if args.log_weights:
    weight_logger = log_utils.WeightsLogger(learner, args.log_weights)
    domain_switched.register(weight_logger.domain_switched)
    timestep_updated.register(weight_logger.timestep_updated)

###############################################################################
# Training code
###############################################################################

def generate_text(sequence_id, position, sequence_type, sequence_type_name):
    learner.evaluate_mode()
    input = Variable(torch.rand(1, 1).mul(len(corpora.vocabulary)).long(), requires_grad=False)
    hidden = learner.create_hidden_states(1)
    if args.cuda:
        input.data = input.data.cuda()
    generate_f.write('\n' + sequence_type_name)
    generate_f.write('\nsequence {:5d} at {}\n'.format(sequence_id, position))
    for i in range(args.generate_length):
        if not args.debug_reveal_domain:
            output, hidden = learner.generate(input, hidden)
        else:
            output, hidden = learner.generate(input, hidden, sequence_type)
        word_weights = output.squeeze().data.exp().cpu()
        try:
            word_idx = torch.multinomial(word_weights, 1)[0]
            input.fill_(word_idx)
            word = corpora.vocabulary.idx2word[word_idx]
            generate_f.write(word)
        except:
            continue
    learner.train_mode()


if args.shadow_run:
    shadow_losses = log_utils.load_shadow_losses(args.shadow_run)
    shadow_positions = log_utils.load_shadow_positions(args.shadow_run)
num_switches = args.total_length // args.lang_switch
num_switches_per_language = num_switches // corpora.get_corpora_number()
assert args.window % args.bptt == 0, "The window size must be a multiple of bptt"
sequence_iterator = data.get_random_alternating_iterator(
        corpora, args.lang_switch, num_switches_per_language, args.window, args.batch_size,
        args.cuda)
overall_size = len(corpora)//args.batch_size
global_loss = 0
global_position = 0
loss_hist = []
global_start_time = time.time()
for sequence_index, (input_sequence, target_sequence) in enumerate(
        data.safe_iterate_sequences(sequence_iterator, args.max_sequences)):
    if args.first_sequence and sequence_index < args.first_sequence:
        # FIXME: this logic should be in the sequence iterator
        global_position += len(input_sequence)
        continue
    sequence_type = sequence_iterator.get_current_index()
    sequence_type_name = sequence_iterator.get_current_iterator().get_name()
    domain_switched(sequence_index, sequence_type, sequence_type_name)
    sequence_loss = 0
    sequence_length = len(input_sequence)
    sequence_end = global_position + sequence_length
    start_time = time.time()
    for chunk_index, (input_chunk, target_chunk) in enumerate(
            data.safe_iterate_chunks(input_sequence, target_sequence, 
                args.bptt, args.batch_size)):
        timestep_updated(chunk_index, global_position)
        batch_loss = None
        if not args.debug_reveal_domain:
            loss = learner.learn(input_chunk, target_chunk.view(-1))
        else:
            loss = learner.learn(input_chunk, target_chunk.view(-1), sequence_type)
        loss = loss.item()
        if args.shadow_run:
            shadow_index = global_position  // len(input_chunk)
            assert global_position == shadow_positions[shadow_index]
            loss -= shadow_losses[shadow_index]
        if batch_loss is None:
            batch_loss = loss
            sequence_loss += loss * len(input_chunk)
            global_loss += loss * len(input_chunk)
            loss_hist.append(loss)
        log_utils.write_general_ppl(gen_fout, gen_json_fout, args, global_position, learner.get_lr(), loss, sequence_type, sequence_type_name, sequence_index, len(input_sequence))
        #if chunk_index == 10 or chunk_index == 20:
        #    generate_text(sequence_index, f'{chunk_index} batches after switch', sequence_type, sequence_type_name)
        if chunk_index  > 0 and (chunk_index % args.report_every) == 0:
            elapsed = time.time() - start_time
            start_time = time.time()
            ppl = math.exp(batch_loss)
            print('\tseq {:4d} / {:d} (ETA {}) | pos. {:8d}/{:d} ({:5d} to end) | lr {:02.5f} | '
                    'loss {:5.2f} | ppl {:8.2f} | ms/batch {:5.2f}'.format(
                sequence_index, len(sequence_iterator), log_utils.format_eta(global_start_time, global_position, overall_size),
                global_position, overall_size, sequence_end - global_position, learner.get_lr(), batch_loss, ppl, elapsed * 1000 / args.report_every)),
            #print(", ".join(("{:.2f}".format(w) for w in learner.get_weights(input_chunk).detach().cpu().numpy())))
        global_position += len(input_chunk)
    sequence_loss /= sequence_length
    print('='*120)
    print('sequence {:4d} / {:d} ({:^10s}) | '
            'size {:5d} | loss {:5.2f} '.format(
            sequence_index, len(sequence_iterator), sequence_type_name, sequence_length, sequence_loss))
    print('='*120)
    #generate_text(sequence_index, 'the end', sequence_type, sequence_type_name)

gen_fout.close()
gen_json_fout.close()
detail_fout.close()
generate_f.close()
with open(args.save, 'wb') as f:
    torch.save(learner, f)

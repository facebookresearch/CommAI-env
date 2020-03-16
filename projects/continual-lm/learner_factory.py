# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import learner
import train_weights
def get_learner(args, vocsize):
    if args.architecture == 'static':
        return learner.StaticLearner(
            args.optimizer, args.lr, args.model, vocsize, args.emsize, args.nhid,
            args.nlayers, args.dropout, args.tied, args.batch_size, args.clip, args.learn_iterations)
    if args.architecture == 'transformer':
        return learner.TransformerLearner(
            args.optimizer, args.lr, args.model, vocsize, args.emsize, args.nhead, args.nhid,
            args.nlayers, args.dropout, args.learn_iterations, args.transformer_warmup)
    elif args.architecture == 'static_per_domain':
        return learner.StaticPerDomainLearner(
            args.optimizer, args.lr, args.model, vocsize, args.emsize, args.nhid,
            args.nlayers, args.dropout, args.tied, args.batch_size, args.clip, args.learn_iterations)
    elif args.architecture == 'clone':
        weights_trainer = get_weights_trainer(args.weights_trainer, args, vocsize)
        if args.residual_weights_trainer:
            residual_weights_trainer = get_weights_trainer(
                    args.residual_weights_trainer, args, vocsize)
        else:
            residual_weights_trainer = None
        return learner.CloneLearner(
            args.model, int(args.consolidation_period / (args.batch_size * args.bptt)) if args.consolidation_period else None, args.consolidation_threshold, vocsize, vocsize, args.emsize, args.nhid,
            args.nlayers, args.max_memory_size, args.max_ltm_size, args.stm_size, args.lr, args.batch_size, args.clip, args.optimizer,
            args.ltm_reinstatement, args.stm_consolidation, 
            args.debug_train_weights_before_predict, weights_trainer, residual_weights_trainer, 
            args.tied, is_cuda=args.cuda)
    elif args.architecture == 'moe':
        weights_trainer = get_weights_trainer(args.weights_trainer, args, vocsize)
        return learner.MoELearner(
            args.model, vocsize, vocsize, args.emsize, args.nhid,
            args.nlayers, args.max_memory_size, args.lr, args.batch_size, args.clip, args.optimizer, 
            args.debug_train_weights_before_predict, weights_trainer, args.learn_iterations, args.tied, is_cuda=args.cuda)
    else:
        raise Exception(f'{args.architecture} is not a valid architecture')

def get_weights_trainer(weights_trainer, args, vocsize):
    memory_size = args.max_memory_size
    if args.architecture == 'clone' and args.max_ltm_size != 0:
        memory_size += 1
    if weights_trainer == 'random':
        weights_trainer = train_weights.RandomSearchWeights(size=memory_size,
                random_noise=args.weights_trainer_lr, iterations=args.weights_trainer_iterations, normalized=args.weight_normalization)
    elif weights_trainer == 'grad':
        weights_trainer = train_weights.GradientWeights(size=memory_size,
                lr=args.weights_trainer_lr, annealing=args.weights_trainer_annealing,
                iterations=args.weights_trainer_iterations, normalized=args.weight_normalization)
    elif weights_trainer == 'greedy':
        weights_trainer = train_weights.GreedyWeights(size=memory_size, best_mass=0.95)
    elif weights_trainer == 'lstm':
        weights_trainer = train_weights.LSTMWeights(ntoken=vocsize, ninp=100,
                nhid=args.weights_lstm_nhid, size=memory_size, lr=args.weights_trainer_lr,
                iterations=args.weights_trainer_iterations, normalized=args.weight_normalization, clear_hidden=args.clear_lstm_hidden)
    elif weights_trainer == 'fixed':
        weights_trainer = train_weights.FixedWeights(memory_size)
    else:
        raise Exception(f'{args.weights_trainer} is not a valid weight training mechanism')
    return weights_trainer

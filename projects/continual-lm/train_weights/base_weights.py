# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
import torch.nn as nn
from numpy import mean

NUM_ITERATIONS_LOSS_SMOOTHING = 10
CONVERGENCE_THRESHOLD = 1e-4


class BaseWeights(nn.Module):
    def __init__(self, size, iterations):
        super(BaseWeights, self).__init__()
        self.weights = nn.Parameter(torch.zeros(size))  # we know we need this wiggle room 
        self.iterations = iterations
        self.n = 0  # allocated size

    def get_state(self):
        return None

    def set_state(self, _):
        pass

    def init_hidden(self, bsz):
        pass

    def predict_weights(self, inp, h):
        assert self.n <= len(self.weights)
        return self.weights[:self.n], h

    def get_weight_parameters(self, i):
        return self.weights[i]

    def set_weight_parameters(self, i, w):
        with torch.no_grad():
            self.weights[i] = w

    def set_weights(self, weights):
        with torch.no_grad():
            self.weights[:len(weights)] = weights

    def append_weight(self):
        self.n += 1
    
    def delete_weight(self, idx):
        self.n -= 1
        with torch.no_grad():
            self.weights[idx:-1] = self.weights[idx+1:]
            self.reset_weight(-1)

    def reset_weight(self, idx):
        with torch.no_grad():
            self.weights[idx] = 0

    def move_weight(self, from_idx, to_idx):
        self._move_weight(self.weights, from_idx, to_idx)

    def _move_weight(self, weights, from_idx, to_idx):
        if from_idx == to_idx:
            return
        with torch.no_grad():
            w = weights[from_idx].clone()
            if from_idx < to_idx:
                weights[from_idx:to_idx] = weights[from_idx+1:to_idx+1]
            else:
                weights[to_idx+1:from_idx+1] = weights[to_idx:from_idx]
            weights[to_idx] = w

    def do_train(self, inp, get_loss, until_convergence):
        if until_convergence:
            self.reset_weights()
        self.losses = []
        self._initialize_search(inp, get_loss)
        if self.n > 1:
            i = 0
            while (until_convergence and (not self.has_converged())) or \
                    (not until_convergence and i < self.iterations):
                self.losses.append(self._iterate_search(inp, get_loss, i))
                i += 1

    def has_converged(self):
        if len(self.losses) < 2 * NUM_ITERATIONS_LOSS_SMOOTHING:
            return False
        prev_loss = mean(self.losses[-2*NUM_ITERATIONS_LOSS_SMOOTHING:
            -NUM_ITERATIONS_LOSS_SMOOTHING])
        cur_loss = mean(self.losses[-NUM_ITERATIONS_LOSS_SMOOTHING:])
        return abs(cur_loss-prev_loss) < CONVERGENCE_THRESHOLD

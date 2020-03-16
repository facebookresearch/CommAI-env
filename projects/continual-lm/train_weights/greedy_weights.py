# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from .base_weights import BaseWeights
import torch
from torch import nn
from numpy import argmax

class GreedyWeights(BaseWeights):
    def __init__(self, size, best_mass):
        super(GreedyWeights, self).__init__(size)
        self.eye = nn.Parameter(torch.eye(size)).requires_grad_(False)
        self.best_mass = best_mass

    def optimize(self, n, get_loss, until_convergence):
        if n > 1:
            best_index = self.get_best_clone(n, get_loss)
            self.shift_weights_to_best(n, best_index)
        else:
            self.set_weight(0, 1)

    def get_best_clone(self, n, get_loss):
        losses = []
        for i in range(n):
            weight_i = self.eye[i,:n]
            losses.append(get_loss(weight_i))
        best_index = argmax(losses)
        return best_index

    def shift_weights_to_best(self, n, best_index):
        self.distribute_remaining_mass(n)
        self.set_weight(best_index, self.best_mass)

    def distribute_remaining_mass(self, n):
        remaining_mass = 1.0 - self.best_mass
        distributed_remaining_mass = remaining_mass / (n - 1)
        with torch.no_grad():
            self.weights[:n] = distributed_remaining_mass


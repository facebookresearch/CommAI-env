# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
from .base_weights import BaseWeights

class FixLastWeightTransformation(BaseWeights):
    """ Returns weights of the form \\alpha W + 1, where W are the weights
    returned by a different weight optimizer"""
    def __init__(self, weights_trainer, iterations, lr):
        super(FixLastWeightTransformation, self).__init__(1, iterations)
        self.weights_trainer = weights_trainer
        self.reset_weights()
        self.optim = torch.optim.Adam([self.weights], lr=lr)
        self.lr = lr

    def reset_weights(self):
        with torch.no_grad():
            self.weights.zero_()
        self.weights_trainer.reset_weights()

    def set_weight(self, i, w):
        raise NotImplementedError()

    def get_weights(self, n, inp):
        weights = self.weights_trainer.get_weights(n-1, inp)
        weights = self.add_fixed_weight(weights)
        return weights

    def add_fixed_weight(self, weights):
        last_weight = weights.new([1])
        rescaling = self.weights[0]
        weights = torch.cat([rescaling * weights, last_weight])
        return weights

    def _iterate_search(self, n, inp, get_loss, it):
        def get_loss2(weights):
            weights = self.add_fixed_weight(weights)
            return get_loss(weights)
        self.weights_trainer._iterate_search(n-1, inp, get_loss2, it)
        weights = self.get_weights(n, inp)
        loss = get_loss(weights)
        self.optim.zero_grad()
        loss.backward()
        self.optim.step()
        return loss.item()

    def _initialize_search(self, n, inp, get_loss):
        def get_loss2(weights):
            weights = self.add_fixed_weight(weights)
            weights.requires_grad_(True)
            return get_loss(weights)
        self.weights_trainer._initialize_search(n-1, inp, get_loss2)

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
from .base_weights import BaseWeights

class GradientWeights(BaseWeights):
    def __init__(self, size, lr, annealing, iterations, normalized):
        super(GradientWeights, self).__init__(size, iterations)
        self.reset_weights()
        self.optim = torch.optim.Adam(self.parameters(), lr=lr)
        self.lr = lr
        self.annealing = annealing
        self.normalized = normalized

    def reset_weights(self):
        with torch.no_grad():
            self.weights.uniform_(-0.1, 0.1)

    def reset_weight(self, idx):
        self.weights[idx].uniform_(-0.1, 0.1)

    def predict_weights(self, inp, h):
        weights, h = super(GradientWeights, self).predict_weights(inp, h)
        if self.normalized:
            weights = torch.nn.functional.softmax(weights, dim=0)
        weights = weights.view(-1, 1, 1, 1)
        return weights, h

    def _iterate_search(self, inp, get_loss, it):
        weights, _ = self.predict_weights(inp, None)
        loss = get_loss(weights)
        self.optim.zero_grad()
        loss.backward()
        self.optim.step()
        for g in self.optim.param_groups:
            g['lr'] = self.lr / (1 + (self.lr * it * self.annealing))
        return loss.item()

    def _initialize_search(self, inp, get_loss):
        pass

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
from .base_weights import BaseWeights

class FixedWeights(BaseWeights):
    def __init__(self, size):
        super(FixedWeights, self).__init__(size, 0)
        self.reset_weights()

    def reset_weights(self):
        with torch.no_grad():
            self.weights.fill_(1)

    def predict_weights(self, inp, h):
        weights, h = super(FixedWeights, self).predict_weights(inp, h)
        weights = weights.view(-1, 1, 1, 1)
        return weights, h

    def reset_weight(self, idx):
        pass

    def _iterate_search(self, inp, get_loss, it):
        pass

    def _initialize_search(self, inp, get_loss):
        pass

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from .base_weights import BaseWeights

class RandomSearchWeights(BaseWeights):
    def __init__(self, size, random_noise, iterations, normalized):
        super(RandomSearchWeights, self).__init__(size, iterations)
        self.weights.requires_grad = False
        self.weights.uniform_(0, 0.1)
        self.iterations = iterations
        self.random_noise = random_noise
        self.normalized = normalized

    def _initialize_search(self, n, inp, get_loss):
        weights = self.get_weights(n, inp)
        self.best_loss = get_loss(weights)
        self.candidate_weights = weights.clone().requires_grad_(False)
        self.noise_vec = self.candidate_weights.clone().zero_().requires_grad_(False)

    def _iterate_search(self, n, inp, get_loss, it):
        current_weights = self.get_weights(n, inp)
        self.candidate_weights.copy_(current_weights)
        self.candidate_weights = self._add_noise_and_normalize(
                self.candidate_weights, self.noise_vec)
        new_loss = get_loss(self.candidate_weights)
        if new_loss < self.best_loss:
            self.best_loss = new_loss
            self.set_weights(self.candidate_weights)
        return new_loss.item()

    def _add_noise_and_normalize(self, weights, noise_vec):
        noise_vec.normal_().mul_(self.random_noise)
        weights += noise_vec
        if self.normalized:
            weights.clamp_(min=0)
            weights /= weights.sum()
        return weights

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch.nn as nn

class BaseLearner(nn.Module):
    def __init__(self, criterion, vocsize, learn_iterations):
        super(BaseLearner, self).__init__()
        self.criterion = criterion
        self.learn_iterations = learn_iterations
        self.vocsize = vocsize

    def learn(self, data, targets, **kwargs):
        self.learn_kwargs = kwargs
        state = self.get_state()
        prediction, new_state = self.predict(data, state)
        first_loss = self.get_loss(prediction, targets)
        loss = first_loss
        for it in range(self.learn_iterations):
            self.train_model(loss, prediction, data, targets)
            if it < self.learn_iterations - 1:
                prediction, new_state = self.predict(data, state)
                loss = self.get_loss(prediction, targets)
        self.set_state(new_state)
        return first_loss

    def get_state(self):
        return None

    def set_state(self, state):
        pass

    def get_loss(self, prediction, targets):
        return self.criterion(prediction.view(-1, self.vocsize), targets)


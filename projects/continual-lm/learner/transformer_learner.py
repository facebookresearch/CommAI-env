# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from .base_learner import BaseLearner
import model
import torch.nn as nn
import torch.optim as optim

class TransformerLearner(BaseLearner):
    def __init__(self, optimizer, lr, model_type, vocsize, emsize, nhead, nhid, nlayers, dropout, learn_iterations, warmup):
        criterion = nn.CrossEntropyLoss()
        super(TransformerLearner, self).__init__(
            criterion, vocsize, learn_iterations)
        self.model = model.TransformerModel(
            vocsize, emsize, nhead, nhid, nlayers, dropout)
        self.dmodel = emsize
        self.lr = lr
        self.step = 1
        self.warmup = warmup
        kwargs = {}
        if lr == 42:
            if optimizer == 'Adam':
                kwargs['betas'] = (0.9, 0.98)
                kwargs['eps'] = 1e-8
            lr = self.compute_lr()
            self.auto_lr = True
        else:
            self.auto_lr = False
        self.optimizer = getattr(optim, optimizer)(self.model.parameters(), lr=lr)

    def compute_lr(self):
        return (1.0 /self.dmodel) * min(self.step**-0.5, self.step*self.warmup**-1.5)
    
    def learn(self, *args):
        if self.auto_lr:
            self.optimizer.param_groups[0]['lr'] = self.compute_lr()
            self.step += 1
        ret = super(TransformerLearner, self).learn(*args)
        return ret

    def predict(self, data, hidden):
        output = self.model(data)
        return output, hidden

    def generate(self, data, hidden):
        output = self.model(data)
        return output.view(-1, self.vocsize), None

    def train_model(self, loss, prediction, data, targets):
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def get_lr(self):
        return self.optimizer.param_groups[0]['lr']

    def get_num_parameters(self):
        return sum(p.view(-1).size(0) for p in self.model.parameters())

    def create_hidden_states(self, bsz):
        return None

    def train_mode(self):
        self.model.train()

    def evaluate_mode(self):
        self.model.eval()


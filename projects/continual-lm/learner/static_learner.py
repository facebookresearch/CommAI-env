# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import model
from model import repackage_hidden
import torch
import torch.optim as optim
import torch.nn as nn
from torch.autograd import Variable
from .base_learner import BaseLearner

class StaticLearner(BaseLearner):
    def __init__(self, optimizer, lr, model_type, vocsize, emsize, nhid, nlayers,
                 dropout, tied, batch_size, clip, learn_iterations):
        criterion = nn.CrossEntropyLoss()
        super(StaticLearner, self).__init__(criterion, vocsize, learn_iterations)
        self.model = model.OriginalRNNModel(
            model_type, vocsize, emsize, nhid, nlayers, dropout, tied)
        self.model.train()
        self.hidden = self.model.init_hidden(batch_size)
        self.vocsize = vocsize
        self.clip = clip
        self.lr = lr
        self.optimizer = getattr(optim, optimizer)(self.model.parameters(), lr=lr)

    def forward(self, data, hidden):
        output, hidden = self.model(data, hidden)
        return output, hidden

    def get_state(self):
        return repackage_hidden(self.hidden)

    def set_state(self, hidden):
        self.hidden = hidden

    def predict(self, data, hidden):
        output, hidden = self.forward(data, hidden)
        return output, hidden

    def train_model(self, loss, prediction, data, targets):
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip)
        self.optimizer.step()

    def cuda(self):
        self.model = self.model.cuda()
        try:
            self.hidden = self.hidden.cuda()
        except AttributeError:
            self.hidden = tuple(h.cuda() for h in self.hidden)

    def generate(self, data, hidden):
        hidden = repackage_hidden(hidden)
        output, hidden = self.forward(data, hidden)
        return output.view(-1, self.vocsize), hidden

    def train_mode(self):
        self.model.train()

    def evaluate_mode(self):
        self.model.eval()

    def create_hidden_states(self, sz):
        return self.model.init_hidden(sz)

    def get_num_parameters(self):
        return sum(p.view(-1).size(0) for p in self.model.parameters())


    def reset_lr(self):
        self.optimizer.param_groups[0]['lr'] = self.lr

    def get_lr(self):
        return self.optimizer.param_groups[0]['lr']


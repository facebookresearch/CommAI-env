# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
from torch import nn, optim
import model
from model import repackage_hidden
from .base_learner import BaseLearner

class StaticPerDomainLearner(BaseLearner):
    def __init__(self, optimizer_type, lr, model_type, vocsize, emsize, nhid, nlayers, dropout, tied, batch_size, clip, learn_iterations):
        criterion = nn.CrossEntropyLoss()
        super(StaticPerDomainLearner, self).__init__(criterion, vocsize, learn_iterations)
        self.models = {}
        self.hiddens = {}
        self.optimizers = {}
        self.is_cuda = False
        def create_new_rnn(self):
            m = model.OriginalRNNModel(
                model_type, vocsize, emsize, nhid, nlayers, dropout, tied)
            if self.cuda:
                m = m.cuda()
            m.train()
            optimizer = getattr(optim, optimizer_type)(m.parameters(), lr=lr)
            hidden = m.init_hidden(batch_size)
            return m, hidden, optimizer
        # hacky way for avoiding saving all arguments :)
        StaticPerDomainLearner.create_new_rnn = create_new_rnn
        self.vocsize = vocsize
        self.clip = clip

    def forward(self, data, hidden, domain_id):
        output, hidden = self.models[domain_id](data, hidden)
        return output, hidden

    def get_lr(self):
        return self.optimizers[self.last_domain_id].param_groups[0]['lr']

    def learn(self, data, targets, domain_id):
        self.last_domain_id = domain_id
        if domain_id not in self.models:
            model, hidden, optimizer = self.create_new_rnn()
            self.models[domain_id] = model
            self.hiddens[domain_id] = hidden
            self.optimizers[domain_id] = optimizer
            print('Number of parameters:', self.get_num_parameters())
        return super(StaticPerDomainLearner, self).learn(data, targets)

    def get_state(self):
        domain_id = self.last_domain_id
        return repackage_hidden(self.hiddens[domain_id])

    def set_state(self, hidden):
        domain_id = self.last_domain_id
        self.hiddens[domain_id] = hidden

    def predict(self, data, hidden):
        domain_id = self.last_domain_id
        output, hidden = self.forward(
                data, hidden, domain_id)
        return output, hidden

    def train_model(self, loss, prediction, data, targets):
        domain_id = self.last_domain_id
        self.optimizers[domain_id].zero_grad()
        loss = self.criterion(prediction.view(-1, self.vocsize), targets)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.models[domain_id].parameters(), self.clip)
        self.optimizers[domain_id].step()

    def cuda(self):
        for domain_id in self.models:
            self.model[domain_id] = self.model[domain_id].cuda()
            try:
                self.hidden[domain_id] = self.hidden[domain_id].cuda()
            except AttributeError:
                self.hidden[domain_id] = tuple(h.cuda() for h in self.hidden[domain_id])
        self.is_cuda = True

    def generate(self, data, hidden, domain_id):
        hidden = repackage_hidden(hidden)
        output, hidden = self.forward(data, hidden, domain_id)
        return output.view(-1, self.vocsize), hidden

    def train_mode(self):
        for model in self.models.values():
            model.train()

    def evaluate_mode(self):
        for model in self.models.values():
            model.eval()

    def create_hidden_states(self, sz):
        return next(iter(self.models.values())).init_hidden(sz)
    
    def get_num_parameters(self):
        return sum(p.view(-1).size(0) for rnn in self.models.values() for p in rnn.parameters())

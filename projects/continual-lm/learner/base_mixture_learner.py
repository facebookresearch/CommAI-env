# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
import torch.optim as optim
import torch.nn as nn
import model
from collections import deque
import numpy as np
from model import repackage_hidden
from .base_learner import BaseLearner
from observer import Observable
import itertools
import abc

class BaseMixtureOfRNNsLearner(BaseLearner):
    def __init__(self, rnn_type, nin, nout, ninp, nhid, nlayers,
            max_memory_size, lr, batch_size, clip, optimizer, train_weights_before_predict, weights_trainer, learn_iterations,
            tie_weights, w_window, dropout, is_cuda):
        criterion = nn.CrossEntropyLoss()
        super(BaseMixtureOfRNNsLearner, self).__init__(criterion, nout, learn_iterations)
        self.optimizer_algorithm = optimizer
        #general parameters
        self.rnn_type = rnn_type
        self.nin = nin
        self.nout = nout
        self.ninp = ninp
        self.nhid = nhid
        self.max_memory_size = max_memory_size
        self.dropout = dropout
        self.rnns = []
        self.ids = []
        self.id_count = 0
        self.lr = lr
        self.batch_size = batch_size
        self.hidden = []
        self.clip = clip
        self.window_size = w_window
        self.nlayers = nlayers
        self.train_weights_before_predict = train_weights_before_predict
        self.cuda_available = is_cuda
        self.outputs = torch.zeros(self.max_memory_size, 20, self.batch_size, self.nout)
        self.weights_trainer = weights_trainer
        self.tie_weights = tie_weights
        self.weights_added = Observable()
        self.weights_removed = Observable()
        self.weights_updated = Observable()
        self._initialize_model()

    @abc.abstractmethod
    def _initialize_model(self):
        pass

    def load_from(self, ot_model):
        #assumes that ot_model is a static_by_domain
        for i in range(len(ot_model.rnns)):
            self.rnns[i] = ot_model.rnns[i].cuda()
            self.hidden[i] = tuple(h.cuda() for h in ot_model.hidden[i])
            #self.optimizers[i] = ot_model.optimizers[i]
        #self.weights_trainer = ot_model.weights_trainer

    def cuda(self):
        for i in range(self.get_n_modules()):
            self.rnns[i] = self.rnns[i].to('cuda')
            try:
                self.hidden[i] = self.hidden[i].to('cuda')
            except AttributeError:
                self.hidden[i] = tuple(h.to('cuda') for h in self.hidden[i])
        self.outputs  = self.outputs.cuda()
        self.weights_trainer = self.weights_trainer.cuda()

    def get_state(self):
        return (self.hidden, self.weights_trainer.get_state())

    def set_state(self, state):
        self.hidden, weights_hidden = state
        self.weights_trainer.set_state(weights_hidden)

    def predict(self, data, hidden):
        hidden, weights_hidden = hidden
        outputs, hidden = self.forward_all_modules(hidden, data)
        self.last_outputs = outputs
        if self.train_weights_before_predict:
            self.train_weights(data, outputs, targets, weights_hidden, until_convergence=True)
        weights, weights_hidden = self.predict_weights(data, weights_hidden) 
        self.last_weights = weights
        self.weights_updated(weights.reshape(-1))
        prediction = self.get_prediction(weights.detach(), outputs.detach())
        return prediction, (hidden, weights_hidden)
    
    #def predict_and_compute_loss(self, data, targets):
    #    outputs, self.hidden = self.forward_all_modules(self.hidden, data)
    #    loss = self.get_loss(prediction, targets)
    #    return loss, prediction, outputs

    def predict_weights(self, data, weights_hidden):
        weights, weights_hidden = self.weights_trainer.predict_weights(data, weights_hidden)
        return weights, weights_hidden

    def train_weights(self, data, outputs, targets, until_convergence=False):
        get_loss = self.get_loss_closure(data, outputs, targets)
        self.weights_trainer.do_train(data, get_loss, until_convergence)

    def get_loss_closure(self, data, outputs, targets):
        def get_loss(weights):
            prediction = self.get_prediction(weights, outputs.detach())
            loss = self.get_loss(prediction, targets)
            return loss
        return get_loss

    def get_prediction(self, weights, outputs):
        weighted_out = weights * outputs
        prediction = torch.sum(weighted_out, 0)
        return prediction

    def generate(self, data, hidden):
        """it passes the input through all the modules, and returns the weighted sum of the predictions
        """
        hidden, weights_hidden = hidden
        outputs, hidden = self.forward_all_modules(hidden, data)
        weights, weights_hidden = self.predict_weights(data, weights_hidden)
        prediction = self.get_prediction(weights, outputs)
        return prediction.view(-1, self.nout), (hidden, weights_hidden)

    def forward_all_modules(self, hidden, data):
        n_modules = self.get_n_modules()
        self.outputs = self.outputs.detach()
        for i in range(n_modules):
            _, hidden[i] = self.forward_module(i, hidden[i], data)
        return self.get_outputs(), hidden

    def get_outputs(self):
        n_modules = self.get_n_modules()
        return self.outputs[:n_modules]

    def forward_module(self, i, hidden, data):
        hidden = repackage_hidden(hidden)
        output, hidden = self.rnns[i].forward(data, hidden)
        self.outputs[i,:,:,:,] = output
        return output, hidden

    def _create_new_rnn(self):
        new_rnn = model.OriginalRNNModel(self.rnn_type, self.nin, self.ninp, self.nhid, self.nlayers, self.dropout, self.tie_weights)
        if self.training:
            new_rnn.train()
        if self.cuda_available:
            new_rnn = new_rnn.cuda()
        self.rnns.append(new_rnn)
        self.ids.append(str(self.id_count))
        self.id_count += 1
        module_idx = len(self.rnns) - 1
        self.weights_trainer.append_weight()
        self.weights_added(module_idx, self.weights_trainer.get_weight_parameters(module_idx))
        self._expand_hidden_vector()
        return module_idx

    def _delete_rnn(self, module_idx):
        del self.ids[module_idx]
        del self.rnns[module_idx]
        del self.hidden[module_idx]
        self.weights_trainer.delete_weight(module_idx)
        self.weights_removed(module_idx)
        return module_idx

    def _expand_hidden_vector(self):
        new_hidden = self.rnns[-1].init_hidden(self.batch_size)
        self.hidden.append(new_hidden)

    def get_n_modules(self):
        return len(self.rnns)

    def create_hidden_states(self, bsz):
        hidden = []
        for i in range(self.get_n_modules()):
            hidden.append(self.rnns[i].init_hidden(bsz))
        return (hidden, self.weights_trainer.init_hidden(bsz))

    def evaluate_mode(self):
        self.eval()
        for i in range(self.get_n_modules()):
            self.rnns[i].eval()

    def train_mode(self):
        self.train()
        for i in range(self.get_n_modules()):
            self.rnns[i].train()

    def get_num_parameters(self):
        return sum(p.view(-1).size(0) for rnn in self.rnns for p in rnn.parameters())


# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
import torch.optim as optim
import torch.nn as nn
from torch.autograd import Variable
import model


# NOTE: import BlockRNN from the CommAI codebase
import sys
import os.path
import old_optim as my_optim
from collections import deque
import numpy as np
import math

def repackage_hidden(h):
    """Wraps hidden states in new Variables, to detach them from their history."""
    if isinstance(h, Variable):
        return Variable(h.data)
    else:
        return tuple(repackage_hidden(v) for v in h)


class BaseLearner(object):
    def __init__(self, model, optimizer, criterion, batch_size, vocsize, clip):
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.hidden = model.init_hidden(batch_size)
        self.vocsize = vocsize
        self.clip = clip

        # Turn on training mode which enables dropout.
        self.model.train()

    def learn(self, data, targets):
        # Starting each batch, we detach the hidden state
        # from how it was previously produced.
        # If we didn't, the model would try backpropagating
        # all the way to start of the dataset.
        #print('I am in baselearner learn')
        self.hidden = repackage_hidden(self.hidden)
        self.optimizer.zero_grad()

        output, self.hidden = self.forward(data, self.hidden)
        #print('output')
        #print(output.size())
        #print(output.view(-1, self.vocsize).size())
        loss = self.criterion(output.view(-1, self.vocsize), targets)
        loss.backward()
        # `clip_grad_norm` helps prevent the exploding gradient
        # problem in RNNs / LSTMs.
        torch.nn.utils.clip_grad_norm(self.model.parameters(), self.clip)
        self.optimizer.step()

        return loss, output.view(-1, self.vocsize)

    def cuda(self):
        self.model = self.model.cuda()
        try:
            self.hidden = self.hidden.cuda()
        except AttributeError:
            self.hidden = tuple(h.cuda() for h in self.hidden)

    def evaluate(self, data, targets):
        self.hidden = repackage_hidden(self.hidden)
        output, self.hidden = self.forward(data, self.hidden)
        #print('output')
        #print(output.size())
        #print(output.view(-1, self.vocsize).size())
        loss = self.criterion(output.view(-1, self.vocsize), targets)
        return loss, output.view(-1, self.vocsize)

    def generate(self, data, hidden):
        hidden = repackage_hidden(hidden)
        output, hidden = self.forward(data, hidden)
        return output.view(-1, self.vocsize), hidden

class StaticLearner(BaseLearner):
    def __init__(self, optimizer, lr, model_type, vocsize, emsize, nhid, nlayers,
                 dropout, tied, batch_size, clip):
        m = model.OriginalRNNModel(
            model_type, vocsize, emsize, nhid, nlayers, dropout, tied)
        criterion = nn.CrossEntropyLoss()
        self.lr = lr
        optimizer = getattr(optim, optimizer)(m.parameters(), lr=lr)

        super(StaticLearner, self).__init__(
            m, optimizer, criterion, batch_size, vocsize, clip)

    def forward(self, data, hidden):
        output, hidden = self.model(data, hidden)
        return output, hidden


    def reset_lr(self):
        self.optimizer.param_groups[0]['lr'] = self.lr

    def get_lr(self):
        return self.optimizer.param_groups[0]['lr']


class CloneLearner(nn.Module):
    """
    Implements a module that contains multiple RNNLM instances.

    The module takes the input, passes it through different models and it
    combines different results for a final prediction.

    It has the ability to create new instances, freeze previous ones.

    :param rnn_type - the type of each rnn. It can be LSTM, GRU, RNN_TANH
    :param nin - the size of the input, output (vocabulary size)
    :param nout - same
    :param ninp - the size of input embedding
    :param nhid - size of hidden layers
    :param nblocks - maximum numbr of clones that the learner can have
    :param batch_size
    :param clip
    :param w_window - number of previous batches used to update w_i
    """
    def __init__(self, rnn_type, nin, nout, ninp, nhid, nlayers, nblocks, lr, batch_size,
                 clip, random_noise, random_search, second_lr, optimizer,
                 deallocation, comb_iterations, comb_backprop,
                 w_window=20, dropout=0.2, parent=None, ponder=1, is_cuda = True):
        super(CloneLearner, self).__init__()
        self.random_search = random_search
        self.optimizer = optimizer
        #necesary for softmax combination
        if self.random_search == False:
            self.comb = model.CloneComb()
            self.comb = self.comb.to('cuda')
            if self.optimizer == 'Adam':
                self.comb_optim = torch.optim.Adam(self.comb.parameters(), lr=second_lr)
            else:
                self.comb_optim = torch.optim.SGD(self.comb.parameters(), lr=second_lr)
        #general parameters
        self.rnn_type = rnn_type
        self.nin = nin
        self.nout = nout
        self.ninp = ninp
        self.nhid = nhid
        self.nblocks = nblocks
        self.dropout = dropout
        self.rnns = []
        self.optimizers = []
        self.curr_clone = 0
        self.lr = lr
        self.second_lr = second_lr
        self.batch_size = batch_size
        self.hidden = []
        self.block_w = []
        self.m_tracking = []
        self.clip = clip
        self.criterion = nn.CrossEntropyLoss()
        self.window_size = w_window
        self.nlayers = nlayers
        self.deallocation = deallocation
        self.comb_iterations = comb_iterations
        self.comb_backprop = comb_backprop
        #necessary for random search
        self.w_distr = [0.0] * self.nblocks
        self.noise = random_noise
        self.random_samples = 100
        self.cuda_available = is_cuda
        self.outputs = torch.zeros(self.nblocks, 20, self.batch_size, self.nout).to('cuda')
        np.random.seed(1111)
        self.gen_outputs = torch.zeros(self.nblocks, 1, 1, self.nout).to('cuda')
        self.create_new_rnn()
        self.last_layer_id = self.get_last_layer_id()

    def cuda(self):
        """makes the last clone cuda compatible"""
        print('new clone cuda')
        curr_clone = len(self.rnns) - 1
        self.rnns[-1] = self.rnns[-1].to('cuda')
        try:
            self.hidden[-1] = self.hidden[-1].to('cuda')
        except AttributeError:
            self.hidden[-1] = tuple(h.to('cuda') for h in self.hidden[-1])

    def get_last_layer_id(self):
        count = 0
        for i, param in enumerate(self.rnns[-1].parameters()):
            count += 1
        return count - 1


    def reset_lr(self):
        for i in range(len(self.optimizers)):
            self.optimizers[i].param_groups[0]['lr'] = self.lr

    def set_lr(self):
        for i in range(len(self.optimizers)):
            self.optimizers[i].param_groups[0]['lr'] = self.lr / self.w_distr[i]

    def create_hidden_states(self, bsz):
        hidden = []
        for i in range(len(self.rnns)):
            hidden.append(self.rnns[i].init_hidden(bsz))
        return hidden

    def delete_rnn(self, best_clone):
        if self.deallocation == 'fifo':
            clone_ind = 0
        else:
            clone_ind = best_clone
        del self.rnns[clone_ind]
        del self.block_w[clone_ind]
        del self.hidden[clone_ind]
        del self.optimizers[clone_ind]
        del self.m_tracking[clone_ind]
        if self.random_search == 0:
            self.comb.delete_clone()
        return clone_ind


    def learn(self, data, targets):
        """it passes the input through all the clones, backpropagates
        through the last one, and returns the weighted sum of the predictions
        """
        for i in range(len(self.hidden)):
            self.hidden[i] = repackage_hidden(self.hidden[i])
        #for param in self.rnns[0].parameters():
        #    print(param.data)
        #output, self.hidden, outs = self.forward(data, self.hidden)
        outs = []
        new_hidden = []
        for i in range(len(self.rnns)):
            #print(i)
            #print(len(self.rnns))
            self.optimizers[i].zero_grad()
            data = data.to('cuda')
            targets = targets.to('cuda')
            output, new_h = self.rnns[i].forward(data, self.hidden[i])
            #outs.append(self.block_w[i] * output.cpu())
            new_hidden.append(new_h)
            loss = self.criterion(output.view(-1, self.nout), targets)
            #self.m_tracking[i].append(math.exp(loss.data))
            if i == (len(self.rnns) - 1) and  self.comb_backprop == 0:
                #print(i)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.rnns[i].parameters(), self.clip)
                self.optimizers[i].step()
                #print(output.shape)
                self.optimizers[i].zero_grad()
            self.outputs[i,:,:,:,] = output
        self.hidden = new_hidden
        weights = torch.Tensor(self.w_distr).to('cuda')
        weights = weights.reshape(len(self.w_distr), 1, 1, 1)
        weighted_out = weights * self.outputs
        pred = torch.sum(weighted_out, 0)
        total_loss = self.criterion(pred.view(-1, self.nout), targets)
        if self.comb_backprop:
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.rnns[len(self.rnns) - 1].parameters(), self.clip)
            self.optimizers[len(self.rnns) - 1].step()
        self.outputs.detach_()
        if self.random_search:
            self.w_distr = self.run_random_search(targets, total_loss)
            for i in range(len(self.rnns)):
                self.m_tracking[i].append(self.w_distr[i])
            self.update_w_vals()
            #print(self.w_distr)
        else:
            it_nr = 0
            self.comb_optim.zero_grad()
            best_loss = 0
            best_weights = None
            best_weights_l = None
            for it in range(self.comb_iterations):
                self.comb_optim.zero_grad()
                future_pred, future_weights, future_l = self.comb.forward(self.outputs, len(self.rnns))
                future_loss = self.criterion(future_pred.view(-1, self.nout), targets)
                future_loss.backward()
                self.comb_optim.step()
                if best_loss > future_loss or it == 0:
                    best_loss = future_loss
                    best_weights = future_weights
                    best_weights_l = future_l
                    it_nr = it
            for i in range(len(self.rnns)):
                self.m_tracking[i].append(best_weights_l[i])
            self.update_w_vals()
            self.comb.set_weight(best_weights)
            self.comb_optim = torch.optim.SGD(self.comb.parameters(), lr=self.second_lr)
            self.w_distr[:len(best_weights_l)] = best_weights_l
            #print(it_nr)
        self.set_lr()
        return total_loss, pred.view(-1, self.nout)

    def normalize_weights(self, distr):
        n = len(self.rnns)
        s = sum(distr[:n])
        #if max(distr[:n]) > min(distr[:n]):
        #    distr[:n] = [(el - min(distr[:n])) / (max(distr[:n]) - min(distr[:n])) for el in distr[:n]]
        distr[:n] = [x/s for x in distr[:n]]
        return distr

    def run_random_search(self, targets, curr_loss):
        best_loss = curr_loss
        best_distr = list(self.w_distr)
        #print(self.w_distr)
        for i in range(self.random_samples):
            new_distr = list(best_distr)
            for j in range(len(self.rnns)):
                if new_distr[j] < self.noise:
                    new_distr[j] += np.random.choice([0, self.noise])
                else:
                    new_distr[j] += np.random.choice([-self.noise, 0, self.noise])
            new_distr = self.normalize_weights(new_distr)
            wrong_direction = 0
            for j in range(len(self.rnns)):
                if new_distr[j] > 1.0 or new_distr[j] < 0.0:
                    wrong_direction = 1
            if wrong_direction == 0:
                new_weights = torch.Tensor(new_distr).to('cuda')
                new_weights = new_weights.reshape(len(self.w_distr), 1, 1, 1)
                weighted_out = new_weights * self.outputs
                new_outs = torch.sum(weighted_out, 0)
                new_loss = self.criterion(new_outs.view(-1, self.nout), targets)
                if new_loss < best_loss:
                    best_loss = new_loss
                    best_distr = new_distr
        return best_distr


    def evaluate_mode(self):
        #self.comb.eval()
        for i in range(len(self.rnns)):
            self.rnns[i].eval()

    def train_mode(self):
        #self.comb.train()
        for i in range(len(self.rnns)):
            self.rnns[i].train()

    def evaluate(self, data, targets):
        """it passes the input through all the clones, and returns the weighted sum of the predictions
        """
        for i in range(len(self.hidden)):
            self.hidden[i] = repackage_hidden(self.hidden[i])
        #for param in self.rnns[0].parameters():
        #    print(param.data)
        #output, self.hidden, outs = self.forward(data, self.hidden)
        outs = []
        new_hidden = []
        for i in range(len(self.rnns)):
            self.optimizers[i].zero_grad()
            data = data.to('cuda')
            output, new_h = self.rnns[i].forward(data, self.hidden[i])
            #outs.append(self.block_w[i] * output.cpu())
            new_hidden.append(new_h)
            #loss = self.criterion(output.view(-1, self.nout), targets.cpu())
            #self.m_tracking[i].append(math.exp(loss.data))
            self.outputs[i,:,:,:,] = output.cpu().detach()
        self.hidden = new_hidden
        #self.comb_optim.zero_grad()
        if self.random_search:
            weights = torch.Tensor(self.w_distr)
            weights = weights.reshape(len(self.w_distr), 1, 1, 1)
            weighted_out = weights * self.outputs
            pred = torch.sum(weighted_out, 0)
            total_loss = self.criterion(pred.view(-1, self.nout), targets.cpu())
            #self.w_distr = self.run_random_search(targets, total_loss)
        else:
            self.comb_optim.zero_grad()
            pred, weights = self.comb.forward(self.outputs, len(self.rnns))
            total_loss = torch.nn.CrossEntropyLoss()(pred.view(-1, self.nout), targets.cpu())

        return total_loss, pred.view(-1, self.nout)

    def generate(self, data, hidden):
        """it passes the input through all the clones, and returns the weighted sum of the predictions
        """
        for i in range(len(hidden)):
            hidden[i] = repackage_hidden(hidden[i])
        #for param in self.rnns[0].parameters():
        #    print(param.data)
        #output, self.hidden, outs = self.forward(data, self.hidden)
        outs = []
        new_hidden = []
        for i in range(len(self.rnns)):
            self.optimizers[i].zero_grad()
            data = data.to('cuda')
            #targets = targets.to('cuda:' + str((i + 1) %2))
            output, new_h = self.rnns[i].forward(data, hidden[i])
            #outs.append(self.block_w[i] * output.cpu())
            new_hidden.append(new_h)
            #loss = self.criterion(output.view(-1, self.nout), targets)
            #self.m_tracking[i].append(math.exp(loss.data))
            self.gen_outputs[i,:,:,:,] = output.detach()
        #self.comb_optim.zero_grad()
        if self.random_search:
            weights = torch.Tensor(self.w_distr).to('cuda')
            weights = weights.reshape(len(self.w_distr), 1, 1, 1)
            weighted_out = weights * self.gen_outputs
            #print(weights)
            #print(self.gen_outputs[0,:,:,:,])
            pred = torch.sum(weighted_out, 0)
        else:
            pred, weights, weights_l = self.comb.forward(self.gen_outputs, len(self.rnns))

        return pred.view(-1, self.nout), new_hidden

    def add_block_w(self, clone_ind = -1):
        """adds a weight value for a new clone"""
        if clone_ind == -1:
            self.block_w.append(1.0)
        else:
            self.block_w.append(self.block_w[clone_ind])
        s = sum(self.block_w)
        self.block_w = [x/s for x in self.block_w]

    def create_new_rnn(self, clone_ind=-1):
        """ creates a new rnn
        if it is the first one it is initialized randomly
        otherwise it copies the weights and the optimizer from the source RNN
        it freezes the previous clone and it adds the new one to the list of clones
        """
        #clone_ind = len(self.rnns) - 1
        new_rnn = model.OriginalRNNModel(self.rnn_type, self.nin, self.ninp, self.nhid, self.nlayers, self.dropout)
        if self.cuda_available:
            new_rnn = new_rnn.to('cuda')
        #print(clone_ind)
        #print(self.rnns)
        if clone_ind == -1:
            new_rnn.init_hidden(self.batch_size)
            if self.optimizer == 'Adam':
                new_opt = torch.optim.Adam(new_rnn.parameters(), lr=self.lr)
            else:
                new_opt = torch.optim.SGD(new_rnn.parameters(), lr=self.lr)
        else:
            new_rnn.load_state_dict(self.rnns[clone_ind].state_dict())
            if self.optimizer == 'Adam':
                new_opt = torch.optim.Adam(new_rnn.parameters(), lr=self.lr)
            else:
                new_opt = torch.optim.SGD(new_rnn.parameters(), lr=self.lr)
            new_opt.load_state_dict(self.optimizers[clone_ind].state_dict())
            for state in new_opt.state.values():
                for k, v in state.items():
                    if isinstance(v, torch.Tensor):
                        #print(v)
                        state[k] = v.to('cuda')
                        #print(state[k])
            if len(self.rnns) >= 1:
                for i, param in enumerate(self.rnns[-1].parameters()):
                    param.requires_grad = False


        self.w_distr[min(len(self.rnns), self.nblocks - 1)] = 1.0
        self.rnns.append(new_rnn)
        self.optimizers.append(new_opt)
        self.add_block_w(clone_ind)
        self.hidden.append(self.rnns[-1].init_hidden(self.batch_size))
        self.m_tracking.append(deque(maxlen=self.window_size))

        if self.nblocks < len(self.rnns):
            deleted_clone = self.delete_rnn(clone_ind)
        if len(self.rnns) > 1 and self.random_search == 0:
            self.comb.add_clone()
            self.comb_optim = torch.optim.SGD(self.comb.parameters(), lr=self.second_lr)
        self.w_distr = self.normalize_weights(self.w_distr)
        self.safe_count = 0

    def update_w_vals(self):
        """updates the w values using the loss tracking values"""
        for i in range(len(self.m_tracking)):
            if sum(self.m_tracking[i]) > 0:
                #self.block_w[i] = 1.0 / (sum(self.m_tracking[i]) / len(self.m_tracking[i]))
                self.block_w[i] = sum(self.m_tracking[i]) / len(self.m_tracking[i])
            else:
                self.block_w[i] = 0.0
        s = sum(self.block_w)
        self.block_w = [x/s for x in self.block_w]

    def get_best_w(self):
        """returns the most relevant clone"""
        #return len(self.rnns) - 1
        print('clone weights: ' + str(self.block_w))
        return np.argmax(self.block_w)

    def get_lr(self):
        return self.optimizers[-1].param_groups[0]['lr']


class MoELearner(nn.Module):
    """
    Implements a module that contains multiple RNNLM instances.

    The module takes the input, passes it through different models and it
    combines different results for a final prediction.

    It has the ability to create new instances, freeze previous ones.

    :param rnn_type - the type of each rnn. It can be LSTM, GRU, RNN_TANH
    :param nin - the size of the input, output (vocabulary size)
    :param nout - same
    :param ninp - the size of input embedding
    :param nhid - size of hidden layers
    :param nblocks - maximum numbr of clones that the learner can have
    :param batch_size
    :param clip
    :param w_window - number of previous batches used to update w_i
    """
    def __init__(self, rnn_type, nin, nout, ninp, nhid, nlayers, nblocks, lr, batch_size,
                 clip, random_noise, random_search, second_lr, optimizer,
                 deallocation, comb_iterations, w_window=20, dropout=0.2, parent=None, ponder=1, is_cuda = True):
        super(MoELearner, self).__init__()
        self.random_search = random_search
        self.opt = optimizer
        #necesary for softmax combination
        if self.random_search == 0:
            self.comb = model.MoeComb(nblocks)
            self.comb = self.comb.to('cuda')
            if self.opt == 'Adam':
                self.comb_optim = torch.optim.Adam(self.comb.parameters(), lr=second_lr)
            else:
                self.comb_optim = torch.optim.SGD(self.comb.parameters(), lr=second_lr)
        if self.random_search == -1:
            self.comb = model.LSTMComb(rnn_type, nin, ninp, nhid, nlayers, nblocks, dropout)
            self.comb = self.comb.to('cuda')
            if self.opt == 'Adam':
                self.comb_optim = torch.optim.Adam(self.comb.parameters(), lr=second_lr)
            else:
                self.comb_optim = torch.optim.SGD(self.comb.parameters(), lr=second_lr)
            self.comb_hidden = self.comb.init_hidden(batch_size)
        #general parameters
        self.rnn_type = rnn_type
        self.nin = nin
        self.nout = nout
        self.ninp = ninp
        self.nhid = nhid
        self.nblocks = nblocks
        self.dropout = dropout
        self.rnns = []
        self.optimizers = []
        self.curr_clone = 0
        self.lr = lr
        self.second_lr = second_lr
        self.batch_size = batch_size
        self.hidden = []
        self.clip = clip
        self.criterion = nn.CrossEntropyLoss()
        self.window_size = w_window
        self.nlayers = nlayers
        self.deallocation = deallocation
        self.comb_iterations = comb_iterations
        #necessary for random search
        self.w_distr = [1.0 / self.nblocks] * self.nblocks
        self.noise = random_noise
        self.random_samples = 100
        self.cuda_available = is_cuda
        self.outputs = torch.zeros(self.nblocks, 20, self.batch_size, self.nout).cuda()
        np.random.seed(1111)
        self.gen_outputs = torch.zeros(self.nblocks, 1, 1, self.nout)
        self.create_new_rnn()
        self.last_layer_id = self.get_last_layer_id()

    def cuda(self):
        """makes the last clone cuda compatible"""
        print('new clone cuda')
        curr_clone = len(self.rnns) - 1
        self.rnns[-1] = self.rnns[-1].to('cuda')
        try:
            self.hidden[-1] = self.hidden[-1].to('cuda')
        except AttributeError:
            self.hidden[-1] = tuple(h.to('cuda') for h in self.hidden[-1])

    def get_last_layer_id(self):
        count = 0
        for i, param in enumerate(self.rnns[-1].parameters()):
            count += 1
        return count - 1


    def reset_lr(self):
        self.optimizer.param_groups[0]['lr'] = self.lr

    def create_hidden_states(self, bsz):
        hidden = []
        for i in range(len(self.rnns)):
            hidden.append(self.rnns[i].init_hidden(bsz))
        return hidden



    def learn(self, data, targets):
        """it passes the input through all the clones, backpropagates
        through the last one, and returns the weighted sum of the predictions
        """
        for i in range(len(self.hidden)):
            self.hidden[i] = repackage_hidden(self.hidden[i])
        new_hidden = []
        self.optimizer.zero_grad()
        for i in range(len(self.rnns)):
            data = data.to('cuda')
            targets = targets.to('cuda')
            output, new_h = self.rnns[i].forward(data, self.hidden[i])
            new_hidden.append(new_h)
            #print(output.shape)
            #self.optimizers[i].zero_grad()
            self.outputs[i,:,:,:,] = output
        #print(len(self.w_distr))
        weights = torch.Tensor(self.w_distr).cuda()
        weights = weights.reshape(len(self.w_distr), 1, 1, 1)
        weighted_out = weights.to('cuda') * self.outputs.to('cuda')
        pred = torch.sum(weighted_out, 0)
        total_loss = self.criterion(pred.view(-1, self.nout), targets)
        total_loss.backward()
        for i in range(len(self.rnns)):
            torch.nn.utils.clip_grad_norm_(self.rnns[i].parameters(), self.clip)
        #print('pass 0')
        self.optimizer.step()
        #print('pass 1')
        self.hidden = new_hidden
        self.outputs.detach_()
        if self.random_search == -1:
            for it in range(self.comb_iterations):
                self.comb_hidden = repackage_hidden(self.comb_hidden)
                self.comb_optim.zero_grad()
                #print(list(self.comb.parameters())[0])
                data = data.to('cuda').detach()
                #print(self.outputs.shape)
                new_pred, w_distr, self.comb_hidden = self.comb.forward(data, self.outputs, self.comb_hidden)
                #weights = torch.Tensor(self.w_distr).cuda()
                future_loss = self.criterion(new_pred.view(-1, self.nout), targets)
                future_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.comb.parameters(), self.clip)
                self.comb_optim.step()
                self.w_distr = w_distr.tolist()
                #print(self.w_distr)
                #for i in range(len(self.rnns)):
                #    self.m_tracking[i].append(weights[i])
            #self.update_w_vals()
        elif self.random_search == 1:
            self.w_distr = self.run_random_search(targets, total_loss)
        else:
            for it in range(self.comb_iterations):
                self.comb_optim.zero_grad()
                #print(list(self.comb.parameters())[0])
                future_pred, self.w_distr = self.comb.forward(self.outputs.to('cuda'), len(self.rnns))
                future_loss = self.criterion(future_pred.view(-1, self.nout), targets)
                future_loss.backward()
                #print(self.w_distr)
                #torch.nn.utils.clip_grad_norm_(self.comb.parameters(), self.clip)
                self.comb_optim.step()
            #for i in range(len(self.rnns)):
            #    self.m_tracking[i].append(weights[i])
            #self.update_w_vals()
        return total_loss, pred.view(-1, self.nout)

    def normalize_weights(self, distr):
        n = len(self.rnns)
        s = sum(distr[:n])
        #if max(distr[:n]) > min(distr[:n]):
        #    distr[:n] = [(el - min(distr[:n])) / (max(distr[:n]) - min(distr[:n])) for el in distr[:n]]
        distr[:n] = [x/s for x in distr[:n]]
        return distr

    def run_random_search(self, targets, curr_loss):
        best_loss = curr_loss
        best_distr = list(self.w_distr)
        #print(self.w_distr)
        for i in range(self.random_samples):
            new_distr = list(best_distr)
            for j in range(len(self.rnns)):
                if new_distr[j] < self.noise:
                    new_distr[j] += np.random.choice([0, self.noise])
                else:
                    new_distr[j] += np.random.choice([-self.noise, 0, self.noise])
            new_distr = self.normalize_weights(new_distr)
            wrong_direction = 0
            for j in range(len(self.rnns)):
                if new_distr[j] > 1.0 or new_distr[j] < 0.0:
                    wrong_direction = 1
            if wrong_direction == 0:
                new_weights = torch.Tensor(new_distr).to('cuda')
                new_weights = new_weights.reshape(len(self.w_distr), 1, 1, 1)
                weighted_out = new_weights * self.outputs
                new_outs = torch.sum(weighted_out, 0)
                new_loss = self.criterion(new_outs.view(-1, self.nout), targets)
                if new_loss < best_loss:
                    best_loss = new_loss
                    best_distr = new_distr
        return best_distr


    def evaluate_mode(self):
        #self.comb.eval()
        for i in range(len(self.rnns)):
            self.rnns[i].eval()

    def train_mode(self):
        #self.comb.train()
        for i in range(len(self.rnns)):
            self.rnns[i].train()


    def generate(self, data, hidden):
        """it passes the input through all the clones, and returns the weighted sum of the predictions
        """
        for i in range(len(hidden)):
            hidden[i] = repackage_hidden(hidden[i])
        #for param in self.rnns[0].parameters():
        #    print(param.data)
        #output, self.hidden, outs = self.forward(data, self.hidden)
        outs = []
        new_hidden = []
        self.optimizer.zero_grad()
        for i in range(len(self.rnns)):
            data = data.to('cuda')
            output, new_h = self.rnns[i].forward(data, hidden[i])
            new_hidden.append(new_h)
            #loss = self.criterion(output.view(-1, self.nout), targets)
            #self.m_tracking[i].append(math.exp(loss.data))
            self.gen_outputs[i,:,:,:,] = output.cpu().detach()
        #self.comb_optim.zero_grad()
        weights = torch.Tensor(self.w_distr).to('cuda')
        weights = weights.reshape(len(self.w_distr), 1, 1, 1)
        weighted_out = weights.to('cuda') * self.gen_outputs.to('cuda')
        pred = torch.sum(weighted_out, 0)
        return pred.view(-1, self.nout), new_hidden


    def create_new_rnn(self, clone_ind=-1):
        """ creates a new rnn
        if it is the first one it is initialized randomly
        otherwise it copies the weights and the optimizer from the source RNN
        it freezes the previous clone and it adds the new one to the list of clones
        """
        #clone_ind = len(self.rnns) - 1
        params = []
        for i in range(self.nblocks):
            new_rnn = model.OriginalRNNModel(self.rnn_type, self.nin, self.ninp, self.nhid, self.nlayers, self.dropout)
            if self.cuda_available:
                new_rnn = new_rnn.to('cuda')
            new_rnn.init_hidden(self.batch_size)
            #params.append(new_rnn.parameters())
            self.rnns.append(new_rnn)
            self.hidden.append(self.rnns[-1].init_hidden(self.batch_size))
            for i, param in enumerate(self.rnns[-1].parameters()):
                params.append(param)
        self.optimizer = torch.optim.SGD(params, lr = self.lr)


    def get_lr(self):
        return self.optimizer.param_groups[0]['lr']

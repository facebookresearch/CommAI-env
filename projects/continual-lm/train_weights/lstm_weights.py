# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
from torch import nn
from .base_weights import BaseWeights

class LSTMWeights(BaseWeights):
    def __init__(self, ntoken, ninp, nhid, size, lr, iterations, normalized, 
            clear_hidden):
        super(LSTMWeights, self).__init__(size, iterations)
        self.nlayers = 1
        self.encoder = nn.Embedding(ntoken, ninp)
        self.rnn = nn.LSTM(ninp, nhid, self.nlayers)
        self.decoder = nn.Linear(nhid, size)
        self.optim = torch.optim.Adam(self.parameters(), lr=lr)
        self.decoder_optim = torch.optim.Adam(self.decoder.parameters(), lr=lr)
        self.init_weights()
        self.nhid = nhid
        self.normalized = normalized
        self.n = 0
        self.hidden = None
        self.clear_hidden = clear_hidden
        self.cached_weights_uid = None

    def get_state(self):
        return self.hidden

    def set_state(self, hidden):
        self.hidden = hidden

    def init_weights(self):
        initrange = 0.1
        self.encoder.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.fill_(0)
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def delete_weight(self, idx):
        self.n -= 1
        with torch.no_grad():
            self.decoder.weight[idx:-1] = self.decoder.weight[idx+1:]
            self.decoder.bias[idx:-1] = self.decoder.bias[idx+1:]
            self.reset_weight(-1)

    def reset_weight(self, idx):
        initrange = 0.1
        with torch.no_grad():
            self.decoder.bias[idx].fill_(0)
            self.decoder.weight[idx].uniform_(-initrange, initrange)

    def move_weight(self, from_idx, to_idx):
        self._move_weight(self.decoder.weight, from_idx, to_idx)
        self._move_weight(self.decoder.bias, from_idx, to_idx)

    def get_weight_parameters(self, idx):
        return (self.decoder.weight[idx], self.decoder.bias[idx])

    def set_weight_parameters(self, idx, wp):
        with torch.no_grad():
            decoder_weight, decoder_bias = wp
            self.decoder.weight[idx] =  decoder_weight
            self.decoder.bias[idx] = decoder_bias

    def get_inp_uid(self, inp):
        return hash(tuple(inp.view(-1)[0:10].cpu()))

    def predict_weights(self, inp, hidden):
        inp_uid = self.get_inp_uid(inp)
        #if self.cached_weights_uid  is not None:
        #    assert self.cached_weights_uid != inp_uid 
        self.cached_weights_uid = inp_uid
        self.output, hidden = self.get_output(inp, hidden)
        weights = self.decode_weights(self.output)
        return weights, hidden

    def get_output(self, inp, hidden):
        bsz = inp.shape[1]
        hidden = self.get_hidden(bsz, hidden)
        emb = self.encoder(inp)
        with torch.no_grad():
            self.rnn.state_dict()['bias_ih_l0'].fill_(0)
            self.rnn.state_dict()['bias_hh_l0'].fill_(0)
        output, hidden = self.rnn(emb, hidden)
        return output, hidden

    def decode_weights(self, output):
        with torch.no_grad():
            self.decoder.bias.fill_(0)
        weights = self.decoder(output)
        weights = weights[:,:,:self.n]
        if self.normalized:
            weights = nn.functional.softmax(weights, dim=2)
        weights = weights.transpose(0, 2).transpose(1, 2)
        weights = weights.unsqueeze(3)
        return weights

    def get_hidden(self, bsz, hidden):
        if hidden is None or self.clear_hidden:
            hidden = self.init_hidden(bsz)
        hidden = tuple(h.detach() for h in hidden)
        return hidden

    def init_hidden(self, bsz):
        weight = next(self.parameters())
        return (weight.new(self.nlayers, bsz, self.nhid).zero_(),
                weight.new(self.nlayers, bsz, self.nhid).zero_())

    def _iterate_search(self, inp, get_loss, it):
        if it == 0:
            weights = self.decode_weights(self.output)
            loss = get_loss(weights)
            self.optim.zero_grad()
            loss.backward()
            self.optim.step()
            return loss.item()
        else:
            raise NotImplementedError()
            weights = self.decode_weights(self.output.detach())
            loss = get_loss(weights)
            self.decoder_optim.zero_grad()
            loss.backward()
            self.decoder_optim.step()
            return loss.item()

    def _initialize_search(self, inp, get_loss):
        pass

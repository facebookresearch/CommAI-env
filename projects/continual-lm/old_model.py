# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F

import old_util as util
from multiprocessing import Manager

import logging

initrange = 0.1


class RNN(nn.Module):
    """
    Implements an RNN learning module.

    The module consists of an input decoder, an RNN layer and and output
    decoder.

    :param rnn_type: the type of the RNN cell, e.g. LSTM.
    :param nin: the size of the input dictionary
    :param nout: the size of the output dictionary
    :param ninp: the size of the embedding vectory
    :param nhid: the size of the hidden layer
    """

    def __init__(self, rnn_type, nin, nout, ninp, nhid,
                    dropout=0.5, parent=None, ponder=1):

        super(RNN, self).__init__()

        self.encoder = nn.Embedding(nin, ninp)
        if rnn_type == 'LSTM':
            self.rnn = getattr(nn, rnn_type + 'Cell')(ninp, nhid)
        else:
            self.rnn = getattr(nn, rnn_type + 'Cell')(ninp, nhid,
                                                        nonlinearity='relu')

        self.decoder = nn.Linear(nhid, nout)

        self.rnn_type = rnn_type
        self.nhid = nhid
        self.ponder = ponder
        self.dropout = dropout
        self.nchan = 4 if rnn_type == 'LSTM' else 1

        self.init_weights(parent)

        self.logger = logging.getLogger(__name__)

    def init_weights(self, parent):
        self.encoder.weight.data.uniform_(-initrange, initrange)

        self.decoder.bias.data.fill_(0)
        self.decoder.weight.data.uniform_(-initrange, initrange)

        # Weight Inheritance
        if parent is not None:
            new_state = self.state_dict()
            old_state = parent.state_dict()

            for k in new_state:
                src, dst = old_state[k], new_state[k]

                # dst.zero_()

                if 'rnn' in k and new_state[k].size(0) > self.nhid:
                    src, dst = util.channel_view(self.nchan, src, dst)

                util.subset(src, dst).copy_(src)

    def forward(self, input, hidden):
        emb = self.encoder(input)

        for _ in range(self.ponder):
            hidden = self.rnn(emb, hidden)

        out = hidden[0] if isinstance(hidden, list) \
                            or isinstance(hidden, tuple) else hidden
        #print('lstm output')
        #print(out.data)
        if self.dropout < 1:        # NOTE no train vs test distinctions
            out = F.dropout(out)

        decoded = self.decoder(out) # NOTE TESTME: was out.view(1, out.size(0) * out.size(1))
        #print('decoder output')
        #print(decoded.squueze().size())
        return decoded.squeeze(), hidden

    def init_hidden(self, bsz):
        '''
        :param bsz: batch size
        '''
        weight = next(self.parameters()).data
        if self.rnn_type == 'LSTM':
            return (Variable(weight.new(bsz, self.nhid).zero_()),
                    Variable(weight.new(bsz, self.nhid).zero_()))
        else:
            return Variable(weight.new(bsz, self.nhid).zero_())


class BlockRNN(RNN):
    '''
    RNN that also takes a list of blocks of the form:
        [b1, ..., bn], bi = [r1, r2, c1, c2, lr]

    These blocks represent groups of parameters in the RNN's transition matrix,
    where all units in a group feed into each other.
    '''
    def __init__(self, rnn_type, nin, nout, ninp, nhid,
                    dropout=0.5, frozen_h=True, parent=None, ponder=1,
                    blocks=None, strict=True):
        super(BlockRNN, self).__init__(rnn_type, nin, nout, ninp, nhid,
                                        dropout, parent, ponder)

        assert isinstance(blocks, list)

        self.blocks = []
        self.lr_mask = None
        self.strict = strict
        self.frozen_h = frozen_h
        self.active_units = torch.ByteTensor(nhid).zero_()

        # Zero-out connections to RNN units:
        self.rnn.weight_hh.data.fill_(0)
        self.rnn.bias_hh.data.fill_(0)
        self.rnn.weight_ih.data.fill_(0)
        self.rnn.bias_ih.data.fill_(0)

        # Zero-out decoder weights (biases start out zero):
        self.decoder.weight.data.fill_(0)
        self.decoder.bias.data.fill_(0)

        # We control the learing rates in order to make sure no learning happens
        # on connections to units that are not active.
        self.lr_weight_hh = torch.FloatTensor(self.rnn.weight_hh.data.size()).zero_()
        self.lr_bias_hh = torch.FloatTensor(self.rnn.bias_hh.data.size()).zero_()
        self.lr_weight_ih = torch.FloatTensor(self.rnn.weight_ih.data.size()).zero_()
        self.lr_bias_ih = torch.FloatTensor(self.rnn.bias_ih.data.size()).zero_()
        self.lr_decoder_weight = torch.FloatTensor(
            self.decoder.weight.data.size()).zero_()
        for b in blocks or []:
            self.add_block(b)

        # NOTE sort blocks ... for convenience
        self.blocks.sort(key=lambda x: x[0])
        self.blocks.sort(key=lambda x: x[2])

        if parent:
            # inherit blocks... not necessarily needed
            pass

    def cuda(self):
        self.active_units = self.active_units.cuda()
        self.lr_weight_hh = self.lr_weight_hh.cuda()
        self.lr_bias_hh = self.lr_bias_hh.cuda()
        self.lr_weight_ih = self.lr_weight_ih.cuda()
        self.lr_bias_ih = self.lr_bias_ih.cuda()
        self.lr_decoder_weight = self.lr_decoder_weight.cuda()
        return super(BlockRNN, self).cuda()

    def forward(self, input, hidden):
        decoded, hidden = super(BlockRNN, self).forward(input, hidden)

        # All non-active units should output 0.
        hidden_non_act = (1 - self.active_units).expand_as(hidden[0])
        assert hidden[0].data[hidden_non_act].nonzero().numel() == 0

        return decoded, hidden

    def share_memory(self):
        # share block list and other BlockRNN specific properties
        self.blocks = Manager().list(self.blocks)
        self.lr_weight_hh.share_memory_()
        self.lr_bias_hh.share_memory_()
        self.lr_weight_ih.share_memory_()
        self.lr_bias_ih.share_memory_()
        self.lr_decoder_weight.share_memory_()
        self.active_units.share_memory_()

        super(BlockRNN, self).share_memory()

    def add_block(self, b, init=True):
        '''
        add a block to the model, optionally initialize the weights
        uniformly or with a closure
        '''

        self.logger.info('Adding block {}'.format(b))

        util.check_block(b, self.nhid)
        if self.strict:
            for b2 in self.blocks:
                assert not util.overlap(b, b2)
        self.blocks.append(b)

        r1, r2, c1, c2, lr = b

        if init:
            new_units = util.get_diagonal_elements_range(b)
            if new_units is None:
                # If we're not adding any new units, check that the connections
                # we add are to units that have already been initialized.
                assert self.active_units[b[0]]
            else:
                self.logger.info('Adding new units {}'.format(new_units))
                unit_from, unit_to = new_units

                self.active_units[unit_from:unit_to] = 1

                # Initialize input connections to new units
                ih = self.rnn.weight_ih.data
                ih, = util.channel_view(self.nchan, ih)
                ih[:, unit_from:unit_to, :].uniform_(-initrange, initrange)

                lr_ih = self.lr_weight_ih
                lr_ih, = util.channel_view(self.nchan, lr_ih)
                lr_ih[:, unit_from:unit_to, :].fill_(lr)

                ihb = self.rnn.bias_ih.data
                ihb, = util.channel_view(self.nchan, ihb)
                ihb[:, unit_from:unit_to].uniform_(-initrange, initrange)

                lr_ihb = self.lr_bias_ih
                lr_ihb, = util.channel_view(self.nchan, lr_ihb)
                lr_ihb[:, unit_from:unit_to, :].fill_(lr)

                # Initialize the bias of recurrent connections (weights are
                # initialized below)
                hhb = self.rnn.bias_hh.data
                hhb, = util.channel_view(self.nchan, hhb)
                hhb[:, unit_from:unit_to].uniform_(-initrange, initrange)

                # Initialize decoder connections to new units:
                dw = self.decoder.weight.data
                dw[:, unit_from:unit_to].uniform_(-initrange, initrange)
                #print('decoder matrix')
                #print(dw)
                self.lr_decoder_weight[:, unit_from:unit_to].fill_(lr)

            # Initialize hidden to hidden connections.
            # This update is the same irrespective of whether the block is
            # diagonal (adding new units) or non-diagonal (new connections
            # between previously initialized units).
            hh = self.rnn.weight_hh.data
            hh, = util.channel_view(self.nchan, hh)
            hh[:, b[0]:b[1], b[2]:b[3]].uniform_(-initrange, initrange)

            self.set_block_lr(self.get_block(b), lr)
            if len(self.blocks) > 1 and self.frozen_h:
                self.reset_block_lr(self.get_block(self.blocks[-2]))
        bidx = len(self.blocks)
        return bidx

    def get_block(self, b):
        ''' find index of a block in self.blocks (e.g. to change lr) '''
        bstr = '_'.join(map(str, b))
        lstr = ['_'.join(map(str, ll)) for ll in self.blocks]
        return lstr.index(bstr)

    def set_block_lr(self, bidx, lr):
        '''
        Sets the learning rate of the connections from hidden to hidden t+1
        '''

        block = self.blocks[bidx]
        block[-1] = lr
        r1, r2, c1, c2, lr = self.blocks[bidx]

        units = util.get_diagonal_elements_range(block)

        # All the units have already been added
        assert self.active_units[r1:r2].nonzero().numel() == r2 - r1
        assert self.active_units[c1:c2].nonzero().numel() == c2 - c1

        if units is not None:
            # We have some diagonal units
            unit_from, unit_to = units

            lr_hhb = self.lr_bias_hh
            lr_hhb, = util.channel_view(self.nchan, lr_hhb)
            lr_hhb[:, unit_from:unit_to].fill_(lr)

        lr_hh = self.lr_weight_hh
        lr_hh, = util.channel_view(self.nchan, lr_hh)
        lr_hh[:, r1:r2, c1:c2].fill_(lr)

    def reset_block_lr(self, bidx, lr = 0.0):
        '''
        Sets the learning rate of the connections from hidden to hidden t+1
        '''

        block = self.blocks[bidx]
        block[-1] = lr
        r1, r2, c1, c2, lr = self.blocks[bidx]

        units = util.get_diagonal_elements_range(block)

        # All the units have already been added
        assert self.active_units[r1:r2].nonzero().numel() == r2 - r1
        assert self.active_units[c1:c2].nonzero().numel() == c2 - c1

        if units is not None:
            # We have some diagonal units
            unit_from, unit_to = units

            lr_hhb = self.lr_bias_hh
            lr_hhb, = util.channel_view(self.nchan, lr_hhb)
            lr_hhb[:, unit_from:unit_to].fill_(lr)

        lr_hh = self.lr_weight_hh
        lr_hh, = util.channel_view(self.nchan, lr_hh)
        lr_hh[:, r1:r2, c1:c2].fill_(lr)

    def blockwise_broadcast(self, vals, t=None):
        ''' blockwise broadcast of values into an empty matrix '''

        assert len(vals) == len(self.blocks)

        result = t if t is not None else \
                        torch.zeros(self.rnn.state_dict()['weight_hh'].size())
        c_result, = util.channel_view(self.nchan, result)

        for i, b in enumerate(self.blocks):
            c_result[:, b[0]:b[1], b[2]:b[3]] = vals[i]

        return result

    def hh_active_mask(self):
        ''' mask for active weights '''
        return self.blockwise_broadcast([1 for b in self.blocks]).byte()

    def hh_nonactive_mask(self):
        return self.hh_active_mask().lt(1)

    def init_output_layer(self):
        self.decoder.bias.data.fill_(0)
        self.decoder.weight.data.uniform_(-initrange, initrange)



class GraphRNN(BlockRNN):
    '''
    A BlockRNN with connectivity between blocks based on an adjacency list (adj_list).
    (The blocks thus necessarily must be diagonal.)

    The adj_list has the form:
        [[bi, bj, lr], ...] for i != j, i, j in [0, #blocks]

        where bi -> bj is a desired edge.
    '''
    def __init__(self, rnn_type, nin, nout, ninp, nhid,
                    dropout=0.5, parent=None, ponder=1,
                    blocks=None, strict=True, adj_list=None):
        super(GraphRNN, self).__init__(rnn_type, nin, nout, ninp, nhid,
                                        dropout, parent, ponder, blocks, strict)

        # assert that blocks are on diagonal
        for b in self.blocks:
            assert b[0] == b[2] and b[1] == b[3]

        self.adj = []
        for l in adj_list or []:
            self.add_link(l)

        if type(self) == GraphRNN:
            self.rnn.state_dict()['weight_hh'][self.hh_nonactive_mask()] = 0

    def add_link(self, l, init=True):
        ''' link the blocks, by adding another block!'''
        src, dst, lr = l
        assert src != dst
        assert all([b >= 0 and b < len(self.blocks) for b in l])

        src, dst = self.blocks[src], self.blocks[dst]
        b = [max(x, y) for x, y in zip(src[0:2], dst[0:2])] + \
                [min(x, y) for x, y in zip(src[2:4], dst[2:4])]

        if src[0] > dst[0]:   # if src is before b2, transpose
            b = list(b[2:4]) + list(b[0:2])

        b += [lr]  # set lr

        self.add_block(b, init=init)

    def share_memory(self):
        # share adjacency list
        self.adj = Manager().list(self.adj)
        super(GraphRNN, self).share_memory()

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch.nn as nn
from torch.autograd import Variable
import torch
# NOTE: import BlockRNN from the CommAI codebase
import sys
import os.path
import math

from old_model import BlockRNN

from multiprocessing import Manager

def repackage_hidden(h):
    """Wraps hidden states in new Variables, to detach them from their history."""
    if isinstance(h, Variable):
        return Variable(h.data)
    else:
        return tuple(repackage_hidden(v) for v in h)



class GraphRNN2(BlockRNN):
    '''
    A BlockRNN with connectivity between blocks based on an adjacency list (adj_list).
    (The blocks thus necessarily must be diagonal.)

    The nodes list is a list of number of units and lr per block:
        [[ni, lr], ...]

    The adj_list has the form:
        [[bi, bj, lr], ...] for i != j, i, j in [0, #blocks]

        where bi -> bj is a desired edge.
    '''
    def __init__(self, rnn_type, nin, nout, ninp, max_nhid,dropout=0.5, frozen_h=True,
                 use_action_input=False, parent=None, strict=True):
        # interface: (, rnn_type, nin, nout, ninp, nhid,
        #                 dropout, parent, ponder,
        #                 blocks, strict):
        super(GraphRNN2, self).__init__(rnn_type, nin, nout, ninp, max_nhid,
                                        dropout, frozen_h, parent, 1, [], strict)

        # NOTE: we represent the nodes with an array of their comulative sizes
        # e.g.: [5, 7, 10] represents three nodes of sizes 5, 2 and 3.
        self.nodes_cum_size = []
        # maps the node ids to block ids
        self.node2block = {}
        # maps links represented as (src,dest) node id pairs
        # into the block id that impements the connection
        self.link2block = {}
        # special node id that represents all previous nodes
        self._ALL_PREV_NODES = -1  # for internal use only

        if parent:
            self.nodes_cum_size = parent.nodes_cum_size
            self.node2block = parent.node2block
            self.link2block = parent.link2block

        # NOTE: commented this code out
        if type(self) == GraphRNN2:
            self.rnn.state_dict()['weight_hh'][self.hh_nonactive_mask()] = 0

    def add_node(self, nunits, lr, init=True):
        '''Appends nunits that are fully connected to each other but not
        with the rest of the network '''
        node_id = self._add_node_limits(nunits)
        node_start, node_end = self._get_node_limits(node_id)
        # create block
        b = [node_start, node_end,  # row limits
             node_start, node_end,  # column limits
             lr]
        bidx = self.add_block(b)

        self.node2block[node_id] = bidx
        return node_id

    def _add_node_limits(self, nunits):
        '''Remembers the number of units per node'''
        self.nodes_cum_size.append(
            nunits + (self.nodes_cum_size[-1]
                      if len(self.nodes_cum_size) > 0 else 0))
        node_id = len(self.nodes_cum_size) - 1
        return node_id

    def _get_node_limits(self, node_id):
        return (self.nodes_cum_size[node_id - 1] if node_id > 0 else 0,
                self.nodes_cum_size[node_id])

    def add_link(self, src, dst, lr, init=True):
        ''' link the blocks, by adding another block!'''
        assert src != dst
        assert all([b >= 0 and b < len(self.blocks) for b in [src, dst]])

        src_lims, dst_lims = self._get_node_limits(src), \
            self._get_node_limits(dst)

        b = [dst_lims[0], dst_lims[1], src_lims[0], src_lims[1], lr]

        bidx = self.add_block(b)
        self.link2block[(src, dst)] = bidx

    def add_links_to_from_all(self, node_id, lr, init=True):
        '''Links the node with all previously added units'''
        node_start, node_end = self._get_node_limits(node_id)
        # connect all previous units to the node
        b = [node_start, node_end, 0, node_start, lr]
        bidx = self.add_block(b)
        self.link2block[(node_id, self._ALL_PREV_NODES)] = bidx
        # connect all units in the node to all previous other units
        b = [0, node_start, node_start, node_end, lr]
        bidx = self.add_block(b)
        self.link2block[(self._ALL_PREV_NODES, node_id)] = bidx

    def share_memory(self):
        # share adjacency list
        self.nodes_cum_size = Manager().list(self.nodes_cum_size)
        super(GraphRNN2, self).share_memory()

    def set_node_lr(self, node_id, lr):
        '''Sets the learning rate of the intra-node recurrent connections
        and of all the links from and to older nodes'''
        self.set_block_lr(self.node2block[node_id], lr)
        self.set_block_lr(self.link2block[(node_id, self._ALL_PREV_NODES)], lr)
        self.set_block_lr(self.link2block[(self._ALL_PREV_NODES, node_id)], lr)


class OriginalRNNModel(nn.Module):
    """Container module with an encoder, a recurrent module, and a decoder."""

    def __init__(self, rnn_type, ntoken, ninp, nhid, nlayers, dropout=0.5, tie_weights=False):
        super(OriginalRNNModel, self).__init__()
        self.drop = nn.Dropout(dropout)
        self.encoder = nn.Embedding(ntoken, ninp)
        if rnn_type in ['LSTM', 'GRU']:
            self.rnn = getattr(nn, rnn_type)(ninp, nhid, nlayers, dropout=dropout)
        else:
            try:
                nonlinearity = {'RNN_TANH': 'tanh', 'RNN_RELU': 'relu'}[rnn_type]
            except KeyError:
                raise ValueError( """An invalid option for `--model` was supplied,
                                 options are ['LSTM', 'GRU', 'RNN_TANH' or 'RNN_RELU']""")
            self.rnn = nn.RNN(ninp, nhid, nlayers, nonlinearity=nonlinearity, dropout=dropout)
        self.decoder = nn.Linear(nhid, ntoken)

        # Optionally tie weights as in:
        # "Using the Output Embedding to Improve Language Models" (Press & Wolf 2016)
        # https://arxiv.org/abs/1608.05859
        # and
        # "Tying Word Vectors and Word Classifiers: A Loss Framework for Language Modeling" (Inan et al. 2016)
        # https://arxiv.org/abs/1611.01462
        if tie_weights:
            if nhid != ninp:
                raise ValueError('When using the tied flag, nhid must be equal to emsize')
            self.decoder.weight = self.encoder.weight

        self.init_weights()

        self.rnn_type = rnn_type
        self.nhid = nhid
        self.nlayers = nlayers
        self.vocsize = ntoken

    def init_weights(self):
        initrange = 0.1
        self.encoder.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.fill_(0)
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, input, hidden):
        emb = self.drop(self.encoder(input))
        output, hidden = self.rnn(emb, hidden)
        #print('lstm output')
        #print(self.output)
        #print(self.rnn.weight_ih.data)
        output = self.drop(output)
        decoded = self.decoder(output.view(output.size(0)*output.size(1), output.size(2)))
        #print('decoder output')
        #print(decoded.data)
        return decoded.view(output.size(0), output.size(1), decoded.size(1)), hidden

    def init_hidden(self, bsz):
        weight = next(self.parameters()).data
        if self.rnn_type == 'LSTM':
            return (Variable(weight.new(self.nlayers, bsz, self.nhid).zero_()),
                    Variable(weight.new(self.nlayers, bsz, self.nhid).zero_()))
        else:
            return Variable(weight.new(self.nlayers, bsz, self.nhid).zero_())



# Temporarily leave PositionalEncoding module here. Will be moved somewhere else.
class PositionalEncoding(nn.Module):
    r"""Inject some information about the relative or absolute position of the tokens
        in the sequence. The positional encodings have the same dimension as
        the embeddings, so that the two can be summed. Here, we use sine and cosine
        functions of different frequencies.
    .. math::
        \text{PosEncoder}(pos, 2i) = sin(pos/10000^(2i/d_model))
        \text{PosEncoder}(pos, 2i+1) = cos(pos/10000^(2i/d_model))
        \text{where pos is the word position and i is the embed idx)
    Args:
        d_model: the embed dim (required).
        dropout: the dropout value (default=0.1).
        max_len: the max. length of the incoming sequence (default=5000).
    Examples:
        >>> pos_encoder = PositionalEncoding(d_model)
    """

    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        r"""Inputs of forward function
        Args:
            x: the sequence fed to the positional encoder model (required).
        Shape:
            x: [sequence length, batch size, embed dim]
            output: [sequence length, batch size, embed dim]
        Examples:
            >>> output = pos_encoder(x)
        """

        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class TransformerModel(nn.Module):
    """Container module with an encoder, a recurrent or transformer module, and a decoder."""

    def __init__(self, ntoken, ninp, nhead, nhid, nlayers, dropout=0.5):
        super(TransformerModel, self).__init__()
        try:
            from torch.nn import TransformerEncoder, TransformerEncoderLayer
        except:
            raise ImportError('TransformerEncoder module does not exist in PyTorch 1.1 or lower.')
        self.model_type = 'Transformer'
        self.src_mask = None
        self.pos_encoder = PositionalEncoding(ninp, dropout)
        encoder_layers = TransformerEncoderLayer(ninp, nhead, nhid, dropout)
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)
        self.encoder = nn.Embedding(ntoken, ninp)
        self.ninp = ninp
        self.decoder = nn.Linear(ninp, ntoken)

        self.init_weights()

    def _generate_square_subsequent_mask(self, sz):
        mask = (torch.triu(torch.ones(sz, sz)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask

    def init_weights(self):
        initrange = 0.1
        self.encoder.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.zero_()
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, src, has_mask=True):
        if has_mask:
            device = src.device
            if self.src_mask is None or self.src_mask.size(0) != len(src):
                mask = self._generate_square_subsequent_mask(len(src)).to(device)
                self.src_mask = mask
        else:
            self.src_mask = None

        src = self.encoder(src) * math.sqrt(self.ninp)
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src, self.src_mask)
        output = self.decoder(output)
        return output #F.log_softmax(output, dim=-1)


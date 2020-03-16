# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import torch
import torch.nn.functional as F
from torch.autograd import Variable


def prepare_vocab():
    vocab = (['0', '1', '.', 'p'] +  # p: pondering
             ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] +  # task codes (at most 8)
             # composition type (N, P, F), no. of bits (2: B, 3: C)
             ['N', 'P', 'F', 'B', 'C', ':', ' '])
    chardict = dict(zip(vocab, list(range(len(vocab)))))
    return vocab, chardict


def triu(m):
    # mask = torch.arange(0, m.numel()).view(m.size(0), m.size(1))
    mask = torch.ones(m.size())
    return mask.triu()


def block_mask(m, r1, r2, c1, c2):
    # mask = torch.arange(0, m.numel()).view(m.size(0), m.size(1))
    '''Note: r2 and c2 can be None, in which case the rest is included'''
    mask = torch.zeros(m.size()).byte()
    mask[r1:r2, c1:c2] = 1
    return mask


def bdiag(m, k):
    mask = torch.zeros(m.size())
    for n in range(int(min(m.size(0), m.size(1)) / k)):
        o = n * k
        mask[o: o + k, o: o + k] = 1
    return mask


def overlap(b1, b2):
    def _overlap(l1, l2):
        return l1[1] > l2[0] and l2[1] > l1[0]

    return _overlap(b1[0:2], b2[0:2]) and _overlap(b1[2:4], b2[2:4])


def check_block(b, sz):
    assert isinstance(b, list)
    assert all([isinstance(x, int) for x in b[0:4]])
    assert len(b) == 5
    r1, r2, c1, c2, _ = b
    assert r2 - r1 > 0
    assert c2 - c1 > 0

    assert r1 >= 0 and c1 >= 0

    assert r2 <= sz and c2 <= sz


def subset(src, dst):
    ''' get subset of dst that is same size as src '''
    assert src.dim() == dst.dim()
    sub = dst

    for (d, s) in enumerate(src.size()):
        sub = sub.narrow(d, 0, s)

    return sub


def outset(src, dst):
    ''' get subset of dst that is bigger than src '''
    assert src.dim() == dst.dim()
    sub = dst

    for (d, s) in enumerate(src.size()):
        sub = sub.narrow(d, s, sub.size(d) - s)

    return sub


def channel_view(nc, *args):
    return [t.view(nc, int(t.size(0) / nc), -1) for t in args]


def sample_gumbel(input):
    noise = torch.rand(input.size())
    eps = 1e-20
    noise.add_(eps).log_().neg_()
    noise.add_(eps).log_().neg_()
    return Variable(noise)


def gumbel_softmax_sample(input, hard=False):
    temperature = 10
    noise = sample_gumbel(input)
    x = (input + noise) / temperature
    x = F.softmax(x)

    if hard:
        _, max_inx = torch.max(x, x.dim() - 1)
        x_hard = torch.zeros(x.size()).scatter_(x.dim() - 1, max_inx.data, 1)
        r2 = x.clone()
        tmp = Variable(x_hard - r2.data)
        tmp.detach_()
        x = tmp + x

    return x.view_as(input)


def get_diagonal_elements_range(block):
    '''
    Given a block, return the diagonal units which are included in this block
    '''
    r1, r2, c1, c2, _ = block
    unit_from = max(r1, c1)
    unit_to = min(r2, c2)
    if unit_from < unit_to:
        return unit_from, unit_to
    else:
        return None

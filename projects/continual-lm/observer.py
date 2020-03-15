# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class Observable(object):
    '''Simple implementation of the observer pattern'''

    def __init__(self):
        self.observers = []

    def register(self, callback):
        self.observers.append(callback)

    def deregister(self, callback):
        self.observers.remove(callback)

    def __call__(self, *args):
        for c in self.observers:
            c(*args)

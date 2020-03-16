# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import term

def all_reductions(t):
    for tr,_,_ in term.all_reductions(t):
        yield tr

def print_all(ts):
    for t in ts:
        print(term.to_str(t))

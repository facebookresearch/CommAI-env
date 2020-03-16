# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import pool

def print_scc(scc):
    for n in sorted((n for n in scc if isinstance(n, pool.Reaction)), 
        reverse=True):
        print(n)


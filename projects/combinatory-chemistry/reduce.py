# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

#!/usr/bin/env python
from expression import Expression
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('expression')
    ap.add_argument('-n', type=int, default=10)
    ap.add_argument('-r', '--replace', action='append', default=[])
    args = ap.parse_args()
    
    exp = Expression.parse(args.expression)
    exp = exp(exp)
    replacements = args.replace

    for i in range(args.n):
        if not exp.is_reducible():
            break
        exp = exp.sreduce()[0]#dreduce()#sreduce()[0]
        print(with_replacements(exp, replacements))
        print(str(exp).replace(args.expression, 'A'))

def with_replacements(exp, replacements):
    str_exp = str(exp)
    for i, repl in enumerate(replacements):
        rid = chr(ord('A') + i)
        str_exp = str_exp.replace(repl, rid)
        str_exp = str_exp.replace("({})".format(repl), chr(ord('A') + i))
        str_exp = str_exp.replace('({})'.format(rid), rid)
    return str_exp

if __name__ == '__main__':
    main()

# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

# import all learners in the current directory
# adapted from: http://stackoverflow.com/a/1057534/367489
# FIXME: this architecture is probably fragile. Test where it fails and fix it.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from os.path import dirname, basename, isfile
import glob
modules = glob.glob(dirname(__file__) + "/*.py")
for m in [basename(f)[:-3] for f in modules if isfile(f)]:
    __import__('learners.' + m)

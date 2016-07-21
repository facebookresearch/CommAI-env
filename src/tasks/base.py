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
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_init


class BaseTask(Task):
    '''
    Base task for other tasks in the competition implementing
    behaviour that should be shared by most of the tasks.
    '''

    def __init__(self, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)

    # ignore anything the learner says while the teacher is speaking
    @on_message()
    def on_any_message(self, event):
        # if the environment is speaking
        if not self._env.is_silent():
            # i will ignore what the learner just said by forgetting it
            self.clear_input_channel()

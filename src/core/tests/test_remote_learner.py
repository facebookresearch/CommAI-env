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

import zmq
import random


def main():
    port = "5556"
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect("tcp://localhost:%s" % port)
    socket.send_string(str('hello'))

    message = '00101110'
    cnt = 0
    while True:
        reward = socket.recv()  # 1 or 0, or '-1' for None
        print(reward)
        msg_in = socket.recv()
        print(msg_in)

        # think...
        msg_out = str(random.getrandbits(1) if cnt % 7 == 0 else 1)
        if cnt % 2 == 0:
            msg_out = str(message[cnt % 8])
        socket.send(msg_out)
        cnt = cnt + 1

if __name__ == '__main__':
    main()

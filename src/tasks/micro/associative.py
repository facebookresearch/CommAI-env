from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from core.task import on_start, on_message, on_timeout, on_output_message, Task
import random
import logging


def generate_lookup(string_length):
    source = list(range(2**string_length))
    target = list(range(2**string_length))
    random.shuffle(target, lambda: random.random())
    return {bin(s)[2:].zfill(string_length):
             bin(t)[2:].zfill(string_length) for s, t in zip(source, target)}


class EpisodicKeyValueAssociation(Task):
    def __init__(self, string_length):
        query_len = 3 * string_length + 4
        answer_len = string_length + 1
        super(EpisodicKeyValueAssociation, self).__init__(
            max_time=query_len + answer_len + 1)
        self.table = generate_lookup(string_length)
        self.logger = logging.getLogger(__name__)

    @on_start()
    def give_instructions(self, event):
        self.finished_talking = False
        self.key = random.choice(self.table.keys())
        self.set_message('A{key}:{value} V{key}.'.format(key=self.key,
                                                         value=self.table[self.key]))

    @on_output_message(r'\.')
    def reward_at_end(self, event):
        self.finished_talking = True

    @on_message()
    def discard_while_talking(self, event):
        if not self.finished_talking:
            self.ignore_last_char()

    @on_message(r'\.')
    def evaluate(self, event):
        if not self.finished_talking:
            return

        if event.is_message(self.table[self.key] + '.'):
            self.set_reward(1)
        else:
            self.set_reward(-1)

    @on_timeout()
    def handle_timeout(self, event):
        self.set_reward(-1)

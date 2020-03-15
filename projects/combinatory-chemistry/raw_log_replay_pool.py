from base_pool import BasePool
import json
from expression import Expression
from reaction import Reaction

INF=10000
class RawLogReplayPool(BasePool):
    def __init__(self, recording_filename):
        self.recording = open(recording_filename)
        entry = self.read_next_entry()
        assert entry['type'] == 'pool'
        N = len(entry['value'])
        super(RawLogReplayPool, self).__init__(N, food_size=INF)
        self.apply_entry(entry)

    def step(self):
        entry = self.read_next_entry()
        self.apply_entry(entry)

    def read_next_entry(self):
        entry = json.loads(next(self.recording))
        return entry

    def apply_entry(self, entry):
        if entry['type'] == 'reaction':
            self.apply_reaction(Reaction.unserialize(entry['value']))
        elif entry['type'] == 'pool':
            self.load_pool_expressions(entry['value'])
        return entry['type']

    def load_pool_expressions(self, expressions_strings):
        for expression_string in expressions_strings:
            self.append(Expression.parse(expression_string))

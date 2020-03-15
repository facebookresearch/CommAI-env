import json
import logging
logger = logging.getLogger(__name__)

class RawLogPoolObserver(object):
    def __init__(self, pool, json_fn, interval):
        self.ticks = 0
        self.interval = interval
        pool.reaction_computed.register(self.on_reaction_computed)
        self.pool = pool
        self.out = open(json_fn, 'w')
        self.write_pool()

    def on_reaction_computed(self, pool, reaction):
        self.write_reaction(reaction)
        self.ticks += 1
        if self.ticks == self.interval:
            self.write_pool()
            self.ticks = 0

    def write_reaction(self, reaction):
        try:
            self.out.write(json.dumps({'type': 'reaction', 'value': reaction.serializable()}) + '\n')
        except RecursionError:
            logger.error('Recursion error')

    def write_pool(self):
        try:
            self.out.write(json.dumps({'type': 'pool', 'value': self.pool.serializable()}) + "\n")
        except RecursionError:
            logger.error('Recursion error')

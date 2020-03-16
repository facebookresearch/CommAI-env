# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import time
from base_reporter import BaseReporter

class ConsoleReporter(BaseReporter):
    def __init__(self, metric_provider, period):
        super(ConsoleReporter, self).__init__(metric_provider)
        self.abbreviations = {'generation': 'gen'}
        self.formats = {'generation': '{}k'}
        self.timer = time.time()
        self.period = period

    def track_metric(self, metric, console_abbr, console_fmt='{}'):
        super(ConsoleReporter, self).track_metric(metric)
        self.abbreviations[metric] = console_abbr
        self.formats[metric] = console_fmt

    def report(self, i):
        metric_values = self.get_metric_values()
        metrics_strs = []
        for metric, value in [('generation', i//1000)] + list(metric_values.items()):
            abbr = self.abbreviations[metric]
            fmt_value = self.formats[metric].format(value)
            metrics_strs.append(f'{abbr} {fmt_value}')
        time_per_gen = (time.time() - self.timer) / self.period * 1000
        if time_per_gen < 1:
            time_per_gen *= 1000
            time_per_gen_unit = 'μs'
        else:
            time_per_gen_unit = 'ms'
        metrics_strs.append(f"time/gen {time_per_gen:.0f}{time_per_gen_unit}")
        self.timer = time.time()
        print( " | ".join(metrics_strs))


from base_reporter import BaseReporter
import json
from pathlib import Path

class JSONReporter(BaseReporter):
    def __init__(self, metric_provider, log_filename):
        super(JSONReporter, self).__init__(metric_provider)
        log_filename = Path(log_filename)
        self.log_handle = open(log_filename, 'w')
        substrates_filename = log_filename.parent / (log_filename.stem + '-substrates.jsonl')
        self.substrates_log_handle = open(substrates_filename, 'w')

    def report(self, generation):
        metric_values = self.get_metric_values()
        self.log_handle.write(json.dumps(metric_values))
        self.log_handle.write('\n')
        self.log_handle.flush()
        self.substrates_log_handle.write(json.dumps(
            {str(k): v for k,v in self.metric_provider.get_substrate_count().items()}))
        self.substrates_log_handle.write('\n')
        self.substrates_log_handle.flush()



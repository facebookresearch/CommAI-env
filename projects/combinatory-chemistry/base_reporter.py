class BaseReporter(object):
    def __init__(self, metric_provider):
        self.metrics = []
        self.metric_provider = metric_provider

    def track_metric(self, metric):
        self.metrics.append(metric)

    def get_metric_values(self):
        metric_values = {}
        for metric in self.metrics:
            metric_values[metric] = \
                    getattr(self.metric_provider, 'get_'+metric)()
        return metric_values

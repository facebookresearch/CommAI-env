from pool_metrics import PoolMetrics
from json_reporter import JSONReporter
from console_reporter import ConsoleReporter


class PoolObserver(object):
    def __init__(self, period, log_filename, food_size, history_size):
        self.pool_metrics = PoolMetrics(food_size, history_size)
        self.period = period
        self.json_reporter = JSONReporter(self.pool_metrics, log_filename)\
                if log_filename else None
        self.console_reporter = ConsoleReporter(self.pool_metrics, period)
        self.track_metric('current_expressions_count', 'count')
        self.track_metric('current_expressions_distinct_count', 'dcount')
        self.track_metric('current_expressions_reducible_count', 'red.count')
        self.track_metric('current_expressions_top10_length')
        self.track_metric('current_expressions_max_length', 'maxlen')
        self.track_metric('current_expressions_mean_length')
        # debug
        self.track_metric('current_expressions_max_depth', 'maxdepth')
        #self.track_metric('current_expressions_reduction_count', 'reductions', '{:.1f}')
        # end debug
        self.track_metric('current_expressions_mean_length', 'meanlen', '{:.2f}')
        self.track_metric('recent_expressions_recurrence_count')
        self.track_metric('recent_largest_scc_size', 'sccLen')
        self.track_metric('recent_scc_count', '#scc')
        self.track_metric('recent_raf_scc_count')
        self.track_metric('recent_raf_length', 'raf')
        self.track_metric('recent_raf_product_max_length')
        self.track_metric('recent_raf_products_count')
        self.track_metric('recent_reactions_count')
        self.track_metric('current_expressions_max_multiplicity')
        self.track_metric('current_expressions_mean_multiplicity')
        self.track_metric('current_expressions_percent_at_1', '@1', '{:.0f}')
        self.track_metric('current_expressions_percent_at_2', '@2', '{:.0f}')
        self.track_metric('recent_raf_products_max_multiplicity', 'raf_mult')
        self.track_metric('recent_raf_complement_products_max_multiplicity')
        self.track_metric('recent_raf_cycle_length', 'raf_lvl')
        self.track_metric('recent_raf_substrate_count', 'sbst')
        self.track_metric('current_expressions_max_multiplicity_length')
        self.track_metric('current_p_reduce', 'Pr', '{:.2f}')
        self.track_metric('current_p_break')
        self.track_metric('current_p_combine')
        self.track_metric('current_n_reduce')
        self.track_metric('current_n_break')
        self.track_metric('current_n_combine')
        self.track_metric('current_total_size', 'T')
        #self.track_metric('recent_recurrent_expression_length', 'rec_expr_len')
        #self.track_metric('recent_raf_scc_expressions_multiplicity', 'scc_mult')

    def track_metric(self, metric, console_abbr=None, console_fmt='{}'):
        if self.json_reporter:
            self.json_reporter.track_metric(metric)
        if console_abbr:
            self.console_reporter.track_metric(metric, console_abbr, console_fmt)

    def on_step_computed(self, pool, ticks):
        if ticks > 0 and ticks % self.period == 0:
            self.report(ticks)

    def on_reaction_computed(self, pool, reaction):
        self.pool_metrics.on_reaction_computed(pool, reaction)

    def report(self, generation):
        if self.json_reporter:
            self.json_reporter.report(generation)
        self.console_reporter.report(generation)
        self.pool_metrics.reset_perishable_history()


    def print_preceding_graph(self, graph, m, depth=1):
        if depth > 0:
            for reaction in graph.predecessors(m):
                reactives = list(map(str, reaction.reactives))
                reaction_type = graph.node[reaction]['reaction_type']
                if reaction_type != 'reduce':
                    continue
                print(reaction_type, " + ".join(reactives), '->', m)
                for r in reaction:
                    if r.size() >4:
                    #if term.is_reducible(r, None):
                    #    print(" / ".join(map(term.to_str, map(operator.itemgetter(0), term.all_reductions(r)))))
                        self.print_preceding_graph(graph, r, depth-1)

from reaction_graph import ReactionGraph
from reaction import Reaction
from collections import Counter
from cachetools import LFUCache
from collections import deque
import numpy as np
import networkx as nx
import zlib
import console_tools
from scipy.stats import mode
from lazy import lazy

import logging
logger = logging.getLogger(__name__)

class PoolMetrics(object):
    def __init__(self, food_size, history_size):
        self.reaction_graph = ReactionGraph()
        self.food_size = food_size
        self.history = Counter() 
        self.substrate_count = Counter()
        self.recent_history = LFUCache(history_size)
        self.pool_str_hist = deque(maxlen=1000)
        self.n_reactions = Counter()
        self.emergent_substrates = set()

    def on_reaction_computed(self, pool, reaction):
        #FIXME: move to arguments
        self.expressions = pool.expressions
        self.pool = pool
        self.reaction_graph.add_reaction(reaction)
        substrate = reaction.get_substrate()
        if substrate is not None:
            self.substrate_count[substrate] += 1

        for product in reaction.products:
            self.history[product] = self.history.get(product, 0) + 1
            self.recent_history[product] = self.recent_history.get(product, 0) + 1
        self.n_reactions[reaction.type] += 1
    
    def get_current_p_reduce(self):
        Z = sum(self.n_reactions.values())
        return self.n_reactions['reduce'] / Z if Z > 0 else 0

    def get_current_p_break(self):
        Z = sum(self.n_reactions.values())
        return self.n_reactions['break'] / Z if Z > 0 else 0

    def get_current_p_combine(self):
        Z = sum(self.n_reactions.values())
        return self.n_reactions['combine'] / Z if Z > 0 else 0

    def get_current_n_combine(self):
        return self.n_reactions['combine']

    def get_current_n_reduce(self):
        return self.n_reactions['reduce']

    def get_current_n_break(self):
        return self.n_reactions['break']

    @lazy
    def raf(self):
        food_set = set(x for x in self.reaction_graph.remove_selfloop().get_expressions()
                if len(x) <= self.food_size)
        raf = self.reaction_graph.get_raf(food_set)
        for r in raf:
            count = self.reaction_graph.get_occurrences(r)
            logger.info(f'{count} x {r} ') #(' + 
                    #'; '.join(f'{x} = {self.expressions[x]}'
                    #    for x in r.reactives) +
                    #')')
        return raf

    def is_valid_raf(self, raf, food_set):
        for r in raf:
            if any(p not in food_set and not any(p not in r2.products for r2 in raf)
                    for p in r.reactives):
                return False
        return True


    @lazy
    def reduction_sg(self):
        return self.reaction_graph.get_reduction_subgraph().remove_selfloop()
        # for reactives, product in raf:
        #     if term.size(product) > 3:
        #         print(" + ".join(map(term.to_str, reactives)), '->', term.to_str(product))

    def reset_perishable_history(self):
        #self.reaction_graph.reset()
        lazy.invalidate(self, 'raf')
        lazy.invalidate(self, 'reduction_sg')
        self.n_reactions.clear()

    def get_substrate_count(self):
        return self.substrate_count

    def get_current_total_size(self):
        return self.pool.get_total_size()
    
    def get_current_expressions_top10_length(self):
        sizes = list(map(len, self.expressions))
        sizes.sort()
        return np.mean(sizes[-10:])

    def get_current_expressions_reducible_count(self):
        reducibles = sum(v for ex, v in self.expressions.items()
                if ex.is_reducible(self.pool))
        return reducibles

    def get_recent_largest_scc_size(self):
        if len(self.reaction_graph) > 0:
            return len(self.get_largest_strongly_connected_component())
        else:
            return -1

    def get_largest_strongly_connected_component(self):
        graph = self.reaction_graph.get_reduction_subgraph()
        graph.trim_short_formulae(4)
        largest = max(graph.get_all_strongly_connected_components(), key=len)
        node_types = nx.get_node_attributes(graph.graph, 'node_type')
        sg = self.reaction_graph.graph.subgraph(largest)
        #for n in largest:
        #    if node_types[n] == 'formula':
        #        print(term.to_str(n))
        #        self.print_preceding_graph(sg, n)
        return largest


    def get_current_expressions_count(self):
        return sum(v for ex, v in self.expressions.items())
    
    def get_current_expressions_distinct_count(self):
        return sum(1 for _ in self.expressions.unique())

    def get_current_expressions_recurrence_count(self, threshold=4):
        c, n = 0, 0
        for f in self.history:
            if len(f) > threshold:
                c += self.history[f]
                n += 1
        return c / n if n > 0 else 0
        # try:
        #     m = max((x for x in self.pool.pool if term.size(x) > threshold),
        #             key=lambda k: self.history.get(k, 0))
        #     #if self.history[m] > 0:
        #     #    print (term.to_str(m), self.history[m])
        #     #    g = self.reaction_graph.graph
        #     #    if m in g:
        #     #        self.print_preceding_graph(g, m, 1)
        #     #    print('-'*30)
        # except ValueError:
        #     pass

    def get_recent_reactions_count(self):
        return len(self.reaction_graph.get_all_reducing_reactions())

    def get_recent_expressions_recurrence_count(self, threshold=4):
        c, n = 0, 0
        for f in self.recent_history:
            if len(f) > threshold:
                c += self.recent_history[f]
                n += 1
        return c / n if n > 0 else 0

    def get_pool_compressed_length(self):
        sorted_pool = sorted(self.expressions, key=len)
        pool_str = " | ".join(map(str, sorted_pool))
        self.pool_str_hist.append(pool_str)
        hist_str = "\n".join(self.pool_str_hist)
        compressed_hist_str = zlib.compress(hist_str.encode())
        return len(compressed_hist_str)

    def get_recent_scc_count(self):
        n = 0
        for scc in self.reduction_sg.get_without_substrates_subgraph().get_all_strongly_connected_components():
            if len(scc) > 1:
                # print("="*20)
                # console_tools.print_scc(scc)
                for r in sorted((r for r in scc if isinstance(r, Reaction)), 
                    reverse=True):
                    logger.debug(f'{r} in scc')
                # import pickle
                # sg_scc = self.reduction_sg.get_subgraph(scc)
                # print(len(sg_scc))
                # if len(scc)>100:
                #     pickle.dump(sg_scc.graph,  open('scc.pkl', 'wb'))
                n += 1
        return n
    
    def get_recent_raf_length(self):
        return len(self.raf)

    def get_recent_raf_cycle_length(self):
        raf_graph = ReactionGraph()
        for reaction in self.raf:
            raf_graph.add_reaction(reaction)
        return raf_graph.get_maximal_cycle_length()

    def get_recent_raf_substrate_count(self):
        raf_graph = ReactionGraph()
        for reaction in self.raf:
            substrate = reaction.get_substrate()
            if substrate is not None:
                self.emergent_substrates.add(substrate)
        if self.emergent_substrates:
            logger.info('Emergent substrates: {}'.format(self.emergent_substrates))
        return len(self.emergent_substrates)


    def get_recent_raf_scc_count(self):
        raf_subgraph = self.reduction_sg.get_subgraph_from_reactions(self.raf)
        n = 0
        raf_subgraph.remove_food_edges()
        for scc in raf_subgraph.get_all_strongly_connected_components():
            if len(scc) > 1:
                n += 1
        return 1

    def get_current_expressions_max_length(self):
        return max(map(len, self.expressions.unique()))

    def get_current_expressions_max_depth(self):
        return max(map(lambda e: e.get_depth(), self.expressions.unique()))

    def get_current_expressions_reduction_count(self):
        return np.mean(list(map(lambda e: len(e.all_reductions()), self.expressions.unique())))
    
    def get_current_expressions_percent_at_1(self):
        return self.get_current_expressions_percent_at(1)

    def get_current_expressions_percent_at_2(self):
        return self.get_current_expressions_percent_at(2)

    def get_current_expressions_percent_at(self, k):
        total = 0
        at_k = 0
        for expr in self.expressions.unique():
            n = self.expressions[expr]
            total += n
            if len(expr) <= k:
                at_k += n
        return at_k * 100 / total

    def get_current_expressions_mean_length(self):
        return np.mean(list(map(len, self.expressions.unique())))

    def get_recent_raf_product_max_length(self):
        return max(map(lambda r: max(len(p) for p in r.products), self.raf), default=0)

    def get_recent_raf_products_count(self):
        return sum(list(self.expressions[p] for p in set.union(set(), *(set(r.products) for r in self.raf))))

    def get_current_expressions_max_multiplicity(self):
        return max(list(v for k,v in self.expressions.items()
            if len(k) > self.food_size), default=0)

    def get_current_expressions_mean_multiplicity(self):
        current_expressions_multiplicity = list(v for k,v in self.expressions.items()
            if len(k) > self.food_size)
        return np.mean(current_expressions_multiplicity) if current_expressions_multiplicity else 0

    def get_current_expressions_max_multiplicity_length(self):
        multiplicity = self.get_current_expressions_max_multiplicity()
        if multiplicity == 1:
            return 0  # no trivial solutions
        max_multiplicity_lengths = list(len(k) for k,v in self.expressions.items()
                if v == multiplicity)
        return np.mean(max_multiplicity_lengths) if max_multiplicity_lengths else 0

    def get_recent_raf_products_max_multiplicity(self):
        #print(term.to_str(max(set(r.product for r in self.raf if term.size(r.product) > self.food_size), key=lambda k:self.pool.terms_set[k])))
        return max(list(self.expressions[p] for p in set.union(set(), *(set(r.products) for r in self.raf if any(len(p) > self.food_size for p in r.products)))), default=0)

    def get_recent_raf_complement_products_max_multiplicity(self):
        #print(term.to_str(max(set(r.product for r in self.raf if term.size(r.product) > self.food_size), key=lambda k:self.pool.terms_set[k])))
        return max(list(self.expressions[p] for p in self.expressions if p not in set.union(set(), *(set(r.products) for r in self.raf if any(len(p) > self.food_size for p in r.products)))), default=0)

    def get_recent_raf_scc_expressions_multiplicity(self):
        raf_subgraph = self.reaction_graph.get_subgraph_from_reactions(self.raf)
        all_sccs = list(scc for scc in raf_subgraph.get_all_strongly_connected_components() if len(scc) > 1)
        largest_expr_in_sccs = list(max(scc, key=len) for scc in all_sccs)
        if all_sccs:
            m = max((expr for expr in largest_expr_in_sccs), key=self.expressions.get_multiplicity)
            return self.expressions.get_multiplicity(m)
        else:
            return 0

    def get_recent_recurrent_expression_length(self):
        try:
            f = max((expr for expr in self.recent_history
                if len(expr) > self.food_size), key=self.recent_history.get)
            return len(f)
        except ValueError:
            return 0

    def get_longest_non_trivial_recurring_formula(self):
        non_trivial_recurring_formulae = self.get_non_trivial_recurring_formulae()
        if non_trivial_recurring_formulae:
            return max(non_trivial_recurring_formulae, key=len)
        else:
            return None

    def get_non_trivial_recurring_formulae(self):
        m = -mode(-np.array(list(self.history.values()))).mode
        return [f for f, n_occ in self.history.items() if n_occ > m]
    

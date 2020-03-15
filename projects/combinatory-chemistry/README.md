# Combinatory Chemistry

This directory contains the code associated with the paper _Combinatory Chemistry:
Towards a Simple Model of Emergent Evolution_.

## Running the simulation

Use `python main.py` with the following parameters:

- `--reactions`: Number of total reactions for which the simulation is run.
- `--tape-size`: Total number of combinators.
- `--report-every`: Number of generations over which results are reported in the console and in the log file.
- `--feed`: Activate substrate assemblage.
- `--food-size`: Maximum expression size for which the substrate assemblage mechanism is activated. It is also relevant for RAF-dependent metrics.
- `--log-dir`: Directory where output logs are stored.
- `--raw-logger`: Also log every single reaction produced in the system.
- `--replay`: Use a raw log to replay the same history (useful to recompute metrics).

For example, run `python main.py --reactions 1000000 --tape-size 10000 --feed --food-size 6 --log-dir out` to run the simulation for 1M iterations on a system of 10k combinators and substrate assemblage enabled for expressions up to size 6, saving results to `out`.

## Log Files

### `log.jsonl`

This file contains a json dictionary on each line. It reports metrics
at the end of each period according to the `--report-every` parameter.
These are a few of the metrics that the system keeps track of. For a complete list
see the `pool_observer.py` file and their definition in `pool_metrics.py`.

- `current_expressions_count`: Total number of expressions in the system.
- `current_expressions_distinct_count`: Diversity of expressions.
- `current_expressions_reducible_count`: Number of expressions that are reducible.
- `current_expressions_top10_length`: Mean length of the 10 longest expressions.
- `current_expressions_max_length`: Length of the longest expression.
- `current_expressions_mean_length`: Mean length of all expressions.
- `recent_largest_scc_size`: Size of the longest strictly connected component in the cumulative reaction graph (CRG).
- `recent_scc_count`: Number of strictly connected components in the CRG.
- `recent_raf_length`: Size of the RAF in the CRG.
- `recent_raf_product_max_length`: Length of the longest expression produced by a RAF.
- `recent_raf_products_count`: Total number of occurrences of an expression that is produced by reactions in the RAF.
- `recent_raf_cycle_length`: Length of the longest shortest path from a node to itself.
- `recent_raf_substrate_count`: Number of different types of foods in the RAF.
- `current_p_reduce`: Proportion of reduce to combine/break reactions.

### `log-substrates.jsonl`

At every reporting period, it writes a json dictionary with the frequency that
each type of substrate has been consumed.

### `raw_log.jsonl`

Activated with the `--raw-logger` flag. It contains one dictionary per line
with two entries: "type" and "value". This dictionary can either contain
a recorded reaction (type="reaction") or, at every reporting period (given 
by the `--report-every` parameter), it writes how many expressions are there
of every kind (type="pool").
dictionary

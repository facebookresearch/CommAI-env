# Class-Agnostic Continual Learning of Alternating Languages and Domains

This folder contains the code associated with the paper _Class-Agnostic Continual Learning
of Alternating Languages and Domains_.

The following instructions indicate how to download the data and train models.


## Dataset preparation

To download the required data, run the script in `data/create_datasets.py` as:

```bash
cd data
pip install -r requirements.txt  # needs the wget package
python create_datasets.py
```

## Training

Train a model with `python main.py`. Important parameters are:

- `--data`: Location of the corpus data. E.g. `data/news_dev`, `data/news_test`, `data/domain_dev`, `data/domain_test`
- `--model-level`: One of `word` or `char`. Use `word` for the domain data and `char` for the news data.
- `--total-length`: Total length in words or characters of the corpus excerpt.
- `--lang-switch`: Average number of tokens every which a language/domain switch occurs.
- `--log-dir`: Destination directory for output log data and trained models.
- `--architecture`: One of `static` (simple LSTM), `moe` (PoE and FF-PoE), `static_per_domain` (Ind. LSTM), `transformer` (Transformer).
- `--weights-trainer`: Only valid for `moe` architecture. One of `grad` (FF-PoE) or `lstm` (PoE).
- `--weights-trainer-iterations`: Number of SGD steps on the weights.
- `--max-memory-size`: Only valid for `moe` architecture. Number of modules.
- `--cluster-run` and `--cluster-run-name`: Used to automatically create subdirectories within the log directory when run on a SLURM cluster.
- `--cuda`: Use GPU

Please, refer to `python main.py --help` for more information on the parameters.

## Example

Consider, for example, the following command line to train a FF-PoE model on a 1M-characters-long excerpt of the news data, switching between languages every 10k characters on average.

```bash
python main.py --architecture moe --emsize 200 --nhid 200 --lr 0.001 --weights-trainer-lr 0.001 --learn-iterations 2 --total-length 1000000 --lang-switch 10000 --weights-trainer grad --max-memory-size 30 --dropout 0.2 --optimizer Adam --weights-trainer-iterations 10  --cuda --data data/news_test --model-level char
```

All the test command lines to replicate our results are available in the `test_command_lines` directory.

## Displaying results

A script is also provided to compute perplexity results and recovery metrics from the log files. Use as follows:

```bash
python results/display_results.py --log-path <logs_parent_directory>
```
where `logs_parent_directory` stands for the parent directory containing multiple
runs (as it is for instance the value of the `--log-dir` parameter above when `--cluster-run` is being used).

This script automatically groups results by dataset and architecture. By default best values per group are returned. To obtain the means, append the `--mean` argument.

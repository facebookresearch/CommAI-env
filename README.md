# AI Challenge

The AI Challenge is a platform for running and evaluating AI systems as
described in A Roadmap towards Machine Intelligence
(http://arxiv.org/abs/1511.08130)

## Running

### Configuration

First, you should create a configuration file stating which tasks
and in which order, if any, are going to be fed to the learner.

You can start by copying the configuration file corresponding to
the full training set as follows:

```bash
cp tasks_config.sample.json tasks_config.json
```

### Human-mode

To run the system on a simple console interface, where you can
impersonate the learner (human mode), run the environment as 
follows:

```bash
python run.py tasks_config.json
```

## Requirements
* Python 2.6+


## Full documentation

The full documentation can be produced using Python Sphinx. Just go to
`src/docs` and run `make html` or `make latexpdf`.

## License
AI Challenge is BSD-licensed. We also provide an additional patent grant.

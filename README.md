# MAINE

MAINE (MAchine INtelligence Environment) is a platform for training and evaluating AI systems as described in [A Roadmap towards Machine Intelligence](http://arxiv.org/abs/1511.08130).

## Introduction

MAINE is a platform for training and testing your AI system, the **Learner**, in a communication-based setup where it interacts via a bit-level interface with an *Environment*. The Environment asks the Learner to solve a number of communication-based *Tasks*, and assigns it a *Reward* for each task it solves. Examples of tasks currently implemented involve tasks where the Learner has to solve counting problems, tasks where it must memorize lists of items and answer questions about them, or follow navigation instructions through a text-based navigation scheme. Crucially, the set of tasks is open: we are constantly extending it, and we invite others to contribute.

The ultimate goal of MAINE is to provide an environment in which Learners that ...


## Running

The environment can be run in two simple steps:

1. Creating a configuration file (for instance, by copying `task_config.sample.json`)
2. Running the environment (in the simplest case, just providing the configuration file as an argument)

By default, the environment will be run in **human-mode** (see below). If you want to
run the environment with a given learning algorithm, see the **Specifying a learning algorithm** 
section below.

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

To get a better grasp of the kind of problems the learning algorithms
are facing, you can run the environment using the `--scrambled` flag
which replaces each word in the observed vocabulary by a random 
pseudo-word.

### Specifying a learning algorithm

WRITEME

## Requirements
* Python 2.6+


## Full documentation

The full documentation can be produced using Python Sphinx. Just go to
`src/docs` and run `make html` or `make latexpdf`.

## License
AI Challenge is BSD-licensed. We also provide an additional patent grant.

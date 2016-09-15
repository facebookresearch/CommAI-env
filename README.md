# MAINE

MAINE (MAchine INtelligence Environment) is a platform for training and evaluating AI systems as described in [A Roadmap towards Machine Intelligence](http://arxiv.org/abs/1511.08130).

## Introduction

## Introduction

MAINE is a platform for training and testing your AI system, the **Learner**, in a communication-based setup where it interacts via a bit-level interface with an **Environment**. The Environment asks the Learner to solve a number of communication-based **Tasks**, and assigns it a **Reward** for each task it solves.

The Learner is presented with multiple instances of all tasks (currently, in random order, although alternative scheduling methods might be considered in the future), and it has to solve as many of them as possible in order to maximize reward. Examples of tasks currently implemented include some in which the Learner must solve counting problems, tasks where it must memorize lists of items and answer questions about them, or follow navigation instructions through a text-based navigation scheme (see [this document](../master/TASKS.md) for detailed descriptions of the tasks) . Many tasks are incremental, in the sense that solving one should make solving another easier. Moreover, some tasks share information, so that Learners that are able to store data in a long-term memory should be favored. The set of tasks is open: we are constantly extending it, and we invite others to contribute. While the tasks might appear simple, we believe that most of them are beyond the grasp of current learning-based algorithms.

The ultimate goal of MAINE is to provide an environment in which Learners can be trained, from ground up, to be able to genuinely interact with humans through language. These are some characteristic of MAINE that distinguish it from other environments currently proposed to train and test AI (such as 


- The 

## Running

```
cp tasks_config.sample.json tasks_config.json
python run_tournament.py tasks_config.json
```

## Requirements
* Python 2.6+


## Full documentation

The full documentation can be produced using Python Sphinx. Just go to
`src/docs` and run `make html` or `make latexpdf`.

## License
AI Challenge is BSD-licensed. We also provide an additional patent grant.

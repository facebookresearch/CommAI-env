# MAINE

MAINE (MAchine INtelligence Environment) is a platform for training and evaluating AI systems as described in [A Roadmap towards Machine Intelligence](http://arxiv.org/abs/1511.08130).

## Introduction

MAINE is a platform for training and testing your AI system, the **Learner**, in a communication-based setup where it interacts via a bit-level interface with an *Environment*. The Environment asks the Learner to solve a number of *Tasks*, and assigns it a *Reward* for each task it solves. Tasks are an open set: they currently include some...

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

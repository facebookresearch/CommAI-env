# MAINE

MAINE (MAchine INtelligence Environment) is a platform for training and evaluating AI systems as described in [A Roadmap towards Machine Intelligence](http://arxiv.org/abs/1511.08130).

## Introduction

MAINE is a platform for training and testing your AI system, the **Learner**, in a communication-based setup where it interacts via a bit-level interface with an **Environment**. The Environment asks the Learner to solve a number of communication-based **Tasks**, and assigns it a **Reward** for each task it solves. Examples of tasks currently implemented include some in which the Learner must solve counting problems, tasks where it must memorize lists of items and answer questions about them, or follow navigation instructions through a text-based navigation scheme. The set of tasks is open: we are constantly extending it, and we invite others to contribute.

The ultimate goal of MAINE is to provide an environment in which Learners can be trained, from ground up, to be able to genuinely interact with humans through language. While the tasks (documented in [here](TASKS))...

- The 


## Running

The environment can be run in two simple steps:

1. Creating a configuration file (for instance, by copying `task_config.sample.json`)
2. Running the environment, in the simplest case, just providing the configuration file as an argument with `python run.py my_config.json` 

By default, the environment will be run in **human-mode**([see below](#human-mode)). If you want to
run the environment with a given learning algorithm, see [the corresponding section
below](#specifying-a-learning-algorithm).

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

**Warning:** Note that the human-mode makes two assumptions about the input coming
from the teacher. The first involves the character encoding. Since the input 
actually arrives in bits but it would be very uncomfortable for a 
human learner to read a bit stream, we transform it into a character
stream for rendering it on screen. The second is the turn-taking convention,
by which we hand control to the human after the environment has produced
two consecutive spaces. None of these conventions are should be assumed
by the learning algorithms, as they could be modified in subsequent 
iterations of the tasks.

### Specifying a learning algorithm

To run the environment with a given learning algorithm, you can use the
`-l` or `--learner` flag followed by the fully qualifed name of the 
learner's class. For example, you can use any of the sample learners:

- `learners.sample_learners.SampleRepeatingLearner`
- `learners.sample_learners.SampleMemorizingLearner`

Defining a learning algorithm involves defining two functions: `next` and
`reward`. `next` receives a bit from the environment, and should return
the next bit spoken by the learner. `reward` notifies the learner of
a given received reward. In Python, you can start from the following 
code snippet to create a Learner:

```python
class MySmartLearner(BaseLearner):
    def reward(self, reward):
        # record receiving a reward

    def next(self, input_bit):
        # Figure out what should be
        # the next bit to be spiken
        return next_bit
```

#### Defining a learner in programming language X

It is also possible to define the learning algorithm in any other programming language. TODO: explain how.


### Console View

Whereas for the human-mode, the default view shows a console view

## Requirements
* Python 2.6+


## Full documentation

The full documentation can be produced using Python Sphinx. Just go to
`src/docs` and run `make html` or `make latexpdf`.

## License
AI Challenge is BSD-licensed. We also provide an additional patent grant.

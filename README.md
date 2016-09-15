# MAINE

MAINE (MAchine INtelligence Environment) is a platform for training and evaluating AI systems as described in [A Roadmap towards Machine Intelligence](http://arxiv.org/abs/1511.08130).

## Introduction

MAINE is a platform for training and testing an AI system, the **Learner** (coded in an arbitrary language of the system developer's choice), in a communication-based setup where it interacts via a bit-level interface with an **Environment**.  The Environment asks the Learner to solve a number of communication-based **Tasks**, and assigns it a **Reward** for each task instance it successfully completes.

The Learner is presented, in random order, with multiple instances of all tasks, and it has to solve as many of them as possible in order to maximize reward. Examples of tasks currently implemented include counting problems, tasks where the Learnes must memorize lists of items and answer questions about them, or follow navigation instructions through a text-based navigation scheme (see [this document](../master/TASKS.md) for detailed descriptions of the tasks). The set of tasks is open: we are constantly extending it, and we invite others to contribute.

The ultimate goal of MAINE is to provide an environment in which Learners can be trained, from ground up, to be able to genuinely interact with humans through language.  The tasks might appear simple (but try solving them in the *scrambled* mode we support, where your knowledge of English won't be of help!), we believe that most of them are beyond the grasp of current learning-based algorithms, and that a Learner able to solve them all would have already made great strides towards the level of communicative intelligence required to interact with and learn further from human teachers.

The following are some basic characteristics of MAINE that distinguish it from other environments currently proposed to train and test AI (such as [OpenAI Gym](https://gym.openai.com/) or [bAbI](https://research.facebook.com/research/babi/), and that are designed to encourage the development of fast, general, communication-based Learners.

- The focus in MAINE is entirely on communication-based tasks, where all communication takes place through a common bit-level interface between the Learner and the Environment.

- In a single MAINE session, the Learner is exposed to a variety of tasks, so that it must learn to recognize different tasks and apply different skill to them as appropriate.

- Many tasks are incremental, in the sense that solving one or more of them should make solving other tasks easier, as long as Learners have a long-term memory for data as well as algorithm (e.g., counting the properties of an object should be easier once the Learner has solved the basic counting tasks and learned how to associate objects and properties).

- There is no division between a training and testing phase:

..- On the one hand, a Learner should not just be able to memorize the solution to a fixed set of tasks, but learn how to *generalize* to new problems it encounters.

..- On the other, just like humans, the Learner should be able to solve simple problems after just a few exposures: thus, speed of learning should be taken into account in the evaluation.

..- **A competition based on MAINE will thus feature a different set of tasks from the ones included in the current development version.**

MAINE is currently in beta-testing stage, and we welcome your feedback and contributions!


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

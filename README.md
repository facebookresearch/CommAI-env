# CommAI-env

CommAI-env (Environment for Communication-based AI) is an experimental platform for training and evaluating AI systems as described in [A Roadmap towards Machine Intelligence](http://arxiv.org/abs/1511.08130).

## Introduction

CommAI-env is a platform for training and testing an AI system, the **Learner** (coded in an arbitrary language of the system developer's choice), in a communication-based setup where it interacts via a bit-level interface with an **Environment**.  The Environment asks the Learner to solve a number of communication-based **Tasks**, and assigns it a **Reward** for each task instance it successfully completes.

The Learner is presented, in random order, with multiple instances of all tasks, and it has to solve as many of them as possible in order to maximize reward. Examples of tasks currently implemented include counting problems, tasks where the Learners must memorize lists of items and answer questions about them, or follow navigation instructions through a text-based navigation scheme (see [this document](../master/TASKS.md) for detailed descriptions of the tasks). The set of tasks is open: we are constantly extending it, and we invite others to contribute.

The ultimate goal of CommAI-env is to provide an environment in which Learners can be trained, from ground up, to be able to genuinely interact with humans through language.  While the tasks might appear almost trivial (but try solving them in the *scrambled* mode we support, where your knowledge of English won't be of help!), we believe that most of them are beyond the grasp of current learning-based algorithms, and that a Learner able to solve them all would have already made great strides towards the level of communicative intelligence required to interact with, and learn further from human teachers. **NB: We do not claim that the tasks in CommAI-env are covering all skills an intelligent communicative agent should possess. Our claim is that, in order to solve CommAI-env, an intelligent agent must have very general learning capabilities, such that it should be able to acquire all the further tasks it needs fast, through interaction with humans or by other means.**

The following are some basic characteristics of CommAI-env that distinguish it from other environments and data-sets currently proposed to train and test AI systems (such as [OpenAI Gym](https://gym.openai.com/), [Allen AI Science Challenge](https://www.kaggle.com/c/the-allen-ai-science-challenge), [MazeBase](https://github.com/facebook/MazeBase) or [bAbI](https://research.facebook.com/research/babi/)), and that are designed to encourage the development of fast, general, communication-based Learners.

- The focus in CommAI-env is entirely on communication-based tasks, where all communication takes place through a common bit-level interface between the Learner and the Environment.

- In a single CommAI-env session, the Learner is exposed to a variety of tasks, so that it must learn to recognize different tasks and apply different skill to them as appropriate.

- Many tasks are incremental, in the sense that solving one or more of them should make solving other tasks easier, as long as Learners have a long-term memory for data as well as algorithm (e.g., counting the properties of an object should be easier once the Learner has solved the basic counting tasks and learned how to associate objects and properties).

- There is no division between a training and testing phase:

  - On the one hand, a Learner should not just be able to memorize the solution to a fixed set of tasks, but learn how to *generalize* to new problems it encounters.

  - On the other, just like humans, the Learner should be able to solve simple problems after just a few exposures: thus, speed of learning should be taken into account in the evaluation.

CommAI-env is currently in beta-testing stage, and we welcome your feedback and contributions!


## Running
The environment can be run as follows:

```bash
cd src

# Creating a configuration file (for instance, by copying the full task set)
cp tasks_config.sample.json tasks_config.json

# Running the environment, in the simplest case, just providing the configuration file as an argument
python run.py tasks_config.json
```

Note that the environment accepts configuration files in both json and python formats (see examples in the src directory).
By default, the environment will be run in **human-mode** ([see below](#human-mode)). If you want to
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

This will provide you with a console-based user interface to interact with
the environment that works as follows. Every time it seems like the
environment is quiet and expecting for the learner to answer, control
is transferred to the user who can input the string to be streamed back
to the environment.

The communication between the two, current time and the cumulative
reward are displayed on the screen.

To get a better grasp of the kind of problems the learning algorithms
are facing, you can run the environment using the `--scrambled` flag
which replaces each word in the observed vocabulary by a random
pseudo-word.

**Warning:** Note that the human-mode makes two assumptions about the input coming
from the teacher. The first involves the character encoding. Since the input
actually arrives in bits but it would be very uncomfortable for a
human user to read a bit stream, we transform it into a character
stream before rendering it on screen. The second is the turn-taking convention,
by which we hand control to the human after the environment has produced
two consecutive spaces. None of these conventions  can be safely assumed
by the learning algorithms, as they could be modified in subsequent
iterations of the tasks.

### Specifying a learning algorithm

To run the environment with a given learning algorithm, you can use the
`-l` or `--learner` flag followed by the fully qualified name of the
learner's class. For example, you can use any of the sample learners:

- `learners.sample_learners.SampleRepeatingLearner`
- `learners.sample_learners.SampleMemorizingLearner`

Defining a learning algorithm involves defining two functions: `next` and
`reward`. `next` receives a bit from the environment, and should return
the next bit spoken by the learner. `reward` notifies the learner of
a given received reward. In Python, you can start from the following
code snippet to create a Learner:

```python
from learners.base import BaseLearner

class MySmartLearner(BaseLearner):
    def reward(self, reward):
        # record receiving a reward

    def next(self, input_bit):
        # figure out what should be
        # the next bit to be spoken
        return next_bit
```

#### Defining a learner in programming language X

It is also possible to define the learning algorithm in any other programming language. To this end, we include
a super class learner `learners.base.RemoteLearner` which sets up a `zeromq` socket between an arbitrary learner binary and the
environment. The environment acts as a server.  For convenience, the user can specify the command to launch the learner
so that it is launched with the environment in the same process.

When the session is created, the environment and learner are initialized:
- The learner begins by sending a handshake 'hello' to the environment.
- Loop: accept reward, accept environment bit, send reply bit.

Example:

```c++
#include <string.h>
#include "zmq.h"

int main()
{
   // This is an example of a silly learner that always replies with '.'
   char reply[1];
   int n = 0;
   const char* response = "00101110";  // '.' utf-8 code

   // connect
   void *context = zmq_ctx_new();
   void *to_env = zmq_socket(context, ZMQ_PAIR);
   int rc = zmq_connect(to_env, "tcp://localhost:5556");

   // handshake
   zmq_send(to_env, "hello", 5, 0);

   // talk
   while (true)
   {
      // receive reward
      zmq_recv(to_env, reply, 1, 0);

      // receive teacher/env bit
      zmq_recv(to_env, reply, 1, 0);

      // reply
      reply[0] = response[n % strlen(response)];
      zmq_send(to_env, reply, 1, 0);
      n += 1;
   }

   zmq_close(to_env);
   zmq_ctx_destroy(context);

   return 0;
}
```

To Run Session with Learner Binary:
```bash
python run.py tasks_config.json -l learners.base.RemoteLearner \
--learner-cmd "/my/learner/binary"
```

### Console View

Whereas for the human-mode, the default view shows a console interface where you can observe the ongoing
communication between the two parts, when running an automated learning algorithm the view defaults to a
simpler one to allow the algorithms run faster. However, it is still possible to bring back the console view by
passing the argument `-v ConsoleView`, or equivalently, `--view ConsoleView`. For example:

```bash
python run.py -l learners.sample_learners.SampleRepeatingLearner -v ConsoleView tasks_config.json
```

## Requirements
* Python 2.6+
* zeromq (for remote learners)


## Full documentation

The full documentation can be produced using Python Sphinx. This includes more technical
documentation describing how you can create your own tasks or descriptions of the internals of the environment.
Just go to `src/docs` and run `make html`.

## Join the commAI-env community

We encourage you to fork the repository for your own research and experimentation.

Join our Facebook page, for general discussion about the project:
https://www.facebook.com/groups/1329249007088140

We actively welcome your pull requests for bugfixes or similar such issues.
See the CONTRIBUTING file for more details.

## License
CommAI-env is BSD-licensed. We also provide an additional patent grant.

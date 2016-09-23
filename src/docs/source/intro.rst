Introduction
------------

The code in the CommAI-env models a simulation scenario in which a
**Learner** communicates with an **Environment** who impersonates a teacher
asking the Learner to perform tasks and rewarding it when it does so. The tasks
are performed through natural language communication, in the same way as the
instructions are given. The communication is performed through a low-level
signal, where characters are encoded as bit sequences. The responsible for the
encoding and decoding of these sequences are the **InputChannel** and
**OutputChannel** objects in the Environment. The Learner and the
Environment will interchange (exactly) one bit at a time. Obviously, one of them
should have nothing to say while the other is speaking. Therefore, a particular
bit sequence is going to represent "being silent". Indeed, all the competition
is centered around assigning meaning to particular sequences of bits that
encode natural language commands.

The communication between the Learner and the Environment is handled by the
**Session**, which forwards the bits produced by each of the participants and
the rewards given to the Learner. For each bit sent, the Session blocks
waiting for the next bit to be sent back. The cumulative rewards and time steps
are recorded for performance evaluation.

A Learner is just any object that can handle a `next` method, which
given a bit it returns its next bit, and a `reward` method that informs the
learner about a received reward.

The Environment, on the other hand, executes one **Task** at a time based on a
*Scheduler*'s decision. A Task is defined through a set of messages and rewards
that are delivered to the Learner by the Environment as a reaction to different
kinds of Events. The possible events are described throughly in :ref:`events`.
To capture these events, the Environment registers **Triggers** to an
**EventManager**. The **Triggers** consist simply on: a type of event,
a condition to filter out events by specific details and a callback function
that will be invoked when an Event arrises. When an event is handled by
some function, it can either modify some internal variables to keep track
of some information, or interact with the learner by either setting the message
that is being sent through the Environment's Output Channel and/or *set the
reward to end the current task*. If the reward is given together with a message,
the Environment sends out the message and then rewards the learner just before
switching to the next task. During this "extra time" no other events are
processed. Also, events can be handled concurrently. This implies that
different (conflicting) messages (and rewards) could be sent to the learner.
Conflicts are solved through defining a priority for the messages.

Finally, a Task can run within a certain World. A World, is composed
ultimately of the same elements of a Task: some state variables and
Triggers and can interact with the Learner. The goal of this entity is to have
consistent across tasks states and behaviors. A Task can access the state
variables of the world, and listen for changes on them. The World, on the other
hand, cannot access the Task that is being run on.

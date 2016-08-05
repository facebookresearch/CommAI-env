How to create a new task
========================

Creating your task step-by-step
-------------------------------

The first thing you need to do, is creating a python file (it's nicer if you create it under the tasks directory) and import the necessary Task class and related tools:::

    from core.task import Task, on_start, on_message, on_sequence,\
        on_state_changed, on_timeout, on_output_message, on_init

In order to define a task, the first thing you need to do is subclassing the Task class as follows. You can omit the world parameter if it doesn't run on any world.::

    class MyTask(Task):
        def __init__(self, world):
            super(MyTask, self).__init__(
                max_time=1000, world=world)

Then, you will need to define how it will react to a set of events (e.g. when the task  is starting, when the learner has produced some expected message, etc.). This is achieved by defining event handlers which have this general form:::

    @on_<type-of-event>(<some-optional-parameters>)
    def on_my_event(self, event):
        ...code...

There are a number of events that have been contemplated, which are detailed below. Also, the reactions to these event can include calling primitives to affect the environment actions, like setting the output message or rewarding the agent.

When you are done with writing your task, you can instantiate it from the main file and send it to the scheduler  so it will be run with the other tasks (see points 2 and 3 in the Summary).

.. _events:

Event Handlers
--------------

In order to create an event handler, you need to the define a method (like on_my_event above) annotated with the type of event that you want to catch. These are the possible annotations you can use:

* `on_init`: Fires when a task is about to be run, but it hasn't started yet. It serves for initialization purposes. It doesn't trigger `StateChanged` events.
* `on_start`: Fires when a task actually starts. Differently from `on_init`, `StateChanged` events get triggered if the `state` variable is modified from this handler.
* `on_message`: Fires whenever the agent sends a message. It optionally takes a regular expression to match only a specified set of messages. The event object contains a "message" field, containing the message that has been received. Finally, two other helper methods have been introduced in the event object. The first, is_message, takes a string and checks whether the last part of the message exactly matches this string (see RepeatingCharTask for an example). The second, get_match, returns the part of the message that has been matched against the regular expression that parametrizes on_message. Optionally, if this regular expression contains groups (parentheses-demarcated chunks), you can give the group number as an argument to retrieve any of these sub-matches (see on_pick_up in the grid world for an example).
* `on_sequence`: Like on_message, but operates on sequences of bits (actually a string of 1s and 0s). The event object contains a "sequence" field, containing the sequence that has been received so far.
* `on_output_message`: Same as on_message, but it matches against what the environment has said.
* `on_output_sequence`: Same as on_sequence, but it matches against what the environment has said.
* `on_state_changed`: Every task and every world implicitly have a state object where you can store any properties you want (by doing self.state.my_variable_state = some_value). You can catch whenever the state object gets modified by annotating your handler with on_state_changed.  This takes as a parameter either a one-argument or a two-argument function (depending on whether there is a world state in conjunction with the task state or not). In python, anonymous functions can be defined, for example, like lambda ts: ts.my_variable_state == 10 for the one argument case or lambda ws, ts: ts.my_variable_state == ws.my_world_variable_state  for the two argument case. In the one argument case, the function is fed the state object of the task. In the two argument case, the function is fed the world state object and the task state object. See the MovingTask for an example, it's easier than it looks.
* `on_timeout`: Gets triggered when we reached the maximum amount of time steps.
* `on_world_init`: Like `on_init`, but when a world is being initialized.
* `on_world_start`: Like `on_start`, but when a world is being started.

State variables
---------------

Both Tasks and Worlds have a special variable called `state`. What's special
about this object is that when an attribute stored within it changes it's value,
it will trigger a StateChanged event. This holds true recursively for containers
stored within this object. For example, say that you have a dictionary created
in `this.state.my_dict`. And, in the context of a task, you do::

  this.state.my_dict['apple'] = 'green'

this will also trigger a StateChanged event. 

Defining Event Handlers at "runtime"
------------------------------------

Say that you are in the middle of your start (say, on the start event) and you want to add a new event handler on the fly. You can do this, by inserting a code snippet just as the following (notice that you can define a function within a function):::

    class MyTask(Task):
        ...
        @on_start()
        def my_task_start(self, event):
             ... <something something> ...
             def my_success_handler(self, event):
                  self.set_reward(1)
             self.add_handler(on_<event>(my_success_handler))

This also works if `my_success_handler` is an instance method::

    class MyTask(Task):
        ...
        @on_start()
        def my_task_start(self, event):
             ... <something something> ...
             self.add_handler(on_<event>(self.my_success_handler))

        def my_success_handler(self, event):
             self.set_reward(1)

Action Primitives
-----------------

Here are the few things you can do to affect the environment behavior. The Task and World classes have the following inherited methods:

* :code:`set_message(message, priority=0)`: Writes into the output buffer a message with the given priority only if there is no other message being sent with a higher priority.
* :code:`set_reward(reward, message='', priority=0)`:  Rewards the learner and ends the task. You can also send a finalization message with the given priority (the priority only applies to the message, not rewards).
* :code:`ignore_last_char()`: removes (or rather, masks with silence) the last character that has been received from the learner. This does not have an effect on already-fired MessageReceived events. Useful if you want to ignore the learner until some later instant.


Guidelines for the Competition tasks
====================================

For the tasks that actually form part of the competition we have typically
follow some guidelines:

* The tasks ignore the learner if the Environment is speaking. This behavior is provided for free by inheriting from BaseTask instead of Task::

    class MyTask(BaseTask):
        def __init__(self, world):
            super(MyTask, self).__init__(
                max_time=1000, world=world)

* All the messages sent by the Environment and the Learner are assumed to end in some punctuation marker.
* Generally we don't allow "substring" answers. For example, if the correct answer is "apple", we don't allow "dasdfsapplefdsf"
* General language and messages that are shared across tasks are kept in the `tasks.competition.messages` module.
* Tasks should present some kind of feedback, but the specifics of it are decided on a task-by-task basis.

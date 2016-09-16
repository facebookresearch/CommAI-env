#Environment implementation:

* Move the tasks in `pending` to `competition` after cleanup of the code. Make
sure that all tasks receive a world as an argument (for global consistency).
* Finish up the `tasks_config.sample.json` file with the setup of the full
competition.
* Add stochastically decreasing rewards?
* Related with above: make sure that the correct answer is the least resistance
path. That is, if a learner is not going to receive a reward for a task,
it should still be more efficient (shorter) solving it correctly than
incorrectly.
* If the task ends without a message, a useless task-separating silence
is issued. This should not be the case, although in practice I don't think
we currently have any task behaving like that (there's always feedback).

#Tasks:
* Move the documentation of the tasks to the code

* Association:
  * Tell me an object with property X, an object with property Y and an object with property Z, in that order, from B’s basket
  * Tell me a property of object X, a property of object Y and a property of object Z, in that order, from B’s basket

* Mixing asking questions and association:

  * Reframe some of the current association tasks using the same association table, but encouraging the Learner to ask for questions if it doesn’t remember something

* Objects:
 * Giving objects to the learner and Q&A
 * Placing objects near the learner (in front, left, right, …) and Q&A on objects and relations (properties)
 * Spatial relationships
 * Asking about the number of objects with relation to the location
 * Pick / Drop objects

* Grid:
 * Navigation / Finding objects

* Algebraic patterns
 * No clear idea here, but something inspired by Marcus/Dehaene experiments such as:
    * Prime: papata mumula…
    * Expected target: fefero; surprising target: ferofe

* Paired associate inference and transitive inference

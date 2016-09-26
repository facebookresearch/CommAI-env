from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import on_start, on_message, on_timeout
from tasks.competition.base import BaseTask
import tasks.competition.messages as msg
import random

# global data structures to be called by multiple tasks

# a dictionary with all possible objects in the vocabulary
vocabulary = {
    0: "apple", 1: "banana", 2: "beet", 3: "carrot", 4: "cucumber", 5: "mango",
    6: "onion", 7: "pear", 8: "pineapple", 9: "potato", 10: "tomato"}

# maximum number of objects to list
max_total = 10

vocab_size = len(vocabulary)


class SimpleCountingTask(BaseTask):
    def __init__(self, world=None):
        super(SimpleCountingTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):

        separator = ""
        counter = {}
        partial_message = ""

        # pick how many objects in total will be described
        total = random.randint(1, max_total)

        for i in range(0, total):
            # for last object change separator from "," to "and"
            if i == total - 2:
                separator = " and "
            elif i == total - 1:
                separator = ""
            else:
                separator = ", "

            # pick object
            obj = vocabulary[random.randint(1, vocab_size - 1)]

            # build up message
            partial_message += msg.indef_article(obj)
            partial_message += separator

            # update counter
            if obj not in counter:
                counter[obj] = 0
            counter[obj] += 1

        # pick object to ask the question
        object_in_question = vocabulary[random.randint(1, vocab_size - 1)]

        self.answer = msg.numbers_in_words[counter.get(object_in_question, 0)]

        self.give_away_message = 'Wrong. The right answer is: {answer}.'.format(
            answer=self.answer
        )

        self.set_message("I have {listing_objects}. How many {object} do I have? "\
            .format(
                listing_objects=partial_message,
                object=msg.pluralize(object_in_question, 2)
        ))

    @on_message(r'\.')
    def check_response(self, event):
        # check if given answer matches
        if event.is_message(self.answer, '.'):
            # if the message sent by the learner equals the teacher's
            # expected answer followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.
        self.fail_learner()

    def fail_learner(self):
        # fail the learner sending a random fail feedback message
        self.set_reward(0, self.give_away_message)

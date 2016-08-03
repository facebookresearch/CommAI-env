# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_init
from worlds.grid_world import Point, Span
import random
import re

# global variables for basic logic
gl_logic_operators_verb = ["dont", ""]
gl_logic_operators = ["and", "or"]

gl_objects = ["banana", "apple"]



class RepeatingTaskLogical2Objects(Task):
    def __init__(self):
        super(RepeatingTaskLogical2Objects, self).__init__(max_time=3000)

    @on_start()
    def on_start(self, event):
 	print "Tralala"

	#create expression
	self.negation_1 = gl_logic_operators_verb[random.randint(0, 1)]
	self.negation_2 = gl_logic_operators_verb[random.randint(0, 1)]
	self.logic_operator = gl_logic_operators[random.randint(0, 1)]
	self.objects = [gl_objects[random.randint(0, 1)], gl_objects[random.randint(0, 1)]]


	#compile message and answer
	self.answer = self.objects[:]
	message = ""
	if self.negation_1 == "dont":
		self.answer.pop(0)
	if self.negation_2 == "dont":
		self.answer.pop(0)
		message = " ".join([self.negation_1, "say", self.objects[0], self.logic_operator, self.negation_2, "say", self.objects[1]])
	else:
		message = " ".join([self.negation_1, "say", self.objects[0], self.logic_operator, self.negation_2, self.objects[1]])

        print(message)
	self.set_message(message)

	#compile answer match
	re_string = re_string = "([a-z]*)[ ]*(and|,|)[ ]*([a-z]*)"
	self.delim_answer = ["and", " ", ",", ""]
	self.re_answer = re.compile(re_string)


    @on_message()
    def on_message(self, event):

        matches=self.re_answer.match(event.message)
	m = matches.groups()
	if not m[1] in self.delim_answer:
		correct = False
		self.set_reward(0)
	else:
		overlap = len(set(self.answer)&set([m[0], m[2]]))/len(self.answer)
		correct = (self.logic_operator=="and" and overlap == 1) or (self.logic_operator=="or" and overlap==0.5)
        	if correct:
        		self.set_reward(1)
		else:
			self.set_reward(0)

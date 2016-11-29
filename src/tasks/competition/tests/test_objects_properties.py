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
import unittest
import tasks.competition.messages as msg
import tasks.competition.objects_properties as objects_properties
from tasks.competition.tests.helpers import task_messenger
import random

global_properties = objects_properties.global_properties


class TestObjectsProperties(unittest.TestCase):

    #
    # helper methods
    #
    def check_positive_feedback(self, m, instructions, answer):
        # hear the congratulations
        feedback_blen = m.read()
        # there is some feedback
        self.assertGreater(feedback_blen, 0,
                           "answering '{0}' to query '{1}' didn't work.".format(
                               answer, instructions))
        m.send()
        self.assertEqual(m.get_cumulative_reward(), 1,
                         "answering '{0}' to query '{1}' didn't work.".format(
                             answer, instructions))

    def check_negative_feedback(self, m, exp_answer):
        # hear the feedback
        m.read()
        answer, = m.search_last_message(
            r"(?:one|the) right \w+ (?:is|are): (.+)\.$")
        m.send()

        try:
            # the answer could be a space-separated list that
            # solves the task in any order
            self.assertEqual(set(self.string_to_enum(exp_answer)),
                             set(self.string_to_enum(answer)),
                             "{0} != {1}".format(exp_answer, answer))
        except AttributeError:
            # exp_answer is not a string and thus,
            # the expected answer is a collection of possibilities
            self.assertIn(answer, exp_answer)

    def solve_correctly_test(self, m, get_correct_answer):
        # read the instructions
        m.read()
        # get the instructions
        instructions = m.get_last_message()
        # get the answer
        answer = get_correct_answer(m)[0]
        # send the answer with the termination marker
        m.send("{0}.".format(answer))
        # hear the congratulations
        self.check_positive_feedback(m, instructions, answer)

    def solve_interrupting_teacher(self, m, get_correct_answer):
        # read the instructions up to the point we can get the answer
        m.read_until(get_correct_answer)
        # get the answer
        answer = get_correct_answer(m)[0]
        # borderline condition: send the first character and
        # check that the teacher hasn't just stopped talking
        # (if it did, then this would be a good response, and it's not
        # what we are testing here)
        m.send(answer[0])
        self.assertFalse(m.is_silent(), "failed to interrupt teacher: "
                    "correct answer detected too late.")
        # send the rest of the answer with the termination marker
        m.send("{0}.".format(answer[1:]))
        # interrupting the teacher shouldn't have worked for us
        self.assertEqual(m.get_cumulative_reward(), 0)
        # wait for the teacher to stop talking
        m.read()
        # get the instructions
        instructions = m.get_last_message()
        # still no reward
        self.assertEqual(m.get_cumulative_reward(), 0)
        # get the answer now that the teacher is silent
        answer = get_correct_answer(m)[0]
        # send the answer with the termination marker
        m.send("{0}.".format(answer))
        # hear the congratulations
        self.check_positive_feedback(m, instructions, answer)

    def timeout_test(self, m, get_correct_answer):
        # read the instructions
        m.read()
        # get the answer
        answer = get_correct_answer(m)
        # check if the answer is a collection of possibilities or just
        # one option
        answer = answer[1] if len(answer) > 1 else answer[0]
        # stay silent
        while m.is_silent():
            m.send()
        # hear the correction
        self.check_negative_feedback(m, answer)

    def do_test_battery(self, task, get_correct_answer):
        with task_messenger(task) as m:
            # test for solving the task correctly
            self.solve_correctly_test(m, get_correct_answer)
        with task_messenger(task) as m:
            # test for not solving it at all
            self.timeout_test(m, get_correct_answer)
        with task_messenger(task) as m:
            # test for not solving it at all
            self.solve_interrupting_teacher(m, get_correct_answer)

    separators = [" ", " and ", ", ", ", and "]

    def enum_to_string(self, lst):
        sep = random.choice(self.separators)
        return sep.join(lst)

    def string_to_enum(self, strlst):
        # check whether strlst has split (to see if it's a string)
        splitting = strlst.split
        for sep in sorted(self.separators,
                          key=lambda x: -len(x)):
            if sep in strlst:
                return splitting(sep)
        return [strlst]

    #
    # tasks testing routines
    #
    def testAssociateObjectWithProperty(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            property_, = m.search_last_message(r"basket is (\w+)")
            return property_,
        self.do_test_battery(objects_properties.AssociateObjectWithPropertyTask,
                             get_correct_answer)

    def testVerifyThatObjectHasProperty(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            object_, property_, basket = m.search_last_message(
                r"(\w+) (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            # send the answer with the termination marker
            if property_ in global_properties[basket][object_]:
                answer = "yes"
            else:
                answer = "no"
            return answer,
        self.do_test_battery(objects_properties.VerifyThatObjectHasPropertyTask,
                             get_correct_answer)

    def testListPropertiesOfAnObject(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            object_, basket = m.search_last_message(
                r"does (\w+) have in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            answer = self.enum_to_string(global_properties[basket][object_])
            return answer,
        self.do_test_battery(objects_properties.ListPropertiesOfAnObjectTask,
                             get_correct_answer)

    def testNameAPropertyOfAnObject(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            object_, basket = m.search_last_message(r"of (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            all_answers = global_properties[basket][object_]
            answer = random.choice(all_answers)
            return answer, all_answers
        self.do_test_battery(objects_properties.NameAPropertyOfAnObjectTask,
                             get_correct_answer)

    def testHowManyPropertiesDoesAnObjectHave(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            object_, basket = m.search_last_message(
                r"does (\w+) have in (\w+)'s")
            if basket in global_properties and \
                    object_ in global_properties[basket]:
                props = global_properties[basket][object_]
                all_answers = [str(len(props))]
                if len(props) <= len(msg.numbers_in_words):
                    all_answers.append(msg.numbers_in_words[len(props)])
            else:
                all_answers = ["0", "zero"]
            answer = random.choice(all_answers)
            return answer, all_answers
        self.do_test_battery(
            objects_properties.HowManyPropertiesDoesAnObjectHaveTask,
            get_correct_answer)

    def testListObjectsWithACertainProperty(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            property_, basket = m.search_last_message(
                r"objects are (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            answer = [object_ for object_ in
                        global_properties[basket]
                        if property_ in
                        global_properties[basket][object_]]
            return " ".join(answer),
        self.do_test_battery(
            objects_properties.ListObjectsWithACertainPropertyTask,
            get_correct_answer)

    def testNameAnObjectWithAProperty(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            property_, basket = m.search_last_message(r"is (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            all_answers = [object_ for object_ in
                            global_properties[basket]
                            if property_ in
                            global_properties[basket][object_]]
            answer = random.choice(all_answers)
            self.assertTrue(all_answers, "There are no objects {0} "
                            "in {1}'s basket".format(property_, basket))
            return answer, all_answers
        self.do_test_battery(
            objects_properties.NameAnObjectWithAPropertyTask,
            get_correct_answer)

    def testHowManyObjectsHaveACertainProperty(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            property_, basket = m.search_last_message(
                r"objects are (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            objects = [object_ for object_ in
                            global_properties[basket]
                            if property_ in
                            global_properties[basket][object_]]
            num_objects = len(objects)
            all_answers = [str(num_objects)]
            if num_objects <= len(msg.numbers_in_words):
                all_answers.append(
                    msg.numbers_in_words[num_objects])
            answer = random.choice(all_answers)
            return answer, all_answers
        self.do_test_battery(
            objects_properties.HowManyObjectsHaveACertainPropertyTask,
            get_correct_answer)

    def testWhoHasACertainObjectWithACertainProperty(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            property_, object_ = m.search_last_message(
                r"(\w+) (\w+) in the")
            baskets = [basket for basket, object_props in
                        global_properties.items()
                        if object_ in object_props and
                        property_ in object_props[object_]]
            if not baskets:
                answer = "nobody"
            else:
                answer = " ".join(baskets)
            return answer,
        self.do_test_battery(
            objects_properties.WhoHasACertainObjectWithACertainPropertyTask,
            get_correct_answer)

    def testListThePropertiesThatAnObjectHasInABasketOnly(self):
        def get_correct_answer(m):
            # find the answer in the instructions
            object_, basket = m.search_last_message(
                r"(\w+) have in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            properties = set(global_properties[basket][object_])
            comp_baskets_props = set.union(
                *[set(object_props[object_])
                    for basket2, object_props in
                    global_properties.items() if basket2 != basket])
            properties_basket_only = properties - comp_baskets_props
            if properties_basket_only:
                answer = " ".join(properties_basket_only)
            else:
                answer = "none"
            return answer,
        self.do_test_battery(
            objects_properties.ListThePropertiesThatAnObjectHasInABasketOnlyTask,
            get_correct_answer)

        def testListThePropertiesThatAnObjectHasInAllBaskets(self):
            def get_correct_answer(m):
                # find the answer in the instructions
                object_, = m.search_last_message(
                    r"does (\w+) have")
                all_baskets_props = set.union(
                    *[set(object_props[object_]
                            if object_ in object_props else [])
                        for basket2, object_props in
                        global_properties.items()])
                if all_baskets_props:
                    answer = " ".join(all_baskets_props)
                else:
                    answer = "none"
                return answer,
            self.do_test_battery(
                objects_properties.ListThePropertiesThatAnObjectHasInAllBasketsTask,
                get_correct_answer)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

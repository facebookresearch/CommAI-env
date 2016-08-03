from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_init
from tasks.competition.base import BaseTask
import tasks.competition.messages as msg
import random
import string

# global data structures to be called by multiple tasks

# properties of objects in two baskets, for memory tasks
# (please keep objects in alphabetical order for ease of debugging)
global_properties = {
    'john': {
        'apple':
            ['green', 'sour', 'hard', 'cheap', 'healthy', 'juicy',
              'local'],
        'banana':
            ['yellow', 'sweet', 'soft', 'cheap', 'healthy', 'exotic',
             'ripe'],
        'beet':
            ['red', 'dirty', 'hard', 'old', 'cheap', 'sweet', 'healthy',
             'local', 'large'],
        'carrot':
            ['orange', 'hard', 'fresh', 'local', 'healthy', 'sweet',
             'crunchy'],
        'cucumber':
            ['green', 'fresh', 'juicy', 'local', 'cheap', 'healthy',
             'frozen', 'crunchy'],
        'mango':
            ['brown', 'rotten'],
        'onion':
            ['white', 'pungent', 'smelly', 'cheap', 'local', 'healthy'],
        'pear':
            ['brown', 'sweet', 'dry', 'cheap', 'local', 'big'],
        'pineapple':
            ['yellow', 'sweet', 'hard', 'exotic', 'brown', 'rough'],
        'potato':
            ['yellow', 'old', 'cheap', 'hard', 'tasteless', 'dirty',
             'bumpy'],
        'tomato':
            ['red', 'soft', 'sour', 'juicy', 'local', 'cheap']},
    'mary': {
        'apple':
            ['red', 'sweet', 'hard', 'fresh', 'juicy', 'expensive',
             'crunchy'],
        'asparagus':
            ['white', 'soft', 'old', 'long', 'expensive', 'dirty'],
        'avocado':
            ['green', 'ripe', 'exotic', 'expensive', 'large', 'healthy',
             'smooth', 'buttery'],
        'banana':
            ['yellow', 'tasteless', 'soft', 'sweet', 'old', 'exotic'],
        'carrot':
            ['orange', 'hard', 'old', 'dirty', 'local', 'small', 'crunchy'],
        'cucumber':
            ['green', 'fresh', 'hard', 'cheap', 'local', 'long'],
        'onion':
            ['yellow', 'old', 'cheap', 'dry', 'local', 'large'],
        'mango':
            ['red', 'green', 'yellow', 'juicy', 'sweet', 'expensive'],
        'pear':
            ['green', 'tasteless', 'hard', 'local', 'cheap', 'big'],
        'pineapple':
            ['yellow', 'sweet', 'dry', 'fresh', 'expensive', 'exotic'],
        'tomato':
            ['red', 'soft', 'sour', 'local', 'cheap']}
}

# it's handy to have a reverse dictionary with the properties in the
# above lists as keys, and the objects as values
reverse_global_properties = {}
for basket in global_properties:
    reverse_global_properties[basket] = {}
    for object in global_properties[basket]:
        for property in global_properties[basket][object]:
            if property not in reverse_global_properties[basket]:
                reverse_global_properties[basket][property] = []
            reverse_global_properties[basket][property].append(object)


# a list of questions about a number, shared by multiple tasks
number_questions = ['please tell me the number.',
                    'what\'s the number?',
                    'what is the number?',
                    'can you tell me the number?']

# when an enumeration is given, each element but the last could be followed by:
# ', ', ' and ', or ', and ' or ' '
delimiters = r'(?:, | and |, and | )'


class AssociateObjectWithPropertyTask(BaseTask):
    def __init__(self, world=None):
        super(AssociateObjectWithPropertyTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # pick some random basket, object and property
        basket = random.choice(global_properties.keys())
        object_ = random.choice(global_properties[basket].keys())
        self.property = random.choice(global_properties[basket][object_])
        # ask the leearner for the property
        self.set_message("{object} in {owner}'s basket is {property}. "
                         "how is {object}?".format(
                             object=object_,
                             owner=basket,
                             property=self.property
                         ))

    @on_message(r"\.")
    def check_response(self, event):
        if event.is_message(self.property, '.'):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        self.set_message('the right answer is: {answer}.'.format(
            answer=self.property
        ))


class VerifyThatObjectHasPropertyTask(BaseTask):
    def __init__(self, world=None):
        super(VerifyThatObjectHasPropertyTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        basket = random.choice(global_properties.keys())
        object_ = random.choice(global_properties[basket].keys())
        object_properties = global_properties[basket][object_]
        # extracting the set of properties (from both baskets)
        all_properties = set(property_
                             for temp_basket, object_properties in
                                global_properties.items()
                             for temp_object, temp_properties in
                                object_properties.items()
                             for property_ in temp_properties)
        # find the properties that that the selected objects does NOT have
        properties_complement = list(all_properties - set(object_properties))
        # deciding if we'll ask about the true or false property
        self.coin_flip = random.randint(0, 1)
        if not self.coin_flip:
            # ask for a false property
            property_ = random.choice(properties_complement)
            self.answer = "no"
        else:
            # ask for a true property
            property_ = random.choice(object_properties)
            self.answer = "yes"
        self.set_message("is {object} {property} in {owner}'s basket?'"
                         .format(
                             object=object_,
                             property=property_,
                             owner=basket
                         ))

    @on_message()
    def check_response(self, event):
        if event.is_message(self.answer, '.'):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        self.set_message('the right answer is: ' + self.answer + '.')


class ListPropertiesofAnObjectTask(BaseTask):
    def __init__(self, world=None):
        super(ListPropertiesofAnObjectTask, self).__init__(
            world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # select a random object from a random basket
        basket = random.choice(global_properties.keys())
        object_ = random.choice(global_properties[basket].keys())
        # retrieving the properties of the selected object
        self.object_properties = set(global_properties[basket][object_])

        self.set_message("which properties does {object} have in "
                         "{owner}'s basket?".format(
                             object=object_,
                             owner=basket))

        # building a regexp to match the answer
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.object_properties))
        # final string must be delimited by period
        enum_re += r'\.$'
        # add check_response as a handler for a message matching the
        # above described enumeration
        self.add_handler(on_message(enum_re)(self.check_response))

    # on_message handler created dynamically when the number of
    # expected responses is known
    def check_response(self, event):
        # get all the elements in the matched enumeration
        potential_properties = set(event.get_match_groups())
        # if the produced elements match the expected properties
        # reward the learner
        if (self.object_properties == potential_properties):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        correct_properties = list(self.object_properties)
        random.shuffle(correct_properties)
        answer = " ".join(correct_properties)
        self.set_message('the right properties are: {answer}.'.format(
            answer=answer
        ))


class NameAPropertyOfAnObjectTask(BaseTask):
    def __init__(self, world=None):
        super(NameAPropertyOfAnObjectTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # pick some basket and object
        basket = random.choice(global_properties.keys())
        object_ = random.choice(global_properties[basket].keys())
        # retrieving the properties of the selected object
        self.object_properties = global_properties[basket][object_]

        self.set_message("can you tell me a property of {object} "
                         "in {owner}'s basket?".format(
                             object=object_,
                             owner=basket
                         ))

    @on_message()
    def check_response(self, event):
        # traverse properties list, and see if you find one that is
        # matching
        if any(event.is_message(property_, '.')
                for property_ in self.object_properties):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        # randomly picked right property
        self.set_message('one right answer is: {answer}.'.format(
            answer=random.choice(self.object_properties)
        ))


class HowManyPropertiesDoesAnObjectHaveTask(BaseTask):
    def __init__(self, world=None):
        super(HowManyPropertiesDoesAnObjectHaveTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # pick some object in a random basket
        basket = random.choice(global_properties.keys())
        object_ = random.choice(global_properties[basket].keys())
        # counting properties of selected object
        self.property_count = len(global_properties[basket][object_])
        self.set_message("how many property does {object} have "
                         "in {owner}'s basket?".format(
                             object=object_,
                             owner=basket
                         ))

    @on_message()
    def check_response(self, event):
        # check if the answer matches any of the possible ways of expressing
        # the correct number.
        if any(event.is_message(correct_alt, '.')
               for correct_alt in msg.number_to_strings(self.property_count)):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        # inform the answer randomly choosing a numeric or alphabetic format.
        self.set_message('the right answer is: {answer}.'.format(
            answer=msg.number_to_string(self.property_count)
        ))


class ListObjectsWithACertainPropertyTask(BaseTask):
    def __init__(self, world=None):
        super(ListObjectsWithACertainPropertyTask, self).__init__(
            world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # chose a random property
        basket = random.choice(reverse_global_properties.keys())
        property_ = random.choice(reverse_global_properties[basket].keys())
        # retrieving the objects that have this property
        self.objects = set(reverse_global_properties[basket][property_])

        self.set_message("which objects are {property} in "
                         "{owner}'s basket?".format(
                             property=property_,
                             owner=basket))

        # building a regexp to match the answer
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.objects))
        # final string must be delimited by period
        enum_re += r'\.$'
        # register a handler that get triggers when an enumeration
        # as described by the regular expression is found.
        self.add_handler(on_message(enum_re)(self.check_response))

    # on_message handler created dynamically when the number of
    # expected responses is known
    def check_response(self, event):
        # get the elements in the matched enumeration
        potential_objects = set(event.get_match_groups())
        # if the elements match the expected objects, reward the learner
        if self.objects == potential_objects:
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        correct_objects = list(self.objects)
        random.shuffle(correct_objects)
        self.set_message('the right objects are: {answer}.'.format(
            answer=" ".join(correct_objects)
        ))


class NameAnObjectWithAPropertyTask(BaseTask):
    def __init__(self, world=None):
        super(NameAnObjectWithAPropertyTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # chose a random property
        basket = random.choice(reverse_global_properties.keys())
        property_ = random.choice(reverse_global_properties[basket].keys())
        # retrieving the objects that have the selected property
        self.objects = reverse_global_properties[basket][property_]

        self.set_message("can you tell me an object that is {property} "
                         "in {owner}'s basket?".format(
                             property=property_,
                             owner=basket
                         ))

    @on_message()
    def check_response(self, event):
            # traverse objects list, and see if you find one that is
            # matching
            if any(event.is_message(object_, '.')
                   for object_ in self.objects):
                # is match found, give reward
                self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        # randomly random right property
        self.set_message('one right answer is: {answer}.'.format(
            answer=random.choice(self.objects)
        ))


class HowManyObjectsHaveACertainPropertyTask(BaseTask):
    def __init__(self, world=None):
        super(HowManyObjectsHaveACertainPropertyTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # we will sample from the actual properties, plus a random
        # string representing a "property" that no object has
        basket = random.choice(reverse_global_properties.keys())
        basket_properties = reverse_global_properties[basket].keys()
        property_pick = random.randint(0, len(basket_properties))
        if property_pick == len(basket_properties):
            # if we picked the last integer, we will generate a fake property
            # for which the answer should be 0
            property_ = self.get_random_property(basket_properties)
            self.object_count = 0
        else:
            # if instead we picked an integer within the property range,
            # let's retrieve the objects and count them
            property_ = basket_properties[property_pick]
            self.object_count = len(
                reverse_global_properties[basket][property_])

        self.set_message("how many objects are {property} in {owner}'s basket?"
                         .format(
                             property=property_,
                             owner=basket
                         ))

    def get_random_property(self, basket_properties):
        # return a random property that is not in basket_properties
        while True:
            # generate random property
            property_ = "".join(random.sample(string.ascii_lowercase,
                                              random.randint(1, 10)))
            # make sure this is not, by chance, identical to a real property
            # in the relevant basket
            if property_ not in basket_properties:
                break
        return property_

    @on_message()
    def check_response(self, event):
        # check if the answer matches any of the possible ways of expressing
        # the correct number.
        if any(event.is_message(correct_alt, '.')
               for correct_alt in msg.number_to_strings(self.object_count)):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        # inform the answer randomly choosing a numeric or alphabetic format.
        self.set_message('the right answer is: {answer}.'.format(
            answer=msg.number_to_string(self.object_count)
        ))


class WhoHasACertainObjectWithACertainPropertyTask(BaseTask):
    def __init__(self, world=None):
        super(WhoHasACertainObjectWithACertainPropertyTask, self).__init__(
            world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        object_, property_ = self.get_random_object_property()
        # we find the set of baskets that have the relevant
        # object and property combination
        self.basket_set = set(basket for basket, object_properties
                                in global_properties.items()
                                if object_ in object_properties and
                                   property_ in object_properties[object_])
        # at this point, if baskets list is empty we add "nobody" as
        # the only item in it
        if not self.basket_set:
            self.basket_set.add('nobody')

        self.set_message("who has {property_object} in the basket?".format(
            property_object=msg.indef_article(property_ + " " + object_)))

        # building a regexp to match the answer
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.basket_set))
        # final string must be delimited by period
        enum_re += r'\.$'
        # add a handler to match the response
        self.add_handler(on_message(enum_re)(self.check_response))

    def get_random_object_property(self):
        # we traverse the baskets building sets of all the objects and
        # properties they contain as well as dictionary of sets
        # recording the object+property pairs present in each basket
        objects_set = set([object_
                           for basket, object_properties
                           in global_properties.items()
                           for object_ in object_properties])
        properties_set = set([property_
                              for basket, property_objects
                              in reverse_global_properties.items()
                              for property_ in property_objects])
        # now we build a random object+property combination from the
        # sets of objects and properties in both baskets
        object_ = random.choice(list(objects_set))
        property_ = random.choice(list(properties_set))
        return object_, property_

    # on_message handler created dynamically when the number of
    # expected responses is known
    def check_response(self, event):
        # retrieve the set of matched elements
        potential_baskets = set(event.get_match_groups())
        # if the elements match the expected set of baskets, reward the learner
        if self.basket_set == potential_baskets:
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        correct_baskets = list(self.basket_set)
        random.shuffle(correct_baskets)
        self.set_message('the right baskets are: {answer}.'.format(
            answer=" ".join(correct_baskets)
        ))


class ListThePropertiesThatAnObjectHasInABasketOnlyTask(BaseTask):
    def __init__(self, world=None):
        super(ListThePropertiesThatAnObjectHasInABasketOnlyTask, self).__init__(
            world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # get an object that appears in a least two baskets
        object_, object_baskets = self.get_object_in_many_baskets()
        # choose one of the baskets
        basket = random.choice(object_baskets)
        # ask the learner
        self.set_message("which properties does {object} have "
                         "in {owner}'s basket only?".format(
                             object=object_,
                             owner=basket
                         ))
        # construct the expected answer which is given by the
        # properties of the object in the given basket minus
        # the properties in all the rest of the baskets:
        self.distinctive_properties_set = self.get_expected_answer(
            object_, basket, object_baskets
        )

        # building a regexp to match the answer
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.distinctive_properties_set))
        # final string must be delimited by period
        enum_re += r'\.$'
        # add a handler to match the response
        self.add_handler(on_message(enum_re)(self.check_response))

    def get_expected_answer(self, object_, basket, object_baskets):
        # get the properties for the object in the chosen basket
        properties_in_basket = set(global_properties[basket][object_])
        # get the list of properties that the object has in the given basket
        # but not in the others.
        properties_in_other_baskets = set(
            prop for other_basket in object_baskets
            for prop in global_properties[other_basket][object_]
            if other_basket != basket)
        # we finally the set of properties that the object only has in
        # the selected basket
        distinctive_properties_set = properties_in_basket - \
            properties_in_other_baskets

        # if distinctive properties set is empty we add "none" as
        # the only item in it
        if not distinctive_properties_set:
            distinctive_properties_set.add('none')
        return distinctive_properties_set

    def get_object_in_many_baskets(self):
        # we traverse the baskets recording, for each object,
        # the baskets it is in
        baskets_with_object = {}
        for basket in global_properties:
            for obj in global_properties[basket]:
                if obj not in baskets_with_object:
                    baskets_with_object[obj] = []
                baskets_with_object[obj].append(basket)
        # traverse baskets_with_object, keeping track of those objects
        # that occur in more than one basket (otherwise the "only"
        # question does not make sense due to a presuppostion
        # violation)
        legit_objects = [obj for obj, baskets in baskets_with_object.items()
                             if len(baskets) > 1]
        # now we pick a random object from this list
        object_ = random.choice(legit_objects)
        # return the object together with the baskets where it occurs
        return object_, baskets_with_object[object_]

    # on_message handler created dynamically when the number of
    # expected responses is known
    def check_response(self, event):
        potential_properties = set(event.get_match_groups())
        if self.distinctive_properties_set == potential_properties:
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        correct_properties = list(self.distinctive_properties_set)
        random.shuffle(correct_properties)
        self.set_message('the right properties are: {answer}.'.format(
            answer=" ".join(correct_properties)
        ))


class ListThePropertiesThatAnObjectHasInAllBasketsTask(BaseTask):
    def __init__(self, world=None):
        super(ListThePropertiesThatAnObjectHasInAllBasketsTask, self).__init__(
            world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # get an object that appears in a least two baskets
        object_, object_baskets = self.get_object_in_many_baskets()
        # ask the learner
        self.set_message("which properties does {object} have "
                         "in all baskets?".format(
                             object=object_
                         ))
        # construct the expected answer which is given by the
        # properties of the object in the given basket minus
        # the properties in all the rest of the baskets:
        self.shared_properties_set = self.get_expected_answer(
            object_, object_baskets
        )

        # building a regexp to match the answer
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.shared_properties_set))
        # final string must be delimited by period
        enum_re += r'\.$'
        # add a handler to match the response
        self.add_handler(on_message(enum_re)(self.check_response))

    def get_expected_answer(self, object_, object_baskets):
        # get the properties that are present in all the baskets
        # for the selected object
        shared_properties_set = set.intersection(*[
            set(prop for prop in global_properties[basket])
            for basket in object_baskets])
        # if set is empty, we put 'none' in it
        if shared_properties_set:
            shared_properties_set.add('none')
        return shared_properties_set

    def get_object_in_many_baskets(self):
        # we traverse the baskets recording, for each object,
        # the baskets it is in
        baskets_with_object = {}
        for basket in global_properties:
            for obj in global_properties[basket]:
                if obj not in baskets_with_object:
                    baskets_with_object[obj] = []
                baskets_with_object[obj].append(basket)
        # traverse baskets_with_object, keeping track of those objects
        # that occur in more than one basket (otherwise the "only"
        # question does not make sense due to a presuppostion
        # violation)
        legit_objects = [obj for obj, baskets in baskets_with_object.items()
                             if len(baskets) > 1]
        # now we pick a random object from this list
        object_ = random.choice(legit_objects)
        # return the object together with the baskets where it occurs
        return object_, baskets_with_object[object_]

    # on_message handler created dynamically when the number of
    # expected responses is known
    def check_response(self, event):
        potential_properties = set(event.get_match_groups())
        if self.shared_properties_set == potential_properties:
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        correct_properties = list(self.shared_properties_set)
        random.shuffle(correct_properties)
        self.set_message('the right properties are: {answer}.'.format(
            answer=" ".join(correct_properties)
        ))

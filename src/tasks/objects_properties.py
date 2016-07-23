from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_init
from tasks.base import BaseTask
import tasks.messages as msg
import random
import string
import re

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
    def __init__(self, env):
        super(AssociateObjectWithPropertyTask, self).__init__(
            env, max_time=3000)

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
    def __init__(self, env):
        super(VerifyThatObjectHasPropertyTask, self).__init__(
            env, max_time=3000)

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
    def __init__(self, env):
        super(ListPropertiesofAnObjectTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # select a random object from a random basket
        basket = random.choice(global_properties.keys())
        object_ = random.choice(global_properties[basket].keys())
        # retrieving the properties of the selected object
        self.object_properties = set(global_properties[basket][object_])

        # building a regexp to match the answer
        re_string = delimiters.join(
            [r'([a-z]+)'] * len(self.object_properties))
        # final string must be delimited by period
        re_string += r'\.$'
        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        self.set_message("which properties does {object} have in "
                         "{owner}'s basket?".format(
                             object=object_,
                             owner=basket))

    @on_message()
    def check_response(self, event):
        # does end of agent message match regexp?
        match = self.re_query.search(event.message)
        if match:
            # if it does, let's parse the parts of the match
            potential_properties = set(match.groups())
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
    def __init__(self, env):
        super(NameAPropertyOfAnObjectTask, self).__init__(
            env, max_time=3000)

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
    def give_away_answer(self,event):
        # randomly picked right property
        self.set_message('one right answer is: {answer}.'.format(
            answer=random.choice(self.object_properties)
        ))


class HowManyPropertiesDoesAnObjectHaveTask(BaseTask):
    def __init__(self, env):
        super(HowManyPropertiesDoesAnObjectHaveTask, self).__init__(
            env, max_time=3000)

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
    def __init__(self, env):
        super(ListObjectsWithACertainPropertyTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # chose a random property
        basket = random.choice(reverse_global_properties.keys())
        property_ = random.choice(reverse_global_properties[basket].keys())
        # retrieving the objects that have this property
        self.objects = set(reverse_global_properties[basket][property_])

        # building a regexp to match the answer
        re_string = delimiters.join(
            [r'([a-z]+)'] * len(self.objects))
        # final string must be delimited by period
        re_string += r'\.$'
        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        self.set_message("which objects are {property} in "
                         "{owner}'s basket?".format(
                             property=property_,
                             owner=basket))

    @on_message()
    def check_response(self, event):
        # does end of agent message match regexp?
        matches = self.re_query.search(event.message)
        if matches:
            # if it does, let's parse the parts of the match
            potential_objects = set(matches.groups())
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
    def __init__(self, env):
        super(NameAnObjectWithAPropertyTask, self).__init__(
            env, max_time=3000)

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
    def __init__(self, env):
        super(HowManyObjectsHaveACertainPropertyTask, self).__init__(
            env, max_time=3000)

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
            while True:
                # generate random property
                property_ = "".join(random.sample(string.ascii_lowercase,
                                                  random.randint(1, 10)))
                # make sure this is not, by chance, identical to a real property
                # in the relevant basket
                if property_ not in basket_properties:
                    break
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
    def __init__(self, env):
        super(WhoHasACertainObjectWithACertainPropertyTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # we traverse the baskets building sets of all the objects and
        # properties they contain as well as dictionary of sets
        # recording the object+property pairs present in each basket
        objects_set = [object_
                          for basket, object_properties
                          in global_properties.items()
                          for object_ in object_properties]
        properties_set = [property_
                             for basket, property_objects
                             in reverse_global_properties.items()
                             for property_ in property_objects]
        # now we build a random object+property combination from the
        # sets of objects and properties in both baskets
        object_ = random.choice(list(objects_set))
        property_ = random.choice(list(properties_set))
        # we build a set of baskets that have the relevant
        # object property combination
        self.basket_set = set(basket for basket, object_properties
                                in global_properties.items()
                                if object_ in object_properties and
                                   property_ in object_properties[object_])
        # at this point, if baskets list is empty we add "nobody" as
        # the only item in it
        if not self.basket_set:
            self.basket_set.add('nobody')

        # building a regexp to match the answer
        re_string = delimiters.join(
            [r'([a-z]+)'] * len(self.basket_set))
        # final string must be delimited by period
        re_string += r'\.$'

        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        self.set_message("who has {property_object} in the basket?".format(
            property_object=msg.indef_article(property_ + " " + object_)))

    @on_message()
    def check_response(self, event):
        # does end of agent message match regexp?
        matches = self.re_query.search(event.message)
        if matches:
            # if it does, let's parse the parts of the match
            potential_baskets = set(matches.groups())
            if self.basket_set == potential_baskets:
                self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        correct_baskets = list(self.basket_set)
        random.shuffle(correct_baskets)
        self.set_message('the right baskets are: {answer}.'.format(
            answer=" ".join(correct_baskets)
        ))


class ListThePropertiesThatAnObjectHasInABasketOnlyTask(Task):
    def __init__(self, env):
        super(ListThePropertiesThatAnObjectHasInABasketOnlyTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # we traverse the baskets recording, for each object, the baskets it is in
        baskets_with_object={}
        for basket in global_properties:
            for object in global_properties[basket]:
                if (not object in baskets_with_object):
                    baskets_with_object[object]=[basket]
                else:
                    baskets_with_object[object].append(basket)

        # traverse baskets_with_object, keeping track of those objects
        # that occur in more than one basket (otherwise the "only"
        # question does not make sense due to a presuppostion
        # violation)
        legit_objects = [object for object in baskets_with_object if len(baskets_with_object[object])>1]
        # now we pick a random object from this list, and a random basket for that object
        object = random.choice(legit_objects)
        # we treat the first item in the shuffled list of baskets with the object as the target basket:
        random.shuffle(baskets_with_object[object])
        basket = baskets_with_object[object][0]
        # we get the set of properties of the object in the other baskets
        properties_in_other_baskets = set()
        for other_basket in baskets_with_object[object][1:]:
            properties_in_other_baskets=properties_in_other_baskets.union(set(global_properties[other_basket][object]))
        # we finally the set of properties that the object only has in the selected basket
        self.distinctive_properties_set = set(global_properties[basket][object]) - properties_in_other_baskets
        # if distinctive properties set is empty we add "none" as
        # the only item in it
        if (not self.distinctive_properties_set):
            self.distinctive_properties_set.add('none')

        # building the regexp query
        re_string = '.*?'
        # each property name but the last could be followed by:
        # ', ', ' and ', or ', and ' or ' '

        for i in range(len(self.distinctive_properties_set)-1):
            re_string += '([a-z]+)(, | and |, and | )'
        # final string must be delimited by period
        re_string += '([a-z]+)\.$'

        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        # preparing the message
        message_string = "which properties does " + object + " have in " +  basket + "'s basket only?"
        self.set_message(message_string)
        self.instructions_completed = False


    @on_output_message(r"\?$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        else:
            # does end of agent message match regexp?
            matches=self.re_query.match(event.message)
            # if it does, let's parse the parts of the match
            potential_properties=set()
            if (matches):
                for chunk in matches.groups():
                    # the delimiters all involve white space
                    if (not re.search(' ',chunk)):
                        potential_properties.add(chunk)
                if (self.distinctive_properties_set == potential_properties):
                    self.set_reward(1,random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        correct_properties=list(self.distinctive_properties_set)
        random.shuffle(correct_properties)
        self.set_message('the right properties are: ' + " ".join(correct_properties) + '.')


class ListThePropertiesThatAnObjectHasInAllBasketsTask(Task):
    def __init__(self, env):
        super(ListThePropertiesThatAnObjectHasInAllBasketsTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # we traverse the baskets recording and the objects,
        # recording, for each object, how many baskets it is in
        basket_count={}
        baskets=global_properties.keys()
        for basket in baskets:
            for object in global_properties[basket]:
                if (not object in basket_count):
                    basket_count[object]=1
                else:
                    basket_count[object]+=1

        # traversing the basket counts, keeping only those objects that occur in all baskets
        legit_objects = [object for object in basket_count if basket_count[object]==len(baskets)]
        # now we pick a random object from this list
        object = random.choice(legit_objects)
        # ... and we accumulate the objects it shares across baskets
        for i in range(len(baskets)):
            if (i==0):
                self.shared_properties_set=set(global_properties[baskets[i]][object])
            else:
                self.shared_properties_set=self.shared_properties_set.intersection(set(global_properties[baskets[i]][object]))
        # if set is empty, we put 'none' in it
        if (not self.shared_properties_set):
            self.shared_properties_set.add('none')

        # building the regexp query
        re_string = '.*?'
        # each property name but the last could be followed by:
        # ', ', ' and ', or ', and ' or ' '

        for i in range(len(self.shared_properties_set)-1):
            re_string += '([a-z]+)(, | and |, and | )'
        # final string must be delimited by period
        re_string += '([a-z]+)\.$'

        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        # preparing the message
        message_string = "which properties does " + object + " have in " + "all baskets?"
        self.set_message(message_string)
        self.instructions_completed = False


    @on_output_message(r"\?$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        else:
            # does end of agent message match regexp?
            matches=self.re_query.match(event.message)
            # if it does, let's parse the parts of the match
            potential_properties=set()
            if (matches):
                for chunk in matches.groups():
                    # the delimiters all involve white space
                    if (not re.search(' ',chunk)):
                        potential_properties.add(chunk)
                if (self.shared_properties_set == potential_properties):
                    self.set_reward(1,random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        correct_properties=list(self.shared_properties_set)
        random.shuffle(correct_properties)
        self.set_message('the right properties are: ' + " ".join(correct_properties) + '.')



class ItalianHowManyPropertiesDoesAnObjectHaveTask(Task):
    def __init__(self, env):
        super(ItalianHowManyPropertiesDoesAnObjectHaveTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        italian_object_translations = {'apple': 'mela',
                                       'asparagus': 'asparago',
                                       'avocado': 'avocado',
                                       'banana': 'banana',
                                       'beet': 'rapa',
                                       'carrot': 'carota',
                                       'cucumber': 'cetriolo',
                                       'onion': 'cipolla',
                                       'pear': 'pera',
                                       'pineapple': 'ananas',
                                       'potato': 'patata',
                                       'tomato': 'pomodoro',
                                       'mango': 'mango'}
        italian_numbers_in_words=['zero', 'uno', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove', 'dieci']

        basket = random.choice(global_properties.keys())
        object=random.choice(global_properties[basket].keys())
        # counting properties of selected object
        self.property_count= len(global_properties[basket][object])
        # translating the object
        object=italian_object_translations[object]
        # alphabetic conversion only supported up to ten
        if (self.property_count<=10):
            self.alphabetic_property_count=italian_numbers_in_words[self.property_count]
        else:
            self.alphabetic_property_count=''

        message_string = "quante proprieta' ha " + object + " nel cestino di " + basket + "?"
        self.set_message(message_string)
        self.instructions_completed = False

    @on_output_message(r"\?$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        elif (
                (event.message[-(len(str(self.property_count))+1):] == (str(self.property_count)+'.'))
                or
                (len(self.alphabetic_property_count)>0 and
                 (event.message[-(len(self.alphabetic_property_count)+1):] == (self.alphabetic_property_count+'.')))):
            italian_msg.congratulations=['ottimo lavoro.',
                                              'bravo.',
                                              'congratulazioni.',
                                              'giusto.',
                                              'corretto.']

            self.set_reward(1,random.choice(italian_msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        # randomly pick digit or string version
        formatted_count = str(self.property_count)
        # no choice if there is no alphabetic version, else flip a
        # coin to decide whether to return digit or string version
        if (len(self.alphabetic_property_count)>0 and
            random.randint(0,1)==1):
            formatted_count=self.alphabetic_property_count
        self.set_message("la risposta corretta e': " + formatted_count + ".")



class GuessTheNumberAskingQuestionsExplicitModelTask(Task):
    def __init__(self, env):
        super(GuessTheNumberAskingQuestionsExplicitModelTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # picking a random nuber of digits between 1 and 5
        self.digits = random.randint(1,5)
        # generating a random number with that number of digits
        self.target_number=str(random.randint(1,9)) # first value shouldn't be 0, although this doesn't really
                                                    # matter for our current purposes
        self.target_number+=''.join(["%s" % random.randint(0, 9) for i in range(1, self.digits)]) # this relies
                                                                  # on weird limit properties of Python's range

        # preparing a regexp to capture requests for help
        # we need to escape the periods and question marks in number_questions
        escaped_number_questions=[]
        for question in number_questions:
            escaped_number_questions.append(re.sub(r'([\.\?])',r'\\\1',question))
        self.re_query = re.compile(r".*(" + "|".join(escaped_number_questions) + ")$")


        # preparing the message
        message_string = "guess the " + str(self.digits) +"-digit number I am thinking of; you can ask me: " + random.choice(number_questions)
        self.set_message(message_string)
        self.instructions_completed = False

    @on_output_message(r"[\.\?]$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        elif self.re_query.match(event.message):
            self.set_message(self.target_number + '.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1,random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('if you asked: ' + random.choice(number_questions) + ', I would have said: '+ self.target_number + '.')


class GuessTheNumberAskingQuestionsTask(Task):
    def __init__(self, env):
        super(GuessTheNumberAskingQuestionsTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # picking a random nuber of digits between 1 and 5
        self.digits = random.randint(1,5)
        # generating a random number with that number of digits
        self.target_number=str(random.randint(1,9)) # first value shouldn't be 0, although this doesn't really
                                                    # matter for our current purposes
        self.target_number+=''.join(["%s" % random.randint(0, 9) for i in range(1, self.digits)]) # this relies
                                                                  # on weird limit properties of Python's range

        # preparing a regexp to capture requests for help
        # we need to escape the periods and question marks in number_questions
        escaped_number_questions=[]
        for question in number_questions:
            escaped_number_questions.append(re.sub(r'([\.\?])',r'\\\1',question))
        self.re_query = re.compile(r".*(" + "|".join(escaped_number_questions) + ")$")


        # preparing the message
        message_string = "guess the " + str(self.digits) +"-digit number I am thinking of; you can ask me for the number."
        self.set_message(message_string)
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        elif self.re_query.match(event.message):
            self.set_message(self.target_number + '.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1,random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('if you asked: ' + random.choice(number_questions) + ', I would have said: '+ self.target_number + '.')

class GuessTheNumberAskingForDigitsExplicitModelTask(Task):
    def __init__(self, env):
        super(GuessTheNumberAskingForDigitsExplicitModelTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):

        # we need to edit the number_questions list by replacing
        # "number" with "next digit"; we will keep two versions of the
        # resulting list: one with just the relevant string replaced,
        # and one with escaped .? for the regular expression
        self.digit_questions=[]
        escaped_digit_questions=[]
        for question in number_questions:
            digit_question=re.sub('number', 'next digit',question)
            self.digit_questions.append(digit_question)
            escaped_digit_questions.append(re.sub(r'([\.\?])',r'\\\1',digit_question))

        # picking a random nuber of digits between 1 and 5
        self.digits = random.randint(1,5)
        # generating a random number with that number of digits
        self.target_number=str(random.randint(1,9)) # first value shouldn't be 0, although this doesn't really
                                                    # matter for our current purposes
        self.target_number+=''.join(["%s" % random.randint(0, 9) for i in range(1, self.digits)]) # this relies
                                                                  # on weird limit properties of Python's range

        # preparing a regexp to capture requests for help
        self.re_query = re.compile(r".*(" + "|".join(escaped_digit_questions) + ")$")

        # also, we initialize a counter to keep track of the next digit
        self.next_digit=0

        # preparing the message
        message_string = "guess the " + str(self.digits) + "-digit number I am thinking of; you can ask me: " + random.choice(self.digit_questions)
        self.set_message(message_string)
        self.instructions_completed = False

    @on_output_message(r"[\.\?]$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        elif self.re_query.match(event.message):
            if (self.next_digit<self.digits):
                self.set_message(self.target_number[self.next_digit] + '.')
                self.next_digit+=1
            else:
                self.set_message('the number has only ' + str(self.digits) + ' digits.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1,random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        give_away_message = ''
        if (self.next_digit<(self.digits)):
            give_away_message += 'if you asked: ' + random.choice(self.digit_questions) + ', I would have said: ' + self.target_number[self.next_digit] + '. '
        give_away_message += 'the number is ' + self.target_number + '.'
        self.set_message(give_away_message)


class GuessTheNumberAskingForDigitsTask(Task):
    def __init__(self, env):
        super(GuessTheNumberAskingForDigitsTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):

        # we need to edit the number_questions list by replacing
        # "number" with "next digit"; we will keep two versions of the
        # resulting list: one with just the relevant string replaced,
        # and one with escaped .? for the regular expression
        self.digit_questions=[]
        escaped_digit_questions=[]
        for question in number_questions:
            digit_question=re.sub('number', 'next digit',question)
            self.digit_questions.append(digit_question)
            escaped_digit_questions.append(re.sub(r'([\.\?])',r'\\\1',digit_question))

        # picking a random nuber of digits between 1 and 5
        self.digits = random.randint(1,5)
        # generating a random number with that number of digits
        self.target_number=str(random.randint(1,9)) # first value shouldn't be 0, although this doesn't really
                                                    # matter for our current purposes
        self.target_number+=''.join(["%s" % random.randint(0, 9) for i in range(1, self.digits)]) # this relies
                                                                  # on weird limit properties of Python's range

        # preparing a regexp to capture requests for help
        self.re_query = re.compile(r".*(" + "|".join(escaped_digit_questions) + ")$")

        # also, we initialize a counter to keep track of the next digit
        self.next_digit=0

        # preparing the message
        message_string = "guess the " + str(self.digits) + "-digit number I am thinking of; you can ask me for the next digit."
        self.set_message(message_string)
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        elif self.re_query.match(event.message):
            if (self.next_digit<self.digits):
                self.set_message(self.target_number[self.next_digit] + '.')
                self.next_digit+=1
            else:
                self.set_message('the number has only ' + str(self.digits) + ' digits.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1,random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        give_away_message = ''
        if (self.next_digit<(self.digits)):
            give_away_message += 'if you asked: ' + random.choice(self.digit_questions) + ', I would have said: ' + self.target_number[self.next_digit] + '. '
        give_away_message += 'the number is ' + self.target_number + '.'
        self.set_message(give_away_message)

# OLD STUFF FROM HERE
# here, I define a global character-by-character association list that
# can be used by the tasks below that rely on the same association
# scheme (here and below, global means: accessible by all tasks in
# this file; local means: accessible within one task only)

# we select a subset of characters as primes, so we can also define
# tasks with disjoint primes from within and without this list
# the following global variable tells us the size of this subset:
global_prime_cardinality=5

alphabet_integers=list(range(0,26)) # weirdly, left value is
                                    # inclusive, right value is
                                    # exclusive
random.shuffle(alphabet_integers)
# conversion to tuple for compatibility with local tables, that HAVE to be tuples
global_primes=tuple(alphabet_integers[0:global_prime_cardinality]) # usual python weirdness
random.shuffle(alphabet_integers)
global_targets=tuple(alphabet_integers[0:global_prime_cardinality]) # usual python weirdness

# the following function returns instead matching primes and targets
# tuples, generating them each time it is called: it will be used by
# "local" tasks to generate their own mapping tables (note that
# objects returned are two TUPLES, as needed by the task classes):
def generate_local_prime_and_target_mappings(prime_cardinality):
    alphabet_integers=list(range(0,26)) # weirdly, left value is
    # inclusive, right value is
    # exclusive
    random.shuffle(alphabet_integers)
    primes=alphabet_integers[0:prime_cardinality] # usual
    #python silliness: this will range from 0 to
    #prime_cardinality-1
    primes=tuple(primes) # we must fix to tuple, or else class will break down
    random.shuffle(alphabet_integers)
    targets=alphabet_integers[0:prime_cardinality] # usual python weirdness
    targets=tuple(targets) # we must fix to tuple, or else class will break down
    # also deleting alphabet_integers
    del(alphabet_integers)
    return([primes,targets])

# the following function generates prime and target strings, according
# to the tables passed as arguments
def generate_prime_and_target(primes,targets,string_length,prime_cardinality):
    raw_prime = [random.randint(0, (prime_cardinality-1)) for i in
                 range(string_length)]
    prime = ''.join(chr(ord('a') + primes[x]) for x in raw_prime)
    target = ''.join(chr(ord('a') + targets[x]) for x in raw_prime)
    return([prime,target])


# TASKS START HERE

class RepeatCharacter(Task):
    def __init__(self, env):
        super(RepeatCharacter, self).__init__(
            env, max_time=500)

    @on_start()
    def give_instructions(self, event):
        self.prime = chr(ord('a') + random.randint(0, 25))
        self.prime += "."
        self.set_message(self.prime)
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-2:] == self.prime:
            self.set_reward(1)

class RepeatStringMax4(Task):
    def __init__(self, env):
        super(RepeatStringMax4, self).__init__(
            env, max_time=500)

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(1, 4)
        self.prime = ""
        for i in range(self.string_length):
            self.prime += chr(ord('a') + random.randint(0, 25))
        self.prime += "."
        self.set_message(self.prime)
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.prime):] == self.prime:
            self.set_reward(1)


class RepeatStringMin5Max10(Task):
    def __init__(self, env):
        super(RepeatStringMin5Max10, self).__init__(
            env, max_time=500)

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(5, 10)
        self.prime = ""
        for i in range(self.string_length):
            self.prime += chr(ord('a') + random.randint(0, 25))
        self.prime += "."
        self.set_message(self.prime)
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.prime):] == self.prime:
            self.set_reward(1)

class GlobalTwoAssociatedCharacters(Task):
    def __init__(self, env):
        super(GlobalTwoAssociatedCharacters, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("global primes: " + str(global_primes))
#        self.logger.debug("global targets: " + str(global_targets))

    @on_start()
    def give_instructions(self, event):
        self.prime,self.target=generate_prime_and_target(global_primes,global_targets,1,global_prime_cardinality)
        self.set_message(self.prime+self.target+".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-2:] == self.target + ".":
            self.set_reward(1)

class GlobalCharacterPrimeTarget(Task):
    def __init__(self, env):
        super(GlobalCharacterPrimeTarget, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("global primes: " + str(global_primes))
#        self.logger.debug("global targets: " + str(global_targets))

    @on_start()
    def give_instructions(self, event):
        self.prime,self.target=generate_prime_and_target(global_primes,global_targets,1,global_prime_cardinality)
        self.target += "."
        self.set_message(self.prime + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-2:] == self.target:
            self.set_reward(1)


class LocalCharacterPrimeTarget(Task):
    # get local primes and targets
    primes,targets=generate_local_prime_and_target_mappings(global_prime_cardinality)
    # note that we use the same number of distinct primes as in the global
    # table, but they are not constrained to be the same (nor to be
    #disjoint)

    def __init__(self, env):
        super(LocalCharacterPrimeTarget, self).__init__(
            env, max_time=500)
        # debug
        # self.logger=logging.getLogger(__name__)
        # self.logger.debug("local primes " + str(self.primes))
        # self.logger.debug("local targets " + str(self.targets))

    @on_start()
    def give_instructions(self, event):
        self.prime,self.target=generate_prime_and_target(self.primes,self.targets,1,global_prime_cardinality)
        self.target += "."
        self.set_message(self.prime + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-2:] == self.target:
            self.set_reward(1)

class GlobalTwoAssociatedDelimitedStringsMax4(Task):
    def __init__(self, env):
        super(GlobalTwoAssociatedDelimitedStringsMax4, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("global primes: " + str(global_primes))
#        self.logger.debug("global targets: " + str(global_targets))

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(1,4)
        self.prime,self.target=generate_prime_and_target(global_primes,global_targets,self.string_length,global_prime_cardinality)
        self.set_message(self.prime + '#' + self.target + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.target):] == self.target:
            self.set_reward(1)


class GlobalTwoAssociatedStringsMax4(Task):
    def __init__(self, env):
        super(GlobalTwoAssociatedStringsMax4, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("global primes: " + str(global_primes))
#        self.logger.debug("global targets: " + str(global_targets))

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(1, 4)
        self.prime,self.target=generate_prime_and_target(global_primes,global_targets,self.string_length,global_prime_cardinality)
        self.set_message(self.prime + self.target + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.target):] == self.target:
            self.set_reward(1)

class LocalTwoAssociatedDelimitedStringsMax4(Task):
    # for comments, see first Local task in this file
    # get local primes and targets
    primes,targets=generate_local_prime_and_target_mappings(global_prime_cardinality)

    def __init__(self, env):
        super(LocalTwoAssociatedDelimitedStringsMax4, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("local primes " + str(self.primes))
#        self.logger.debug("local targets " + str(self.targets))

    @on_start()
    def give_instructions(self, event):
        string_length = random.randint(1,4)
        self.prime,self.target=generate_prime_and_target(self.primes,self.targets,
                                                         self.string_length,global_prime_cardinality)
        self.set_message(self.prime + '#' + self.target + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.target):] == self.target:
            self.set_reward(1)


class LocalTwoAssociatedStringsMax4(Task):
    # for comments, see first Local task in this file
    # get local primes and targets
    primes,targets=generate_local_prime_and_target_mappings(global_prime_cardinality)

    def __init__(self, env):
        super(LocalTwoAssociatedStringsMax4, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("local primes " + str(self.primes))
#        self.logger.debug("local targets " + str(self.targets))

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(1, 4)
        self.prime,self.target=generate_prime_and_target(self.primes,self.targets,
                                                         self.string_length,global_prime_cardinality)
        self.set_message(self.prime + self.target + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.target):] == self.target:
            self.set_reward(1)


class GlobalStringPrimeTargetMax4(Task):
    def __init__(self, env):
        super(GlobalStringPrimeTargetMax4, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("global primes: " + str(global_primes))
#        self.logger.debug("global targets: " + str(global_targets))

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(1, 4)
        self.prime,self.target=generate_prime_and_target(global_primes,global_targets,self.string_length,global_prime_cardinality)
        self.target += "."
        self.set_message(self.prime + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.target):] == self.target:
            self.set_reward(1)

class LocalStringPrimeTargetMax4(Task):
    # for comments, see first Local task in this file
    # get local primes and targets
    primes,targets=generate_local_prime_and_target_mappings(global_prime_cardinality)

    def __init__(self, env):
        super(LocalStringPrimeTargetMax4, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("local primes " + str(self.primes))
#        self.logger.debug("local targets " + str(self.targets))

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(1, 4)
        self.prime,self.target=generate_prime_and_target(self.primes,self.targets,
                                                         self.string_length,global_prime_cardinality)
        self.target += "."
        self.set_message(self.prime + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.target):] == self.target:
            self.set_reward(1)


class GlobalStringPrimeTargetMin5Max10(Task):
    def __init__(self, env):
        super(GlobalStringPrimeTargetMin5Max10, self).__init__(
            env, max_time=500)
        # debug
#        self.logger=logging.getLogger(__name__)
#        self.logger.debug("global primes: " + str(global_primes))
#        self.logger.debug("global targets: " + str(global_targets))

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(5, 10)
        self.prime,self.target=generate_prime_and_target(global_primes,global_targets,self.string_length,global_prime_cardinality)
        self.target += "."
        self.set_message(self.prime + ".")
        self.instructions_completed = False

    @on_output_message(r"\.$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_character(self, event):
        if not self.instructions_completed:
            pass
        elif event.message[-len(self.target):] == self.target:
            self.set_reward(1)

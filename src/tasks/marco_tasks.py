from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import random
import re
import logging
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_init

# TRYING pull request
# global data structures to be called by multiple tasks

# properties of objects in two baskets, for memory tasks
# (please keep objects in alphabetical order for ease of debugging)
global_properties =  {'john' :
               {'apple':['green','sour','hard','cheap','healthy','juicy','local'],
                'banana':['yellow','sweet','soft','cheap','healthy','exotic','ripe'],
                'beet':['red','dirty','hard','old','cheap','sweet','healthy','local','large'],
                'carrot':['orange','hard','fresh','local','healthy','sweet','crunchy'],
                'cucumber':['green','fresh','juicy','local','cheap','healthy','frozen','crunchy'],
                'onion':['white','pungent','smelly','cheap','local','healthy'],
                'pear':['brown','sweet','dry','cheap','local','big'],
                'pineapple':['yellow','sweet','hard','exotic','brown','rough'],
                'potato':['yellow','old','cheap','hard','tasteless','dirty','bumpy',],
                'tomato':['red','soft','sour','juicy','local','cheap']},
               'mary' :
                {'apple':['red','sweet','hard','fresh','juicy','expensive','crunchy'],
                'asparagus':['white','soft','old','long','expensive','dirty'],
                'avocado':['green','ripe','exotic','expensive','large','healthy','smooth','buttery'],
                'banana':['yellow','tasteless','soft','sweet','old','exotic'],
                'carrot':['orange','hard','old','dirty','local','small','crunchy'],
                'cucumber':['green','fresh','hard','cheap','local','long'],
                'onion':['yellow','old','cheap','dry','local','large'],
                'mango':['red','green','yellow','juicy','sweet','expensive'],
                'pear':['green','tasteless','hard','local','cheap','big'],
                'pineapple':['yellow','sweet','dry','fresh','expensive','exotic']}
           }

# it's handy to have a reverse dictionary with the properties in the
# above lists as keys, and the objects as values
reverse_global_properties={}
for basket in global_properties:
    reverse_global_properties[basket]={}
    for object in global_properties[basket]:
        for property in global_properties[basket][object]:
            if property in reverse_global_properties[basket]:
                reverse_global_properties[basket][property].append(object)
            else:
                reverse_global_properties[basket][property]=[object]

# handy list with word transcriptions of the integers from 0 to 10
numbers_in_words=['zero','one','two','three','four','five','six','seven','eight','nine','ten']

# a list of congratulations messages to be issued when the learner solves a task
congratulations_messages=['good job.',
                          'bravo.',
                          'congratulations.',
                          'nice work.',
                          'correct.']

class AssociateObjectWithPropertyTask(Task):
    def __init__(self, env):
        super(AssociateObjectWithPropertyTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        basket = random.choice(global_properties.keys())
        object = random.choice(global_properties[basket].keys())
        self.property = random.choice(global_properties[basket][object])
        message_string = object + " in " + basket + "'s basket is " + self.property + ". how is " + object +"?"
        self.property += "."
        self.set_message(message_string)
        self.instructions_completed = False

    @on_output_message(r"\?$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        elif event.message[-len(self.property):] == self.property:
            self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('the right answer is: ' + self.property + '.')

class VerifyThatObjectHasPropertyTask(Task):
    def __init__(self, env):
        super(VerifyThatObjectHasPropertyTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        basket = random.choice(global_properties.keys())
        object = random.choice(global_properties[basket].keys())
        # extracting the set of properties (from both baskets) that the selected objects does NOT have
        all_properties=[]
        for temp_basket in global_properties:
            for temp_object in global_properties[temp_basket]:
                for temp_property in global_properties[temp_basket][temp_object]:
                    all_properties.append(temp_property)
        property_complement=list(set(all_properties)-set(global_properties[basket][object]))
        # picking one true property and one false one
        in_and_out_properties= [random.choice(global_properties[basket][object]),random.choice(property_complement)]
        # deciding if we'll ask about the true or false property
        self.coin_flip = random.randint(0,1)
        property = in_and_out_properties[self.coin_flip]
        message_string = "is " + object + " " + property + " in " + basket + "'s basket?"
        self.set_message(message_string)
        self.instructions_completed = False
        # debug
        # self.logger=logging.getLogger(__name__)
        # self.logger.debug("property complement: " + " ".join(property_complement))


    @on_output_message(r"\?$")
    def check_ending(self, event):
        self.instructions_completed = True

    @on_message()
    def check_response(self, event):
        if not self.instructions_completed:
            self.clear_input_channel()
        elif (self.coin_flip==1 and event.message[-3:] == "no.") or (self.coin_flip==0 and event.message[-4:] == "yes."):
            self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        if (self.coin_flip==1):
            right_answer="no"
        else:
            right_answer="yes"
        self.set_message('the right answer is: ' + right_answer + '.')


class ListPropertiesofAnObjectTask(Task):
    def __init__(self, env):
        super(ListPropertiesofAnObjectTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        basket = random.choice(global_properties.keys())
        object = random.choice(global_properties[basket].keys())
        # retrieving the properties of the selected object
        self.object_properties = set(global_properties[basket][object])

        # building the regexp query
        # GK: don't you need to prefix with r these things?
        re_string = '.*?'
        # each property name but the last could be followed by:
        # ', ', ' and ', or ', and ' or ' '
        for i in range(len(self.object_properties)-1):
            re_string += '([a-z]+)(, | and |, and | )'
        # final string must be delimited by period
        re_string += '([a-z]+)\.$'

        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        message_string = "which properties does " + object + " have in " + basket + "'s basket?"
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
                if (self.object_properties == potential_properties):
                    self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('the right answer is: ' + " ".join(object_properties) + '.')

class NameAPropertyOfAnObject(Task):
    def __init__(self, env):
        super(NameAPropertyOfAnObject, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        basket = random.choice(global_properties.keys())
        object = random.choice(global_properties[basket].keys())
        # retrieving the properties of the selected object
        self.object_properties = global_properties[basket][object]

        message_string = "can you tell me a property of " + object + " in " + basket + "'s basket?"
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
            # this could be made more efficient, but since we don't have
            # many properties current version should be OK
            # traverse properties list, and see if you find one that is
            # matching
            found_matching_property=False
            object_properties_index=0
            while ((not found_matching_property) and
                   (object_properties_index<len(self.object_properties))):
                current_property=self.object_properties[object_properties_index]
                # GK: I'm going to make a few helper functions for matching a string or a regexp
                #     against the message inside this function, so we don't need to do anymore this thing
                #     of having to count the number of characters you need to extract.
                if event.message[-(len(current_property)+1):] == (current_property + "."):
                    found_matching_property=True
                object_properties_index+=1
            # is match found, give reward
            if (found_matching_property):
                self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        # randomly picked right property
        self.set_message('one right answer is: ' + random.choice(self.object_properties) + '.')


class HowManyPropertiesDoesAnObjectHaveTask(Task):
    def __init__(self, env):
        super(HowManyPropertiesDoesAnObjectHaveTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        basket = random.choice(global_properties.keys())
        object=random.choice(global_properties[basket].keys())
        # counting properties of selected object
        self.property_count= len(global_properties[basket][object])
        # alphabetic conversion only supported up to ten
        if (self.property_count<=10):
            self.alphabetic_property_count=numbers_in_words[self.property_count]
        else:
            self.alphabetic_property_count=''

        message_string = "how many property does " + object + " have in " + basket + "'s basket?"
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
            self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        # randomly pick digit or string version
        formatted_count = str(self.property_count)
        # no choice if there is no alphabetic version, else flip a
        # coin to decide whether to return digit or string version
        if (len(self.alphabetic_property_count)>0 and
            random.randint(0,1)==1):
            formatted_count=self.alphabetic_property_count
        self.set_message('the right answer is: ' + formatted_count + '.')


# NEW FROM HERE
class ItalianHowManyPropertiesDoesAnObjectHaveTask(Task):
    def __init__(self, env):
        super(ItalianHowManyPropertiesDoesAnObjectHaveTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        italian_object_translations = {'apple':'mela',
                                       'asparagus':'asparago',
                                       'avocado':'avocado',
                                       'banana':'banana',
                                       'beet':'rapa',
                                       'carrot':'carota',
                                       'cucumber':'cetriolo',
                                       'onion':'cipolla',
                                       'pear':'pera',
                                       'pineapple':'ananas',
                                       'potato':'patata',
                                       'tomato':'pomodoro',
                                       'mango':'mango'}
        italian_numbers_in_words=['zero','uno','due','tre','quattro','cinque','sei','sette','otto','nove','dieci']

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
            italian_congratulations_messages=['ottimo lavoro.',
                                              'bravo.',
                                              'congratulazioni.',
                                              'giusto.',
                                              'corretto.']

            self.set_reward(1,random.choice(italian_congratulations_messages))

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


class ListObjectsWithACertainPropertyTask(Task):
    def __init__(self, env):
        super(ListObjectsWithACertainPropertyTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):

        basket = random.choice(reverse_global_properties.keys())
        property = random.choice(reverse_global_properties[basket].keys())
        # retrieving the objects that have this property
        self.objects = set(reverse_global_properties[basket][property])

        # building the regexp query
        re_string = '.*?'
        # each object name but the last could be followed by:
        # ', ', ' and ', or ', and ' or ' '
        for i in range(len(self.objects)-1):
            re_string += '([a-z]+)(, | and |, and | )'
        # final string must be delimited by period
        re_string += '([a-z]+)\.$'

        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        message_string = "which objects are " + property + " in " + basket + "'s basket?"
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
            potential_objects=set()
            if (matches):
                for chunk in matches.groups():
                    # the delimiters all involve white space
                    if (not re.search(' ',chunk)):
                        potential_objects.add(chunk)
                if (self.objects == potential_objects):
                    self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('the right answer is: ' + "".join(self.objects) + '.')


class NameAnObjectWithAProperty(Task):
    def __init__(self, env):
        super(NameAnObjectWithAProperty, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        basket = random.choice(reverse_global_properties.keys())
        property = random.choice(reverse_global_properties[basket].keys())
        # retrieving the objects that have the selected property
        self.objects = reverse_global_properties[basket][property]

        message_string = "can you tell me an object that is " + property + " in " + basket + "'s basket?"
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
            # this could be made more efficient, but since we don't have
            # many objects current version should be OK
            # traverse objects list, and see if you find one that is
            # matching
            found_matching_object=False
            objects_index=0
            while ((not found_matching_object) and
                   (objects_index<len(self.objects))):
                current_object=self.objects[objects_index]
                if event.message[-(len(current_object)+1):] == (current_object + "."):
                    found_matching_object=True
                objects_index+=1
            # is match found, give reward
            if (found_matching_object):
                self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        # randomly random right property
        self.set_message('one right answer is: ' + random.choice(self.objects) + '.')


class HowManyObjectsHaveACertainPropertyTask(Task):
    def __init__(self, env):
        super(HowManyObjectsHaveACertainPropertyTask, self).__init__(
            env, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # we will sample from the actual properties, plus a random
        # string representing a "property" that no object has
        basket = random.choice(reverse_global_properties.keys())
        basket_properties=reverse_global_properties[basket].keys()
        property_pick=random.randint(0,len(basket_properties))
        # if we picked the last integer, we will generate a fake property and answer should be 0
        if (property_pick==len(basket_properties)):
            property = ""
            for i in range(random.randint(1, 10)):
                property += chr(ord('a') + random.randint(0, 25))
            # make sure this is not, by chance, identical to a real property in the relevant
            # basket
            while (property in basket_properties):
                property = ""
                for i in range(random.randint(1, 10)):
                    property += chr(ord('a') + random.randint(0, 25))
            self.object_count=0
            self.alphabetic_object_count='zero'
        # if instead we picked an integer within the property range, let's retrieve the corresponding
        # objects and count them
        else:
            property = basket_properties[property_pick]
            self.object_count= len(reverse_global_properties[basket][property])
            # alphabetic conversion only supported up to ten
            if (self.object_count<=10):
                self.alphabetic_object_count=numbers_in_words[self.object_count]
            else:
                self.alphabetic_object_count=''

        message_string = "how many objects are " + property + " in " + basket + "'s basket?"
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
                (event.message[-(len(str(self.object_count))+1):] == (str(self.object_count)+'.'))
                or
                (len(self.alphabetic_object_count)>0 and
                 (event.message[-(len(self.alphabetic_object_count)+1):] == (self.alphabetic_object_count+'.')))):
            self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        # randomly pick digit or string version
        formatted_count = str(self.object_count)
        # no choice if there is no alphabetic version, else flip a coin
        if (len(self.alphabetic_object_count)>0 and
            random.randint(0,1)==1):
            formatted_count=self.alphabetic_object_count
        self.set_message('the right answer is: ' + formatted_count + '.')


class WhoHasACertainObjectWithACertainPropertyTask(Task):
    def __init__(self, env):
        super(WhoHasACertainObjectWithACertainPropertyTask, self).__init__(
            env, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        # we traverse the baskets building sets of all the objects and
        # properties they contain as well as dictionary of sets
        # recording the object+property pairs present in each basket
        objects_set=set()
        properties_set=set()
        object_property_combinations={}
        for basket in global_properties.keys():
            object_property_combinations[basket]=set()
            for object in global_properties[basket].keys():
                objects_set.add(object)
                for property in global_properties[basket][object]:
                    properties_set.add(property)
                    object_property_combinations[basket].add((object, property))
        # now we build a random object+property combination from the
        # sets of objects and properties in both baskets
        object = random.choice(list(objects_set))
        property = random.choice(list(properties_set))
        # we build a list of baskets that have the relevant object property combination
        self.basket_set=set()
        for basket in global_properties.keys():
            if ((object, property) in object_property_combinations[basket]):
                self.basket_set.add(basket)
        # at this point, if baskets list is empty we add "nobody" as
        # the only item in it
        if (not self.basket_set):
            self.basket_set.add('nobody')

        # building the regexp query
        re_string = '.*?'
        # each basket name but the last could be followed by:
        # ', ', ' and ', or ', and ' or ' '
        for i in range(len(self.basket_set)-1):
            re_string += '([a-z]+)(, | and |, and | )'
        # final string must be delimited by period
        re_string += '([a-z]+)\.$'

        # compiling into a proper regexp
        self.re_query = re.compile(re_string)

        # deciding if to use a or an as determiner
        determiner = "a"
        if (property[0] in 'aeiou'):
            determiner = "an"

        # preparing the message
        message_string = "who has " + determiner + " " + property + " " + object + " in the basket?"
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
            potential_baskets=set()
            if (matches):
                for chunk in matches.groups():
                    # the delimiters all involve white space
                    if (not re.search(' ',chunk)):
                        potential_baskets.add(chunk)
                if (self.basket_set == potential_baskets):
                    self.set_reward(1,random.choice(congratulations_messages))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('the right answer is: ' + " ".join(self.basket_set) + '.')


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

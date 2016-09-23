from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message
import tasks.competition.messages as msg
import random
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


class ItalianHowManyPropertiesDoesAnObjectHaveTask(Task):
    def __init__(self):
        super(ItalianHowManyPropertiesDoesAnObjectHaveTask, self).__init__(
            max_time=3000)

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
            self.ignore_last_char()
        elif (
                (event.message[-(len(str(self.property_count))+1):] == (str(self.property_count)+'.'))
                or
                (len(self.alphabetic_property_count)>0 and
                 (event.message[-(len(self.alphabetic_property_count)+1):] == (self.alphabetic_property_count+'.')))):
            italian_msg_congratulations=['ottimo lavoro.',
                                              'bravo.',
                                              'congratulazioni.',
                                              'giusto.',
                                              'corretto.']

            self.set_reward(1,random.choice(italian_msg_congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        # randomly pick digit or string version
        formatted_count = str(self.property_count)
        # no choice if there is no alphabetic version, else flip a
        # coin to decide whether to return digit or string version
        if (len(self.alphabetic_property_count)>0 and
                random.randint(0, 1) == 1):
            formatted_count=self.alphabetic_property_count
        self.set_message("la risposta corretta e': " + formatted_count + ".")



class GuessTheNumberAskingQuestionsExplicitModelTask(Task):
    def __init__(self, ):
        super(GuessTheNumberAskingQuestionsExplicitModelTask, self).__init__(
            max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # picking a random nuber of digits between 1 and 5
        self.digits = random.randint(1, 5)
        # generating a random number with that number of digits
        self.target_number=str(random.randint(1, 9)) # first value shouldn't be 0, although this doesn't really
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
            self.ignore_last_char()
        elif self.re_query.match(event.message):
            self.set_message(self.target_number + '.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('if you asked: ' + random.choice(number_questions) + ', I would have said: '+ self.target_number + '.')


class GuessTheNumberAskingQuestionsTask(Task):
    def __init__(self):
        super(GuessTheNumberAskingQuestionsTask, self).__init__(
            max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # picking a random nuber of digits between 1 and 5
        self.digits = random.randint(1, 5)
        # generating a random number with that number of digits
        self.target_number=str(random.randint(1, 9)) # first value shouldn't be 0, although this doesn't really
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
            self.ignore_last_char()
        elif self.re_query.match(event.message):
            self.set_message(self.target_number + '.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        self.set_message('if you asked: ' + random.choice(number_questions) + ', I would have said: '+ self.target_number + '.')

class GuessTheNumberAskingForDigitsExplicitModelTask(Task):
    def __init__(self):
        super(GuessTheNumberAskingForDigitsExplicitModelTask, self).__init__(
            max_time=3500)

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
            self.ignore_last_char()
        elif self.re_query.match(event.message):
            if (self.next_digit<self.digits):
                self.set_message(self.target_number[self.next_digit] + '.')
                self.next_digit+=1
            else:
                self.set_message('the number has only ' + str(self.digits) + ' digits.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self,event):
        give_away_message = ''
        if (self.next_digit<(self.digits)):
            give_away_message += 'if you asked: ' + random.choice(self.digit_questions) + ', I would have said: ' + self.target_number[self.next_digit] + '. '
        give_away_message += 'the number is ' + self.target_number + '.'
        self.set_message(give_away_message)


class GuessTheNumberAskingForDigitsTask(Task):
    def __init__(self):
        super(GuessTheNumberAskingForDigitsTask, self).__init__(
            max_time=3500)

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
            self.ignore_last_char()
        elif self.re_query.match(event.message):
            if (self.next_digit<self.digits):
                self.set_message(self.target_number[self.next_digit] + '.')
                self.next_digit+=1
            else:
                self.set_message('the number has only ' + str(self.digits) + ' digits.')
        elif event.message[-(self.digits+1):] == (self.target_number + '.'):
            self.set_reward(1, random.choice(msg.congratulations))

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
    raw_prime = [random.randint(0, (prime_cardinality - 1)) for i in
                 range(string_length)]
    prime = ''.join(chr(ord('a') + primes[x]) for x in raw_prime)
    target = ''.join(chr(ord('a') + targets[x]) for x in raw_prime)
    return([prime,target])


# TASKS START HERE

class RepeatCharacter(Task):
    def __init__(self):
        super(RepeatCharacter, self).__init__(
            max_time=500)

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
    def __init__(self):
        super(RepeatStringMax4, self).__init__(
            max_time=500)

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
    def __init__(self):
        super(RepeatStringMin5Max10, self).__init__(
            max_time=500)

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
    def __init__(self):
        super(GlobalTwoAssociatedCharacters, self).__init__(
            max_time=500)

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
    def __init__(self):
        super(GlobalCharacterPrimeTarget, self).__init__(
            max_time=500)

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

    def __init__(self):
        super(LocalCharacterPrimeTarget, self).__init__(
            max_time=500)
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
    def __init__(self):
        super(GlobalTwoAssociatedDelimitedStringsMax4, self).__init__(
            max_time=500)

    @on_start()
    def give_instructions(self, event):
        self.string_length = random.randint(1, 4)
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
    def __init__(self):
        super(GlobalTwoAssociatedStringsMax4, self).__init__(
            max_time=500)

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

    def __init__(self):
        super(LocalTwoAssociatedDelimitedStringsMax4, self).__init__(
            max_time=500)

    @on_start()
    def give_instructions(self, event):
        string_length = random.randint(1, 4)
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

    def __init__(self):
        super(LocalTwoAssociatedStringsMax4, self).__init__(
            max_time=500)

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
    def __init__(self):
        super(GlobalStringPrimeTargetMax4, self).__init__(
            max_time=500)

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

    def __init__(self):
        super(LocalStringPrimeTargetMax4, self).__init__(
            max_time=500)

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
            max_time=500)

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

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
import random

# a list of congratulations messages to be issued when the learner solves a task
congratulations = ['good job.',
                   'bravo.',
                   'congratulations.',
                   'nice work.',
                   'correct.']
# a list of congratulations messages to be issued when the learner fails a task
failed = ['wrong!',
          'wrong.',
          'you failed!',
          'incorrect.']

timeout = ['time is out!', 'sorry, time is out!', 'too bad, time out!']

# handy list with word transcriptions of the integers from 0 to 10
numbers_in_words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six',
                    'seven', 'eight', 'nine', 'ten']


def number_to_string(num):
    '''
    Returns a string version of a number, randomly picking between
    letters and numbers.
    '''
    return random.choice(number_to_strings(num))


def number_to_strings(num):
    '''
    Returns all the string versions of a number.
    '''
    ret = [str(num)]
    if num <= len(numbers_in_words):
        ret.append(numbers_in_words[num])
    return ret


def string_to_number(n):
    if n in numbers_in_words:
        return numbers_in_words.index(n)
    else:
        return int(n)

#
# simple grammatical functions
#


def indef_article(x):
    if x[0] in 'aeiou':
        return 'an ' + x
    else:
        return 'a ' + x


def pluralize(obj, c):
    if c == 1:
        return obj
    else:
        return obj + 's'


def lemmatize(word):
    # if the word ends with an s and it's the result of pluralization
    # remove the s:
    if word[-1] == 's' and pluralize(word[:-1], 2) == word:
        return word[:-1]
    else:
        return word

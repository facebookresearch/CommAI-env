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
import logging
import codecs
import string
import random
import re
import math


class IdentitySerializer:
    '''
    Skips the serialization and just returns the text as-is.
    '''
    def __init__(self):
        self.SILENCE_TOKEN = ' '
        self.logger = logging.getLogger(__name__)

    def to_binary(self, message):
        return message

    def to_text(self, data):
        return data

    def can_deserialize(self, data):
        return data


class ScramblingSerializerWrapper:
    '''
    This is wrapper for any serializer that, on top of the serialization step,
    scrambles the words so they are unintelligible to human readers.
    Note: the scrambling process has two steps: a forward (during to_binary)
    where a new word is assigned to each input token and a backward (during
    to_text) where the word is translated back to its original form.
    If a word that has not been generated during the forward pass is sent to
    the backward pass, this word is left unchanged. As a consequence, if the
    learner uses a word (e.g "apple") before it has been uttered by the
    environment, it will go through unchanged. If at any point, the environment
    starts using this word, it will get assigned a new scrambled string (e.g.
    "vsdsf"), and now "apple" that was going through unchanged before, it's
    being mapped to a new string.
    '''
    def __init__(self, serializer, readable=True):
        '''
        Args:
            serialzer: underlying serializer that will get the calls forwarded.
        '''
        # the underlying serializer
        self._serializer = serializer
        self.SILENCE_TOKEN = serializer.SILENCE_TOKEN
        # 'vowels' and 'consonants' (to be alternated if readable = true)
        self.readable = readable
        self.V = 'aeiouy'
        self.C = ''.join([i for i in string.ascii_lowercase if i not in self.V])
        # a mapping of real words to scrambled words an back
        self.word_mapping = {}
        self.inv_word_mapping = {}
        self.logger = logging.getLogger(__name__)

    def to_binary(self, message):
        self.logger.debug("Tokenizing message '{0}'".format(message))
        # get all the parts of the message without cutting the spaces out
        tokens = self.tokenize(message)
        self.logger.debug("Scrambling message '{0}'".format(tokens))
        # transform each of the pieces (if needed) and merge them together
        scrambled_message = ''.join(self.scramble(t) for t in tokens)
        self.logger.debug("Returning scrambled message '{0}'".format(
            scrambled_message))
        # pass it on to the real serializer
        return self._serializer.to_binary(scrambled_message)

    def to_text(self, data):
        # get the scrambled message back from the bits
        scrambled_message = self._serializer.to_text(data)
        # split into tokens, including spaces and punctuation marks
        self.logger.debug("Tokenizing {0}".format(scrambled_message))
        tokens = self.tokenize(scrambled_message)
        self.logger.debug("Unscrambling {0}".format(tokens))
        # unmask the words in it
        return ''.join(self.unscramble(t) for t in tokens)

    def can_deserialize(self, data):
        if not self._serializer.can_deserialize(data):
            return False
        # get the scrambled message back from the bits
        scrambled_message = self._serializer.to_text(data)
        # split into tokens, including spaces and punctuation marks
        tokens = self.tokenize(scrambled_message)
        # to deserialize we have to be at the end of a word.
        return tokens and tokens[-1][1] != 'WORD'

    def scramble(self, token):
        word, pos = token
        if pos == 'SILENCE' or pos == 'PUNCT':
            # if this is a space or a punctuation sign, don't do anything
            return word
        else:
            if word.lower() not in self.word_mapping:
                # if we don't have a pseudo-word already assigned
                # generate a new pseudo-word
                pseudo_word = self.gen_pseudo_word(len(word))
                self.word_mapping[word.lower()] = pseudo_word
                self.inv_word_mapping[pseudo_word] = word.lower()
            return self.capitalize(word, self.word_mapping[word.lower()])

    def capitalize(self, word, scrambled_word):
        if len(scrambled_word) == len(word):
            # if the two words have the same length, we preverve capitalization
            return ''.join(scrambled_word[i].upper()
                           if word[i] in string.ascii_uppercase
                           else scrambled_word[i] for i in range(len(word)))
        else:
            # just capitalize the first letter
            return (scrambled_word[0].upper()
                    if word[0] in string.ascii_uppercase
                    else scrambled_word[0]) + scrambled_word[1:]

    def unscramble(self, token):
        scrambled_word, pos = token
        if pos == 'SILENCE' or pos == 'PUNCT':
            # if this is a space or a punctuation sign, don't do anything
            return scrambled_word
        else:
            # say that we have apple -> qwerty
            # if the word is qwerty, we return apple
            if scrambled_word.lower() in self.inv_word_mapping:
                return self.capitalize(scrambled_word,
                                       self.inv_word_mapping[
                                           scrambled_word.lower()])
            # conversely, if the word is apple, we return qwerty
            # so we have a bijection between the scrambled and normal words
            elif scrambled_word.lower() in self.word_mapping:
                return self.capitalize(scrambled_word, self.word_mapping[
                    scrambled_word.lower()])
            else:
                # otherwise we just return the word as is
                return scrambled_word

    def gen_pseudo_word(self, L=None):
        if not L:
            L = random.randint(1, 8)
        # generate one word that we hadn't used before
        while True:
            if self.readable:
                # alternating between vowels and consonants, sampled with repl.
                _choice, _range = random.choice, range(int(math.ceil(L / 2)))
                v = [_choice(self.V) for i in _range]
                c = [_choice(self.C) for i in _range]
                zipped = zip(v, c) if random.getrandbits(1) else zip(c, v)
                pseudo_word = ''.join([a for b in zipped for a in b])[:L]
            else:
                pseudo_word = ''.join(random.sample(
                                      string.ascii_lowercase, L))
            if pseudo_word not in self.inv_word_mapping:
                return pseudo_word

    def tokenize(self, message):
        '''
        Simplified tokenizer that splits a message over spaces and punctuation.
        '''
        punct = ",.:;'\"?"
        silence_token = self._serializer.SILENCE_TOKEN
        tokenized_message = []
        tokens = re.split('(\W)', message)
        for t in tokens:
            if not t:
                # re.split can return empty strings between consecutive
                # separators: ignore them.
                continue
            # separate intial punctuation marks
            if t in punct:
                tokenized_message.append((t, 'PUNCT'))
            elif t == silence_token:
                tokenized_message.append((t, 'SILENCE'))
            else:
                tokenized_message.append((t, 'WORD'))
        return tokenized_message


class StandardSerializer:
    '''
    Transforms text into bits and back using UTF-8 format.
    '''
    def __init__(self):
        self.SILENCE_TOKEN = ' '
        self.SILENCE_ENCODING = u' '
        self.logger = logging.getLogger(__name__)

    def to_binary(self, message):
        '''
        Given a text message, returns a binary string (still represented as a
        character string).
        '''
        # All spaces are encoded as null bytes:
        message = message.replace(self.SILENCE_TOKEN, self.SILENCE_ENCODING)
        # handle unicode
        message = codecs.encode(message, 'utf-8')
        data = []
        for c in message:
            # get the numeric value of the character
            try: 
                c = ord(c)
            except TypeError:
                # already an int (Python 3)
                pass
            # convert to binary
            bin_c = bin(c)
            # remove the '0b' prefix
            bin_c = bin_c[2:]
            # pad with zeros
            bin_c = bin_c.zfill(8)
            data.append(bin_c)
        return ''.join(data)

    def to_text(self, data, strict=False):
        '''Transforms a binary string into text.

        Given a binary string, returns the UTF-8 encoded text. If the
        string cannot be deserialized, returns None. It can also try to
        recover from meaningless data by skipping a few bytes in the beginning.

        Args:
            data: the binary string to deserialze.
            strict: if False, the initial bytes can be skipped in order to
            find a valid character. This allows to recover from randomly
            produced bit strings.

        Returns: A string with containing the decoded text.
        '''
        # if we are not in strict mode, we can skip bytes to find a message
        for skip in range(int(len(data) / 8) if not strict else 1):
            try:
                # convert data to a byte-stream
                message = bytearray()
                sub_data = data[skip * 8:]
                for i in range(int(len(sub_data) / 8)):
                    b = sub_data[i * 8:(i + 1) * 8]
                    message.append(int(b, 2))
                message = codecs.decode(message, 'utf-8')
                message = message.replace(self.SILENCE_ENCODING,
                                          self.SILENCE_TOKEN)
                if skip > 0:
                    self.logger.debug("Skipping {0} bytes to find a valid "
                                     "unicode character".format(skip))

                return message
            except UnicodeDecodeError:
                pass

        return None

    def can_deserialize(self, data):
        if len(data) < 8:
            return False
        return self.to_text(data) is not None


class GeneralSerializer:
    '''
    Transforms text into bits and back using specified mapping.
    Expects an index to symbol mapping `i2s`.
    silence_idx is which index in mapping is silence, defaults to 0
    '''
    def __init__(self, i2s, silence_idx):
        self.SILENCE_TOKEN = ' '
        self.SILENCE_ENCODING = silence_idx if silence_idx is not None else 0

        self.i2s = i2s
        self.s2i = {}
        for k, v in self.i2s.items:
            self.s2i[v] = k

        self.L = math.ceil(math.log(len(self.i2s), 2))

        # pad end of dictionary with silence
        for k in range(len(self.i2s), math.pow(2, self.L)):
            self.i2s[k] = self.SILENCE_TOKEN

        assert i2s[self.SILENCE_ENCODING] == self.SILENCE_TOKEN, \
                                                'mapping conflict for silence'

        self.logger = logging.getLogger(__name__)

    def to_binary(self, message):
        '''
        Given a text message, returns a binary string (still represented as a
        character string).
        '''
        message = codecs.encode(message, 'ascii')

        data = []
        for c in message:
            c = self.s2i[c]
            bin_c = bin(c)[2:]
            bin_c = bin_c.zfill(self.L)
            data.append(bin_c)

        return ''.join(data)

    def to_text(self, data):
        '''Transforms a binary string into text.

        Given a binary string, returns the encoded text. If the
        string cannot be deserialized, returns None.

        Args:
            data: the binary string to deserialze.

        Returns: A string with containing the decoded text.
        '''
        buff = codecs.encode(data, 'ascii')
        text = u''
        while buff != "":
            idx = int(buff[:self.L], 2)
            text = text + self.i2s[idx]
            buff = buff[self.L:]
        return text

    def can_deserialize(self, data):
        if len(data) < self.L:
            return False
        return self.to_text(data) is not None


class ASCIISerializer:
    '''
    Transforms text into bits and back according to ASCII format.
    '''
    def __init__(self):
        i2s = {}
        for k in range(0, 255):
            i2s[k] = chr(k)

        return GeneralSerializer(i2s, ord(' '))

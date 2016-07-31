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
    '''
    def __init__(self, serializer):
        '''
        Args:
            serialzer: underlying serializer that will get the calls forwarded.
        '''
        # the underlying serializer
        self._serializer = serializer
        self.SILENCE_TOKEN = serializer.SILENCE_TOKEN
        # a mapping of real words to scrambled words an back
        self.word_mapping = {}
        self.inv_word_mapping = {}

    def to_binary(self, message):
        # get all the parts of the message without cutting the spaces out
        tokens = self.tokenize(message)
        # transform each of the pieces (if needed) and merge them together
        scrambled_message = ''.join(self.scramble(t) for t in tokens)
        # pass it on to the real serializer
        return self._serializer.to_binary(scrambled_message)

    def to_text(self, data):
        # get the scrambled message back from the bits
        scrambled_message = self._serializer.to_text(data)
        # split into tokens, including spaces and punctuation marks
        tokens = self.tokenize(scrambled_message)
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
            if word not in self.word_mapping:
                # if we don't have a pseudo-word already assigned
                # generate a new pseudo-word
                pseudo_word = self.gen_pseudo_word()
                self.word_mapping[word] = pseudo_word
                self.inv_word_mapping[pseudo_word] = word
            return self.word_mapping[word]

    def unscramble(self, token):
        scrambled_word, pos = token
        if pos == 'SILENCE' or pos == 'PUNCT':
            # if this is a space or a punctuation sign, don't do anything
            return scrambled_word
        else:
            # say that we have apple -> qwerty
            # if the word is qwerty, we return apple
            if scrambled_word in self.inv_word_mapping:
                return self.inv_word_mapping[scrambled_word]
            # conversely, if the word is apple, we return qwerty
            # so we have a bijection between the scrambled and normal words
            elif scrambled_word in self.word_mapping:
                return self.word_mapping[scrambled_word]
            else:
                # otherwise we just return the word as is
                return scrambled_word

    def gen_pseudo_word(self, word_len=None):
        if not word_len:
            word_len = random.randint(1, 8)
        while True:
            # generate one word that we hadn't used before
            pseudo_word = ''.join(random.sample(
                                  string.ascii_lowercase, word_len))
            if pseudo_word not in self.inv_word_mapping:
                return pseudo_word

    def tokenize(self, message):
        '''
        Simplified tokenizer that splits a message over spaces and punctuation.
        '''
        punct = ",.:;'\"?"
        silence_token = self._serializer.SILENCE_TOKEN
        tokenized_message = []
        # strip initial silences
        while message and message[0] == silence_token:
            tokenized_message.append((silence_token, 'SILENCE'))
            message = message[1:]
        tokens = message.split(silence_token)
        for t in tokens:
            # separate intial punctuation marks
            while t and t[0] in punct:
                tokenized_message.append((t[0], 'PUNCT'))
                t = t[1:]
            # add the word without any trailing punctuation marks
            word = t.rstrip(punct)
            if word:
                tokenized_message.append((word, 'WORD'))
            t = t[len(word):]
            # separate trailing punctuation marks
            while t and t[-1] in punct:
                tokenized_message.append((t[-1], 'PUNCT'))
                t = t[:-1]
            # add separating silence
            tokenized_message.append((silence_token, 'SILENCE'))
        # remove the last silence
        if tokenized_message:
            del(tokenized_message[-1])
        # strip final silences
        while message and message[-1] == silence_token:
            tokenized_message.append((silence_token, 'SILENCE'))
            message = message[:-1]
        return tokenized_message


class StandardSerializer:
    '''
    Transforms text into bits and back using UTF-8 format.
    '''
    def __init__(self):
        self.SILENCE_TOKEN = ' '
        self.SILENCE_ENCODING = '\0'
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
            # convert to binary
            bin_c = bin(ord(c))
            # remove the '0b' prefix
            bin_c = bin_c[2:]
            # pad with zeros
            bin_c = bin_c.zfill(8)
            data.append(bin_c)
        return ''.join(data)

    def to_text(self, data, strict=False):
        '''
        Given a binary string, returns the UTF-8 encoded text. If the
        string cannot be deserialized, returns None.
        Args:
            data: the binary string to deserialze.
            strict: if False, the initial bytes can be skipped in order to
                find a valid character. This allows to recover from randomly
                produced bit strings.
        '''
        # if we are not in strict mode, we can skip bytes to find a message
        for skip in range(int(len(data) / 8) if not strict else 1):
            try:
                message = str('')
                sub_data = data[skip * 8:]
                for i in range(int(len(sub_data) / 8)):
                    b = sub_data[i * 8:(i + 1) * 8]
                    message += chr(int(b, 2))
                message = codecs.decode(message, 'utf-8')
                message = message.replace(self.SILENCE_ENCODING,
                                          self.SILENCE_TOKEN)
                if skip > 0:
                    self.logger.warn("Skipping {0} bytes to find a valid "
                                     "unicode character".format(skip))

                return message
            except UnicodeDecodeError:
                pass

        return None

    def can_deserialize(self, data):
        if len(data) < 8:
            return False
        return self.to_text(data) is not None

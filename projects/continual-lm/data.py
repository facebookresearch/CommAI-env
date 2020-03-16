# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import torch
import sys
import numpy as np
import pathlib
import tqdm
import scipy.stats as stats
import random
import zlib
import itertools
from collections import defaultdict


def get_random_alternating_iterator(
        corpora, switch_frequency, nswitches, chunk_size, batch_size, cuda):
    sequence_iterators = []
    for corpus in corpora:
        switch_frequency_in_chunks = switch_frequency / chunk_size / batch_size
        batched_corpus = BatchedCorpus(corpus, batch_size)
        exponential_lengths_sequence_it = ExponentialLengthsSequenceIterator(
                corpus.name, batched_corpus, nswitches, switch_frequency_in_chunks,
                chunk_size)
        sequence_iterators.append(exponential_lengths_sequence_it)
    sequence_iterator = RandomAlternationIterator(sequence_iterators, cuda)
    return sequence_iterator


def safe_iterate_sequences(sequence_iterator, max_sequences=None, first_sequence=None):
    last_sequence_ending = defaultdict(lambda:None)
    for input_sequence, target_sequence in itertools.islice(
            sequence_iterator, first_sequence, max_sequences):
        domain_id = sequence_iterator.get_current_index()
        assert last_sequence_ending[domain_id] is None or (last_sequence_ending[domain_id] == input_sequence[0,:]).all()
        last_sequence_ending[domain_id] =  target_sequence[-1,:]
        yield input_sequence, target_sequence

def safe_iterate_chunks(input_sequence, target_sequence, chunk_size, batch_size):
        last_chunk_ending = None
        for input_chunk, target_chunk in zip(
                ChunkIterator(input_sequence, chunk_size),
                ChunkIterator(target_sequence, chunk_size)):
            assert input_chunk.size(0) == chunk_size, input_chunk.size(0)
            assert input_chunk.size(1) == batch_size, input_chunk.size(1)
            assert (input_chunk[1:,:] == target_chunk.view(input_chunk.shape)[:-1,:]).all()
            if last_chunk_ending is not None:
                assert (input_chunk[0,:] == last_chunk_ending).all()
            last_chunk_ending = target_chunk[-1,:]
            yield input_chunk, target_chunk


class Dictionary(object):
    def __init__(self):
        self.word2idx = {}
        self.idx2word = []

    def add_word(self, word):
        if word not in self.word2idx:
            self.idx2word.append(word)
            self.word2idx[word] = len(self.idx2word) - 1
        return self.word2idx[word]

    def __contains__(self, word):
        return word in self.word2idx

    def __len__(self):
        return len(self.idx2word)

    def __iter__(self):
        return iter(self.idx2word)

class MultiCorpora(object):
    def __init__(self, root_path, token_type):
        root_path = pathlib.Path(root_path)
        self.corpora_names = []
        self.corpora = {}
        assert list(root_path.glob('*.txt')), f"No corpus files in {root_path}"
        for i,corpus_path in enumerate(root_path.glob('*.txt')):
            corpus_name = corpus_path.stem
            self.corpora_names.append(corpus_name)
            self.corpora[corpus_name] = Corpus(corpus_path, token_type)
            self.vocabulary  = self.corpora[corpus_name].vocabulary

    def unified_vocabulary(self):
        vocabulary = Dictionary()
        for corpus_name, corpus in self.corpora.items():
            for w in corpus.vocabulary:
                vocabulary.add_word(w)
        return vocabulary

    def get_corpora_number(self):
        return len(self.corpora)

    def __len__(self):
        return sum(len(corpus) for corpus in self.corpora.values())

    def __iter__(self):
        return iter(self.corpora.values())

class Corpus(object):
    def __init__(self, path, token_type):
        self.path = path
        self.name = path.stem
        assert token_type in ['char', 'word']
        self.token_type = token_type
        self.vocabulary = self.read_vocabulary(path.parent / 'vocab', token_type)

    def __len__(self):
        return len(self.data)

    def get_data(self, ntokens=None):
        vocab_hash = zlib.adler32(''.join(self.vocabulary.idx2word).encode())
        cache_file = self.path.parent / 'cache' / (self.path.stem + f'_{ntokens if ntokens else "all"}_{vocab_hash}.cache')
        if cache_file.is_file():
            print(f'Loading corpus from cache at {cache_file}')
            self.data = torch.load(cache_file)
        else:
            self.data = self.tokenize(self.path, self.vocabulary, ntokens)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            torch.save(self.data, cache_file)
        return self.data

    def read_vocabulary(self, vocabulary_path, token_type):
        """Returns a Dictionary with the full vocabulary"""
        vocabulary_files = vocabulary_path.glob('*.vocab')
        #assert os.path.exists(path)
        vocabulary = Dictionary()
        for vocabulary_file in vocabulary_files:
            # Add words to the set
            with open(vocabulary_file, 'r') as f:
                for line in f:
                    vocabulary.add_word(line.strip())
        if token_type == 'char':
            vocabulary.add_word(' ')
            vocabulary.add_word('\t')
            vocabulary.add_word('\n')
        vocabulary.add_word('<unk>')
        return vocabulary

    def tokenize(self, path, vocabulary, tokens=None):
        """Tokenizes a text file."""
        assert os.path.exists(path)
        if not tokens:
            with open(path, 'r') as f:
                tot_tokens = 0
                nlines = 0
                for line in f:
                    if self.token_type == 'word':
                        words = line.split()
                    else:
                        words = list(line)
                    tot_tokens += len(words)
                    nlines += 1
            tokens = tot_tokens
        with open(path, 'r') as f:
            ids = torch.LongTensor(tokens)
            token = 0
            t = tqdm.tqdm(total=tokens, desc=f'Tokenizing {path.stem}')
            for line in f:
                if token == tokens:  # we already have all we wanted
                    break
                if self.token_type == 'word':
                    words = line.split()
                else:
                    words = list(line)
                for word in words:
                    if token == tokens:  # we already have all we wanted
                        break
                    if word not in vocabulary:
                        word="<unk>"
                    ids[token] = vocabulary.word2idx[word]
                    token += 1
                    t.update(n=1)
            t.close()
            assert token == tokens  # we didn't finish the file before getting all we wanted
        return ids

class BatchedCorpus(object):
    def __init__(self, corpus, batch_size):
        self.corpus = corpus
        self.batch_size = batch_size

    def get_data(self, data_size):
        data = self.corpus.get_data(data_size * self.batch_size)
        batched_data = data.view(self.batch_size, data_size)
        return batched_data.t().contiguous()


class SequenceIterator(object):
    def __init__(self, name, corpus, switching_points, chunk_size):
        self.name = name
        self.corpus = corpus
        self.switching_points = switching_points
        self.chunk_size = chunk_size
        total_data = sum(switching_points)
        self.corpus_data = corpus.get_data(int(total_data) * chunk_size + 1)

    def get_name(self):
        return self.name

    def __len__(self):
        return len(self.switching_points)

    def __iter__(self):
        self.switching_points_it = iter(self.switching_points)
        self.next_sequence_start = 0
        return self

    def __next__(self):
        start = self.next_sequence_start * self.chunk_size
        sequence_length = next(self.switching_points_it)
        end = start + sequence_length * self.chunk_size
        assert end <= len(self.corpus_data)
        self.next_sequence_start += sequence_length
        return self.corpus_data[start:end], self.corpus_data[start+1:end+1]

class ExponentialLengthsSequenceIterator(SequenceIterator):
    def __init__(self, name, corpus, nswitches, mean_chunks_until_switch, chunk_size):
        switching_points = self.get_switching_points(
                nswitches, mean_chunks_until_switch)
        super(ExponentialLengthsSequenceIterator, self).__init__(
                name, corpus, switching_points, chunk_size)

    def get_switching_points(self, nswitches, switch_frequency):
        b = 10*switch_frequency
        s = switch_frequency
        l = 0.1 * switch_frequency
        switches = np.rint(stats.truncexpon(b, scale=s, loc=l).rvs(int(nswitches)))
        switches = np.maximum(1, switches)
        return switches.astype(np.int)

class RandomAlternationIterator(object):
    def __init__(self, collections, cuda):
        self.collections = collections
        self.cuda = cuda

    def __len__(self):
        return sum(len(c) for c in self.collections)

    def __iter__(self):
        self.iterators  = [iter(collection) for collection in self.collections]
        self.order = self.get_random_order_with_no_consecutives([len(it) for it in self.iterators])
        self.current_iterator_index = None
        self.order_it = iter(self.order)
        return self

    def get_random_order_with_no_consecutives(self, iterator_lengths):
        order = sum([[i]*l for i,l in enumerate(iterator_lengths)], [])
        random.shuffle(order)
        i = 0
        while self._count_consecutives(order) > 0 and i < 1000:
            start, length = self._find_first_consecutive_subsequence(order)
            self._swap_with_random(order, start + length // 2)
            i += 1
        return order

    def _find_first_consecutive_subsequence(self, sequence):
        consecutive = False
        last_x = None
        consecutive_start = None
        for i, x in enumerate(sequence):
            if consecutive:
                if last_x != x:
                    consecutive_length = i - consecutive_start + 1
                    return consecutive_start, consecutive_length
            else:
                if last_x == x:
                    consecutive = True
                    consecutive_start = i - 1
            last_x = x
        assert consecutive
        consecutive_length = len(sequence) - consecutive_start
        return consecutive_start, consecutive_length

    def _count_consecutives(self, sequence):
        element_count_tuples = self._to_element_count_tuples(sequence)
        return sum(1 for (_, c) in element_count_tuples if c > 1)

    def _to_element_count_tuples(self, sequence):
        element_counts = []
        for x in sequence:
            if not element_counts or element_counts[-1][0] != x:
                element_counts.append((x,1))
            else:
                element_counts[-1] = (x, element_counts[-1][1] + 1)
        return element_counts

    def _swap_with_random(self, sequence, pos):
        ot = random.randint(0, len(sequence)-1)
        sequence[pos], sequence[ot] = sequence[ot], sequence[pos]


    def __next__(self):
        self.current_iterator_index = next(self.order_it)
        try:
            elem = next(self.iterators[self.current_iterator_index])
            if self.cuda:
                    elem = (el.cuda() for el in elem)
            return elem
        except StopIteration:
            assert False, f"{self.current_iterator_index} ran out of sequences"

    def get_current_index(self):
        return self.current_iterator_index

    def get_current_iterator(self):
        return self.iterators[self.current_iterator_index]

class ChunkIterator(object):
    def __init__(self, sequence, bptt):
        self.sequence = sequence
        self.bptt = bptt

    def __iter__(self):
        self.it = 0
        return self

    def __next__(self):
        start = self.it * self.bptt
        end = (self.it + 1) * self.bptt
        last = self.sequence.shape[0]
        if start < last:
            assert end <= last
            self.it += 1
            return self.sequence[start:end]
        raise StopIteration

def data_to_char(data):
    data = data.cpu().numpy()
    def to_char(x):
        return corpus.vocabulary.idx2word[x]
    char_data = np.vectorize(to_char)(data)
    return char_data

def char_to_string(char_data):
    strings = list(map("".join,char_data))
    return strings

def print_data(data, corpus):
    char_data = data_to_char(data.t())
    #print(char_data)
    strings = char_to_string(char_data)
    for s in itertools.islice(strings, 10):
        print(s)
        print()
    print('-'*20)


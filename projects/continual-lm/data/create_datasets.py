import wget
import tarfile
import os
import zipfile
import gzip
import shutil
import glob
from nltk.corpus.reader.bnc import BNCCorpusReader
from nltk.probability import FreqDist

news_url = 'http://www.statmt.org/wmt13/training-monolingual-news-2009.tgz'
europarl_url = 'http://www.statmt.org/wmt14/training-monolingual-europarl-v7/europarl-v7.en.gz'
wiki_url = 'https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-103-raw-v1.zip'
bnc_url = 'https://ota.bodleian.ox.ac.uk/repository/xmlui/bitstream/handle/20.500.12024/2554/2554.zip'

lang_list = ['fr', 'es', 'en', 'de', 'cs']

def filter_char_level(path, inp, out_path, out, start, finish):
    vocab = {}
    fin = open(path + inp, 'r')
    count = 0
    for line in fin:
        count += 1
        if count < start:
            continue
        if count > finish:
            break
        for el in line:
            if el not in vocab:
                vocab[el] = 0
            vocab[el] += 1
    #print(vocab)
    #print(len(vocab))
    fout = open(out_path + out + '.txt', 'w')
    fin = open(path + inp, 'r')
    count = 0
    for line in fin:
        count += 1
        if count < start:
            continue
        if count > finish:
            break
        good = 1
        for el in line:
            if vocab[el] < 100:
                good = 0
        if good == 1:
            fout.write(line)
    if not os.path.exists(out_path + 'vocab/'):
        os.mkdir(out_path + 'vocab/')
    fout2 = open(out_path + 'vocab/' + out + '.vocab', 'w')
    for el in vocab:
        if vocab[el] >= 100:
            fout2.write(el + '\n')

def filter_word_level(path, inp, out_path, out, start, finish):
    vocab = {}
    fin = open(path + inp, 'r')
    fout = open(out_path + out + '.txt', 'w')
    count = 0
    for line in fin:
        count += 1
        if count < start:
            continue
        if count > finish:
            break
        fout.write(line)
        els = line.split()
        for el in els:
            if el not in vocab:
                vocab[el] = 0
            vocab[el] += 1
    #print(vocab)
    #print(len(vocab))
    words = [i[0] for i in sorted(vocab.items(), key = lambda x:x[1], reverse = True)]
    words = words[:25000]
    #print(words[0])
    new_vocab = dict((k,1) for k in words)
    if not os.path.exists(out_path + 'vocab/'):
        os.mkdir(out_path + 'vocab/')
    fout2 = open(out_path + 'vocab/' + out + '.vocab', 'w')
    for el in new_vocab:
        fout2.write(el + '\n')
    fout2.write('<unk>\n')



def create_news_dataset():
    if not os.path.exists('news/'):
        os.mkdir('news/')
    wget.download(news_url, 'news/news.2009.tgz')
    tar = tarfile.open('news/news.2009.tgz', 'r')
    tar.extractall(path = 'news/')
    tar.close()
    for el in lang_list:
        path = 'news/training-monolingual/'
        file_name = 'news.2009.' + el + '.shuffled'
        num_lines = sum(1 for line in open(path + file_name))
        filter_char_level(path, file_name, 'news_dev/', 'news.dev.' + el, 0, num_lines // 2)
        filter_char_level(path, file_name, 'news_test/', 'news.test.' + el, num_lines // 2 + 1, num_lines)

def create_wiki_data():
    if not os.path.exists('domain/'):
        os.mkdir('domain/')
    wget.download(wiki_url, 'domain/wiki.zip')
    zip_file = zipfile.ZipFile('domain/wiki.zip', 'r')
    zip_file.extractall('domain/')
    path = 'domain/wikitext-103-raw/'
    file_name = 'wiki.train.raw'
    num_lines = sum(1 for line in open(path + file_name))
    filter_word_level(path, file_name, 'domain_dev/', 'wiki.dev', 0, num_lines // 2)
    filter_word_level(path, file_name, 'domain_test/', 'wiki.test', num_lines // 2 + 1, num_lines)

def create_europarl_data():
    if not os.path.exists('domain/'):
        os.mkdir('domain/')
    wget.download(europarl_url, 'domain/europarl.gz')
    gz_file = gzip.open('domain/europarl.gz', 'r')
    gz_content = gz_file.read()
    gz_content = gz_content.decode('utf-8')
    f_out = open('domain/europarl.raw', 'w+')
    f_out.write(gz_content)
    gz_file.close()
    f_out.close()
    path = 'domain/'
    file_name = 'europarl.raw'
    num_lines = sum(1 for line in open(path + file_name))
    filter_word_level(path, file_name, 'domain_dev/', 'europarl.dev', 0, num_lines // 2)
    filter_word_level(path, file_name, 'domain_test/', 'europarl.test', num_lines // 2 + 1, num_lines)

def create_bnc_data():
    if not os.path.exists('domain/'):
        os.mkdir('domain/')
    print("Please go to https://ota.bodleian.ox.ac.uk/repository/xmlui/handle/20.500.12024/2554")
    print("download, and save the BNC corpus file as {}".format(os.getcwd() + "/domain/bnc.zip"))
    #wget.download(bnc_url, 'domain/bnc.zip')
    input("Press ENTER when this is done to continue...")
    zip_file = zipfile.ZipFile('domain/bnc.zip', 'r')
    zip_file.extractall('domain/')
    bnc_reader = BNCCorpusReader(root="domain/download/Texts", fileids=r'[A-K]/\w*/\w*\.xml')
    sents = bnc_reader.sents()
    fout = open('domain/bnc.raw', 'w+')
    for sent in sents:
        fout.write(' '.join(sent) + '\n')
    fout.close()
    path = 'domain/'
    file_name = 'bnc.raw'
    num_lines = sum(1 for line in open(path + file_name))
    filter_word_level(path, file_name, 'domain_dev/', 'bnc.dev', 0, num_lines // 2)
    filter_word_level(path, file_name, 'domain_test/', 'bnc.test', num_lines // 2 + 1, num_lines)

def create_news_word():
    path = 'news/training-monolingual/'
    file_name = 'news.2009.en.shuffled'
    num_lines = sum(1 for line in open(path + file_name))
    filter_word_level(path, file_name, 'domain_dev/', 'news.dev', 0, num_lines // 2)
    filter_word_level(path, file_name, 'domain_test/', 'news.test', num_lines // 2 + 1, num_lines)

if __name__ == '__main__':
    if not os.path.exists('news_dev/'):
        os.mkdir('news_dev/')
    if not os.path.exists('domain_dev/'):
        os.mkdir('domain_dev/')
    if not os.path.exists('news_test/'):
        os.mkdir('news_test/')
    if not os.path.exists('domain_test/'):
        os.mkdir('domain_test/')
    create_news_dataset()
    create_wiki_data()
    create_europarl_data()
    create_bnc_data()
    create_news_word()

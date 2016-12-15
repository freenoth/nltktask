#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Some analisys of text files and store results in database.
"""

# py_ver    : [3.5.2]
# date      : [02.11.2016]
# author    : [Aleksey Yakovlev]
# email     : [nothscr@gmail.com]

import re
import time
import multiprocessing

from pathlib import Path
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize

import dbhelp
import ac


WORKDIR = 'text_files'

# extention for stop-words list
STOPWORDS = ['наш', 'нашему', 'нашей', 'нашем', 'нашим',
             'мм', 'см', 'км', 'mm', 'cm', 'km', 'руб', 'шт',
             'kb', 'mb', 'gb', 'tb', 'ghz', 'hz', 'тыс', 'mah',
             'мгц', 'ггц', 'гц', 'квт', 'kg', 'кг']


class PathErrors(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)


class Timer(object):
    """ Service class, needed to control running time. """
    def __init__(self):
        self.start_time = time.time()

    def __str__(self):
        current_time = time.time()
        return '{:.3f} sec'.format(current_time - self.start_time)


def get_files():
    """ Get all *.txt files as list from directory ~/text_files/

    :return: list of objects (type Path) that represent text files in work directory
    """
    current_path = Path() / WORKDIR

    # check directory exist
    if not current_path.exists() or not current_path.is_dir():
        error_text = 'Directory "{0}" does not exist!'.format(str(current_path))
        raise PathErrors(error_text)

    # collect all *.txt files in folder: ~/text_files/
    file_list = [x for x in current_path.glob('*.txt')]
    return file_list


def transform_bad_tokens(tokens):
    """ try to extract some good info from bad tokens

    :param tokens: list of bad tokens
    :return: list of not_so_bad_tokens
    """
    if not tokens:
        return []

    # 1st : remove all punctuation
    bad_text = re.sub(r'[_|\W]+', ' ', ' '.join(tokens))

    # 2nd : save a good alpha-tokens from result
    not_so_bad_tokens = [x for x in word_tokenize(bad_text) if (x.isalpha() and len(x) > 1)]

    # 3rd : save another tokens (with filter numbers and one-letters)
    # very_bad_tokens = [x for x in word_tokenize(bad_text) if (not x.isalpha()
    #                                                               and not x.isdigit())]
    #
    # filter dimensions like 100x100x100 etc..
    # filter different metrics like 100kg, 2year etc..
    # filter square like mm2 or km³
    # very_bad_tokens = [x for x in very_bad_tokens
    #                            if (not re.match(r'^\d+\D+$', x)
    #                                and not re.match(r'\d+[x|X|х|Х](\d+[x|X|х|Х])*\d+', x)
    #                                and not re.match(r""".*[mMмМ][23²³]$""", x))]

    # убираем из пула слов оставшиеся "мусорные" слова/опечатки/названия моделей/метрики/размеры и т.д.

    return not_so_bad_tokens


def get_nausea(word_tokens):
    """ Get academic "nausea" by tokens

    :param word_tokens: list of tokens
    :return: tuple of value of nausea, number of words, number of unique words
    """
    rus_stemmer = SnowballStemmer('russian')
    eng_stemmer = SnowballStemmer('english')

    words = [eng_stemmer.stem(rus_stemmer.stem(word)) for word in word_tokens]

    uniq_words = len(set(words))

    freq_words = [words.count(word) for word in set(words)]
    freq_words.sort()

    freq = sum(freq_words[-5:])

    a_nausea = freq / uniq_words
    return a_nausea, len(words), uniq_words


def textfile_worker(task_queue, answer_queue):
    """ A process-handler of textfiles. Get job from incoming queue and put result into outgoing queue.

    :param task_queue: a JoinableQueue that contain tasks (Path objects)
    :param answer_queue: a Queue to save results (contain dbhelp.TableRow objects)
    :return:
    """
    while not task_queue.empty():
        job = task_queue.get()

        # read text from file
        # this function allowed only from python 3.5 vers
        # text = job.read_text('utf-8')
        # for old versions
        f = open(str(job), 'r', -1, 'utf-8')
        text = f.read()
        f.close()
        text_len = len(text)

        # clear text, need only alphanumeric or punctuation symbols
        # punctuation symbols from string.punctuation list
        text = re.sub(r'[^\w!"#$%&\'()*+,-./:;<=>?@[\\\]^`{|}~]+', ' ', text)

        # save good tokens : an alphabetic words with length > 1
        tokens = [x for x in word_tokenize(text) if (x.isalpha() and len(x) > 1)]

        # save bad tokens for next handling
        # dont save numbers, we dont need them
        bad_tokens = [x for x in word_tokenize(text) if (not x.isdigit() and not x.isalpha())]

        # try to identify a not_very_bad tokens from bad
        bad_tokens = transform_bad_tokens(bad_tokens)
        tokens.extend(bad_tokens)
        bad_tokens.clear()

        # convert cheats
        police = ac.AntiCheater()
        tr_tokens = [police.check_word(word) for word in tokens]
        tokens = [x[0] for x in tr_tokens]

        text = ' '.join(tokens)
        tokens.clear()

        is_cheat = set([x[1] for x in tr_tokens])
        is_cheat = 1 if 1 in is_cheat or -1 in is_cheat else 0
        tr_tokens.clear()

        # prepare stop-words for filtering tokens
        stop_words = stopwords.words('russian')
        stop_words.extend(stopwords.words('english'))
        stop_words.extend(STOPWORDS)

        # get list of words with filtering stop-words
        text = text.lower()
        tokens = [x for x in word_tokenize(text) if (x not in stop_words)]

        nsea, nwords, nuwords = -1, -1, -1
        if tokens:
            nsea, nwords, nuwords = get_nausea(tokens)

        result = dbhelp.TableRow(job.name, nsea, is_cheat, text_len, nwords, nuwords)
        answer_queue.put(result)

        task_queue.task_done()

    return 0


def _main():
    timer = Timer()
    db = dbhelp.SQLite3Helper()

    # prepare tasks for subprocess
    jobs = get_files()
    jqueue = multiprocessing.JoinableQueue()
    for job in jobs:
        jqueue.put(job)

    aqueue = multiprocessing.Queue()

    # start subprocess
    workers = []
    for i in range(0, multiprocessing.cpu_count()):
        w = multiprocessing.Process(target=textfile_worker, args=(jqueue, aqueue))
        workers.append(w)
        w.start()

    jqueue.join()

    # put result into database
    while not aqueue.empty():
        answer = aqueue.get()
        db.store(answer)

    db.flush()
    print(timer)


if __name__ == '__main__':
    _main()

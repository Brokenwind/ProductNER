#!/usr/bin/python
#-*-coding:utf-8-*-

import sys
import time
import json
import logging
import logging.config

import numpy as np
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler

reload(sys)
sys.setdefaultencoding('utf8')

def param_check(words, tags, max_length):
    ''' 
       ret  0  : json解析出错
            1  : 参数不足
            2  : 解析正确
    '''
    wordList = []
    tagList  = []
    ret = 2

    try :
        wordTmp = json.loads(words)
        tagTmp  = json.loads(tags)

        if((len(wordTmp) == 0) or (len(wordTmp) != len(tagTmp))):
            ret = 1
            return ret, wordList, tagList
        try:
            wordTmp = map(lambda word: word.encode('utf8','ignore'), wordTmp)
            tagTmp  = map(lambda tag: tag.encode('utf8', 'ignore'), tagTmp)

        except UnicodeDecodeError:
            pass
        #去除'\t'并限制长度
        for i, info in enumerate(zip(wordTmp, tagTmp)):
            word, tag = info

            if(i < max_length and word != '\t'):
                wordList.append(word)
                tagList.append(tag) 
    except:
        ret = 0
   
    return ret, wordList, tagList


verb_set = set(["v","vi","vx"])

def if_short_pharse(words, tags):
    '''
    为了纠正词语ner判错的case
    检测短语，单独利用词库进行匹配
    '''
    ret = False

    #三个词以内，并且没有动词
    if(len(words) < 3):
        if_verb = False
        for tag in tags:
            if(tag in verb_set):
                if_verb = True
                break

        if(not if_verb):
            ret = True 
    return ret

def get_logger(filename):
    """Return a logger instance that writes in filename

    Args:
        filename: (string) path to log.txt

    Returns:
        logger: (instance of logger)

    """
    log_fmt   = '%(asctime)s:%(levelname)s: %(message)s'
    formatter = logging.Formatter(log_fmt)
    
    log_file_handler = TimedRotatingFileHandler(filename, "midnight", 1, 80) 
    log_file_handler.setFormatter(formatter)  
    log_file_handler.setLevel(logging.INFO)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(log_file_handler) 

    return logger


class Progbar(object):
    """Progbar class copied from keras (https://github.com/fchollet/keras/)

    Displays a progress bar.
    Small edit : added strict arg to update
    # Arguments
        target: Total number of steps expected.
        interval: Minimum visual progress update interval (in seconds).
    """

    def __init__(self, target, width=30, verbose=1):
        self.width = width
        self.target = target
        self.sum_values = {}
        self.unique_values = []
        self.start = time.time()
        self.total_width = 0
        self.seen_so_far = 0
        self.verbose = verbose

    def update(self, current, values=[], exact=[], strict=[]):
        """
        Updates the progress bar.
        # Arguments
            current: Index of current step.
            values: List of tuples (name, value_for_last_step).
                The progress bar will display averages for these values.
            exact: List of tuples (name, value_for_last_step).
                The progress bar will display these values directly.
        """

        for k, v in values:
            if k not in self.sum_values:
                self.sum_values[k] = [v * (current - self.seen_so_far),
                                      current - self.seen_so_far]
                self.unique_values.append(k)
            else:
                self.sum_values[k][0] += v * (current - self.seen_so_far)
                self.sum_values[k][1] += (current - self.seen_so_far)
        for k, v in exact:
            if k not in self.sum_values:
                self.unique_values.append(k)
            self.sum_values[k] = [v, 1]

        for k, v in strict:
            if k not in self.sum_values:
                self.unique_values.append(k)
            self.sum_values[k] = v

        self.seen_so_far = current

        now = time.time()
        if self.verbose == 1:
            prev_total_width = self.total_width
            sys.stdout.write("\b" * prev_total_width)
            sys.stdout.write("\r")

            numdigits = int(np.floor(np.log10(self.target))) + 1
            barstr = '%%%dd/%%%dd [' % (numdigits, numdigits)
            bar = barstr % (current, self.target)
            prog = float(current)/self.target
            prog_width = int(self.width*prog)
            if prog_width > 0:
                bar += ('='*(prog_width-1))
                if current < self.target:
                    bar += '>'
                else:
                    bar += '='
            bar += ('.'*(self.width-prog_width))
            bar += ']'
            sys.stdout.write(bar)
            self.total_width = len(bar)

            if current:
                time_per_unit = (now - self.start) / current
            else:
                time_per_unit = 0
            eta = time_per_unit*(self.target - current)
            info = ''
            if current < self.target:
                info += ' - ETA: %ds' % eta
            else:
                info += ' - %ds' % (now - self.start)
            for k in self.unique_values:
                if type(self.sum_values[k]) is list:
                    info += ' - %s: %.4f' % (k,
                        self.sum_values[k][0] / max(1, self.sum_values[k][1]))
                else:
                    info += ' - %s: %s' % (k, self.sum_values[k])

            self.total_width += len(info)
            if prev_total_width > self.total_width:
                info += ((prev_total_width-self.total_width) * " ")

            sys.stdout.write(info)
            sys.stdout.flush()

            if current >= self.target:
                sys.stdout.write("\n")

        if self.verbose == 2:
            if current >= self.target:
                info = '%ds' % (now - self.start)
                for k in self.unique_values:
                    info += ' - %s: %.4f' % (k,
                        self.sum_values[k][0] / max(1, self.sum_values[k][1]))
                sys.stdout.write(info + "\n")

    def add(self, n, values=[]):
        self.update(self.seen_so_far+n, values)



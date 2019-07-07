#!/usr/bin/python
#-*-coding:utf-8-*-

import os
import sys
import time
import datetime

sys.path.append("..")

from util.general_utils import get_logger
from util.data_utils import get_trimmed_glove_vectors, load_vocab, \
        get_processing_word


class Config():
    def __init__(self, log_name, load=True):
        """Initialize hyperparameters and load vocabs

        Args:
            load_embeddings: (bool) if True, load embeddings into
                np array, else None

        """
        # create instance of logger
        self.logger = get_logger(log_name)

        # load if requested (default)
        if load:
            self.load()


    def load(self):
        """Loads vocabulary, processing functions and embeddings

        Supposes that build_data.py has been run successfully and that
        the corresponding files have been created (vocab and trimmed GloVe
        vectors)

        """
        # 1. vocabulary
        self.vocab_words = load_vocab(self.filename_words)
        self.vocab_tags  = load_vocab(self.filename_tags)
        self.vocab_chars = load_vocab(self.filename_chars)

        self.nwords     = len(self.vocab_words)
        self.nchars     = len(self.vocab_chars)
        self.ntags      = len(self.vocab_tags)

        # 2. get processing functions that map str -> id
        self.processing_word = get_processing_word(self.vocab_words,
                self.vocab_chars, lowercase=True, chars=self.use_chars)
        self.processing_tag  = get_processing_word(self.vocab_tags,
                lowercase=False, allow_unk=False)

        # 3. get pre-trained embeddings
        self.embeddings = (get_trimmed_glove_vectors(self.filename_trimmed)
                if self.use_pretrained else None)

    # embeddings
    dim_word = 100
    dim_char = 100

    max_iter = None # if not None, max number of examples in Dataset
    
    # training
    train_embeddings = False
    nepochs          = 100
    dropout          = 0.8
    batch_size       = 128
    lr_method        = "adam"
    lr               = 0.001
    lr_decay         = 0.9
    clip             = -1 # if negative, no clipping
    nepoch_no_imprv  = 15

    # model hyperparameters
    hidden_size_char = 100 # lstm on chars
    hidden_size_lstm = 100 # lstm on word embeddings

    # NOTE: if both chars and crf, only 1.6x slower on GPU
    use_crf = True # if crf, training is 1.7x slower on CPU
    use_chars = True # if char embedding, training is 3.5x slower on CPU

    #句子最长的单词个数
    max_length = 50

    #配置文件地址
    base_dir = "../data"

    # general config
    dir_output = os.path.join(base_dir, "chosen_model")  
    dir_model  = os.path.join(dir_output, "model.weights/") 

    filename_glove   =  os.path.join(base_dir , "word_model") 
    filename_trimmed =  os.path.join(base_dir , "new_word_model.npz") 
    use_pretrained = True

    data_dir = os.path.join(base_dir , "data_config")

    # vocab (created from dataset with build_data.py)
    filename_words = os.path.join(data_dir , "words.txt") 
    filename_tags =  os.path.join(data_dir , "tags.txt") 
    filename_chars = os.path.join(data_dir , "chars.txt") 

    #erp 相关配置
    sql_dict =  {
        "centerWord"   : "select * from YX_KBQA_CENTERWORD where isValid = 1",
        "simWords"     : "select * from YX_KBQA_SIMWORDS",
        "propertyInfo" : "select * from YX_KBQA_PROPERTY_INFOS where isValid = 1 and wordType = 'VALUE'"
   } 

    erp_dir = os.path.join(base_dir, "erp") 
    
    #每隔1小时更新一次数据
    interval = 3600000





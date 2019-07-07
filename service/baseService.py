#!/usr/bin/python
#-*-coding:utf-8-*-

import re
import os
import sys
reload(sys)
sys.path.append("..")
sys.setdefaultencoding('utf8')

import time
import json
import traceback
import logging
import numpy as np
import tensorflow as tf

import tornado.web
import ConfigParser
import tornado.ioloop
from tornado.options import options, define

from bean.state import State
from bean.ner_result import NerResult

from constant import rule_config 
from constant.config import Config
from constant.model_id import ModelId

from util.data_utils import CoNLLDataset
from util.general_utils import param_check, if_short_pharse

from model.ner_model import NERModel

from manager.mysql_conn import MySQLConn
from manager.erp_manager import ErpManager


os.environ['CUDA_VISIBLE_DEVICES']='-1'


flags = tf.flags

FLAGS = flags.FLAGS

flags.DEFINE_integer(
    "port_number", None,
    "服务运行的端口号"
)


flags.DEFINE_string(
    "log_name", None,
    "服务运行产生log写入的文件"
)


class NERHandler(tornado.web.RequestHandler):
    
    def post(self):
        if_continue = True

        try:
            traceId = self.get_argument("traceId") 
            words   = self.get_argument('words')
            tags    = self.get_argument('tags')
        except Exception, e:
            if_continue = False
            config.logger.error("ner service param is not enough, {:s}".format(traceback.format_exc()))

        if(if_continue):
            nerResult = self.nerFind(traceId, words, tags)
        else:
            nerResult = NerResult()
            nerResult.setState(State.param_not_enough)

        out_dict = nerResult.__dict__
        self.write(out_dict)


    def ruleJudge(self, word, pred, tag):
        '''
        优先判断是否是停用的词性
        然后是不是停用词
        不是停用词时，利用配置文件进行判断
        '''
        if_stop_tag = erpManager.ifStopTag(tag)
        if(if_stop_tag):
            pred = ModelId.OTHER
        else:
            if_stop_erp = erpManager.ifStopErp(word, pred)
            
            if(if_stop_erp):
                pred = ModelId.OTHER

            else:
                if(pred == ModelId.OTHER):
                    pred = erpManager.recognizeErp(word)
        
        return pred


    def nerFind(self, traceId, words, tags):
        start = time.time()

        nerResult = NerResult()

        #参数检查
        ret, words, tags = param_check(words, tags, config.max_length)
        if(ret == 0): 
            nerResult.setState(State.param_error)
            config.logger.error("traceId : {:s}, error in convert {:s} ".format(traceId, words))
            return nerResult

        if(ret == 1):
            nerResult.setState(State.param_not_enough) 
            config.logger.error("traceId : {:s}, words {:s} params is not enough".format(traceId, words))
            return nerResult    
      
        entitySet    = set([])    
        attrNameSet  = set([])
        attrValueSet = set([])

        try:
            preds = [ModelId.OTHER for i in range(len(words))]

            #为了纠正词语ner出错的情况
            #对于词组,只利用词典进行匹配，不经过模型
            if_pharse = if_short_pharse(words, tags)

            if(not if_pharse):
                preds = model.predict(words)

            labels = preds

            for i, info in enumerate(zip(words, preds, tags)):
                word, pred, tag = info
    
                new_pred = self.ruleJudge(word, pred, tag)
                #log中标识来源
                if(new_pred != pred):
                    labels[i] = new_pred + "_"

                if(new_pred == ModelId.ENTITY):
                    entitySet.add(word)
 
                elif(new_pred == ModelId.ATTR_NAME):
                    attrNameSet.add(word)
                
                elif(new_pred == ModelId.ATTR_VALUE):
                    attrValueSet.add(word)
                         
            nerResult.setEntity(list(entitySet))
            nerResult.setAttrName(list(attrNameSet))
            nerResult.setAttrValue(list(attrValueSet))
            
            end = time.time()
            last = int(round((end - start) * 1000))

            config.logger.info("traceId : {:s}, words : {}, label : {}, cost : {} ms".format(traceId, " ".join(words), " ".join(labels), last))     

        except Exception, e:
            nerResult.state(State.interval_error) 
            config.logger.error("traceId : {:s}, error in get ner result, sen : {} , error info : {}".format(traceId, " ".join(words) , traceback.format_exc()))
        
        return nerResult


##健康测试接口
class HealthHandler(tornado.web.RequestHandler): 
    def get(self):
        out_dict = self.healthCheck()
        self.write(out_dict)
 
    def healthCheck(self):
        out_dict = {"code" : 200}

        try:
            words = ["健康", "测试"]
            preds = model.predict(words)

            if(not preds):
                out_dict["code"] = 404

        except Exception, e:
            out_dict["code"] = 404
            config.logger.error("----health test failed, {:s}----".format(traceback.format_exc()))

        return out_dict

def update_erp():
    '''
    定时加载数据库中的数据和配置文件
    进行更新
    '''
    start = time.time()

    try:
        mc = MySQLConn()

        centerWordsSql  = config.sql_dict["centerWord"] 
        centerWordsInfo = mc.iter_query_result(centerWordsSql)

        simWordsSql  = config.sql_dict["simWords"]
        simWordsInfo = mc.iter_query_result(simWordsSql)

        propertyInfoSql  = config.sql_dict["propertyInfo"]
        propertyInfoInfo = mc.iter_query_result(propertyInfoSql)

        erpManager.update_erp(centerWordsInfo, simWordsInfo, propertyInfoInfo, rule_config.stop_dict)

        end  = time.time()
        last = int(round((end - start) * 1000))

        config.logger.info("----connent mysql, update erp and stop dict, cost {} ms-----".format(last))

    except Exception, e:
        config.logger.error("error in update erp from db , {:s}".format(traceback.format_exc()))


def make_app():
    return tornado.web.Application([
        (r"/yanxuan-ner/ner",  NERHandler),
        (r"/yanxuan-ner/health", HealthHandler)
    ])

if __name__ == "__main__":

    #required parameters
    flags.mark_flag_as_required("port_number")
    flags.mark_flag_as_required("log_name")

    # create instance of config
    config = Config(FLAGS.log_name)

    #erp manager
    erpManager = ErpManager(config, rule_config.stop_dict)

    #build model
    model = NERModel(config)
    model.build()
    model.restore_session(config.dir_model)

    app = make_app()
    app.listen(FLAGS.port_number)
     
    tornado.ioloop.PeriodicCallback(update_erp, config.interval).start()  
    tornado.ioloop.IOLoop.instance().start()


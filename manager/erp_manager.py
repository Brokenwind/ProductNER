#!/usr/bin/python
#-*-coding:utf-8-*-

import os
import sys
sys.path.append("..")

import traceback
from constant.model_id import ModelId

class ErpManager(object):
    def __init__(self, config, stop_dict):
        self.config = config

        self.entitySet    = set([])
        self.attrNameSet  = set([])
        self.attrValueSet = set([])
        self.stopDict = stop_dict

        '''
        首次获取从文件读取，实体、属性名和属性词
        '''
        self.load_entity_from_file()
        self.load_attr_name_from_file()
        self.load_attr_value_from_file()
        
        self.config.logger.info("load finished, entity size :{:d}, attrName size :{:d}, attrValue size :{:d}".format(len(self.entitySet), len(self.attrNameSet), len(self.attrValueSet)))


    def load_entity_from_file(self):
        f = open(os.path.join(self.config.erp_dir, "init.entity"))
        lines = f.readlines()
        f.close()

        for line in lines:
            info = line.strip().split('\t')
            wordType  = info[0]
            
            if(wordType in set(["SPU", "SALE_CATE"])):
                keyword   = info[1]
                if(keyword != ""):
                    self.entitySet.add(keyword)
           
                if(len(info) == 4): 
                    sim_words = info[3].split(',')

                    for word in sim_words:
                        if(word != ""):
                            self.entitySet.add(word)


    def load_attr_name_from_file(self):
        f = open(os.path.join(self.config.erp_dir, "init.property_name"))
        lines = f.readlines()
        f.close()

        for line in lines:
            attr = line.strip().split('\t')[0]
            sim_words = line.strip().split('\t')[1].split(',')

            if(attr != ""):
                self.attrNameSet.add(attr)

            for word in sim_words:
                if(word != ""):
                    self.attrNameSet.add(word)

    def load_attr_value_from_file(self):
        f = open(os.path.join(self.config.erp_dir, "init.property_value"))
        lines = f.readlines()
        f.close()

        for line in lines:
            value = line.strip().split('\t')[1].split(',')

            for each in value:
                if(each != ""):
                    self.attrValueSet.add(each)


    def update_erp(self, centerWordsInfo, simWordsInfo, propertyInfoInfo, stop_dict):
        '''
        更新配置文件
        包括(1)从数据库中读取的新的erp信息,单个中文字符的不予以保留,只保留词语
            (2)新的停用词词典
        '''
        new_entity = set([])
        new_attr_name  = set([])
        new_attr_value = set([])

        entity_id_set = set([])
        attr_id_set   = set([])
         
        for r in centerWordsInfo:
            try :
                Id = r[0]
                originWord = r[1]

                if(len(originWord) > 1):
                    centerWord = originWord.encode("utf8","ignore")
                    wordType   = r[2].encode("utf8","ignore")

                    if(wordType  == "ENTITY"):
                        entity_id_set.add(Id)
                        new_entity.add(centerWord)
                    elif(wordType == "PRO_NAME"):
                        attr_id_set.add(Id)
                        new_attr_name.add(centerWord)
            except Exception, e:
                self.config.logger.error("centerWordsInfo update failed , {:s}".format(traceback.format_exc()))
                continue

        for r in simWordsInfo:
            try:
                Id = r[1]
                simWord = r[2]
                
                if(len(simWord) > 1):
                    simWord = simWord.encode('utf8', "ignore")

                    if(Id in entity_id_set):    
                        new_entity.add(simWord)
                    elif(Id in attr_id_set):
                        new_attr_name.add(simWord)
            except Exception, e:
                self.config.logger.error("simWordsInfo update failed , {:s}".format(traceback.format_exc()))
                continue
            
        for r in propertyInfoInfo:
            try :
                Id = r[1]
                word = r[2]
                if(Id in attr_id_set and len(word) > 1):
                    word = word.encode("utf8","ignore")
                    new_attr_value.add(word)
            except Exception, e:
                self.config.logger.error("propertyInfoInfo update failed , {:s}".format(traceback.format_exc()))
                continue

        self.stopDict     = stop_dict
        self.entitySet    = new_entity
        self.attrNameSet  = new_attr_name
        self.attrValueSet = new_attr_value

        self.config.logger.info("update finished, entity size :{:d}, attrName size :{:d}, attrValue size :{:d}".format(len(new_entity), len(new_attr_name), len(new_attr_value)))

    
    def recognizeErp(self, word):
        '''
        识别实体词
        '''
        out = ModelId.OTHER

        if(word in self.entitySet):
            out = ModelId.ENTITY
        elif(word in self.attrNameSet):
            out = ModelId.ATTR_NAME
        elif(word in self.attrValueSet):
            out = ModelId.ATTR_VALUE


        return out

    def ifStopErp(self, word, pred):
        '''
        模型实体词的停用词判别
        '''
        ret = False

        if(word in self.stopDict[ModelId.TOTAL]):
            ret = True

        else:
            stop_set = self.stopDict.get(pred, [])

            if(word in stop_set):
                ret = True

        return ret
        
    def ifStopTag(self, tag):
        '''
        部分词性的词，强制不被识别为erp
        人名 地名 动词 
        '''
        ret = False

        if(tag in self.stopDict.get("tags", [])):
            ret = True


        return ret






        




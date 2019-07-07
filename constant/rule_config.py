#!/usr/bin/python
#-*-coding:utf-8-*-

from model_id import ModelId


stop_dict =  { 
    ModelId.TOTAL   : set(["ORDER_NUM", "URL", "条件", "山", "讲故事", "其他", "积分", "混球", "卧槽", "嚯", "沙雕", "二奶", "赠品"]) ,
    ModelId.ENTITY  : set([])  ,
    ModelId.ATTR_NAME   : set([]) , 
    ModelId.ATTR_VALUE  : set([]) ,
    #停用词性 人名 地名 动词 数词
    "tags" : set(["nr", "nrf", "nrj", "nr1", "nr2", "ns", "nsf", "v", "m"]) 
}

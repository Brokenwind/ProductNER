#!/usr/bin/python
#-*-coding:utf-8-*-


from state import State

class NerResult(object):

    def __init__(self):
        self.entity    = [] 
        self.attrName  = [] 
        self.attrValue = [] 
        self.state = State.success


    def setEntity(self, entity):
        self.entity = entity


    def setAttrName(self, attrName):
        self.attrName = attrName


    def setAttrValue(self, attrValue):
        self.attrValue = attrValue


    def setState(self, state):
        self.state = state

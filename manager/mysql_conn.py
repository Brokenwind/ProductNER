#!/usr/bin/python
#-*-coding:utf-8-*-

import MySQLdb


class MySQLConn(object):
    def __init__(self , host = "10.200.175.25", user = "yx_kbqa", passwd = "yx_kbqa",  db = "yx_kbqa", port = 6306):
        self.conn = MySQLdb.connect(host, user, passwd, db, port = port, charset='utf8')
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.conn.close()

    def iter_query_result(self, query):
        self.cursor.execute(query)
        row = self.cursor.fetchone()
        while row:
            yield row 
            row = self.cursor.fetchone()



if __name__ == '__main__':
    mc = MySQLConn()

    centerWordsSql = "select * from YX_KBQA_CENTERWORD where isValid = 1" 

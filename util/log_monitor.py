#!/usr/bin/python
#-*-coding:utf-8-*-
#
#收集日志信息
#昨天的分片的日志信息
#按照时间顺序进行组合成单一的log信息
#并删除分片的log信息
#监测每天日志中的错误和超时的log信息
#存储在log文件夹下的monitor_info 目录下
#写入crontab -e 中，定时任务
#

import os
import re
import time
import datetime
import traceback
import tensorflow as tf

flags = tf.flags
FLAGS = flags.FLAGS

flags.DEFINE_string(
    "log_dir", None,
    "存放log文件的目录"
)


flags.DEFINE_string(
    "time_pattern", None,
    "识别每一个响应输出的log"
)


flags.DEFINE_integer(
    "time_out", 3000,
    "响应超时的时间,ms"
)


class LoadCorpus(object): 
    '''
    使用迭代器读取语料库
    '''
    def __init__(self, path):
        self.path = path
 
    def __iter__(self):
        for line in open(self.path):
            yield line.strip()


def getDateBefore(date_diff):
    '''
    获取date_diff前的日期
    获取昨天的日期 date_diff = 1 : 2018-11-15
    '''
    today=datetime.date.today()
    daydiff=datetime.timedelta(days=date_diff)
    beforeday =today-daydiff
    return str(beforeday)



def calculateDateDiff(start_date, end_date):
    '''
    计算两个日期的间隔
    '''
    start_sec = time.mktime(time.strptime(start_date,'%Y-%m-%d'))
    end_sec = time.mktime(time.strptime(end_date,'%Y-%m-%d'))
    work_days = int((end_sec - start_sec)/(24*60*60))

    return work_days


def isValidDate(date):
  '''
  判断是否是一个有效的日期字符串
  '''
  try:
    time.strptime(date, "%Y-%m-%d")
    return True
  except:
    return False


def isStartWithTime(item):
    '''
    判断一句话是否是日期开头
    '''
    ret = False

    part = item.split(" ")    
    if(len(part) == 0):
        return ret
    
    date = part[0]
    ret = isValidDate(date)
     
    return ret


def makeDir(dir_path, error_name):
    '''
    路径不存在时，新建文件夹
    限制文件夹下的文件个数
    最多存储100个，删除100天之前的信息
    '''
    if(not os.path.exists(dir_path)):
        os.mkdir(dir_path)

    today = getDateBefore(0)
    for name in os.listdir(dir_path):
        file_time = name.split(".")[-1]
        day_diff = calculateDateDiff(file_time, today)
        if(day_diff >= 100):
            path = os.path.join(dir_path, name)
            os.remove(path)


def getLogContent(log_path):
    '''
    读取每个log文件里面的log信息
    如果不是以时间开头的log
    拼接到上一条log上去
    '''
    log_list = []

    first_log = ""

    log_corpus = LoadCorpus(log_path) 

    for item in log_corpus:
        if(item == ""):
            continue

        if_match = isStartWithTime(item)

        if(if_match):
            #第一条包含时间信息的log,获取当前日志时间, 贴到第一条log上面去
            if(first_log):
                time = line[:23]
                first_log = time + ':' + first_log + "\n" + item
                log_list.append(first_log)
                first_log = ""         
            else:
                log_list.append(item)
        else:
            #存在上一个log信息,进行拼接
            if(len(log_list) > 0):
                last_log = log_list.pop()
                last_log = last_log + "\n" + item
                log_list.append(last_log)
            #不存在上一个log信息,向之后的第一条log合并 
            else:
               first_log = first_log.strip() + "\n" + item

    return log_list


def mergeLog(log_dir):
     #获取昨天的日期
    yday_str = getDateBefore(1)

    log_name = "main.log." + yday_str

    #获取昨天的log文件
    yday_log = filter(lambda item: item.endswith(yday_str) and item != log_name, os.listdir(log_dir))

    #获取所有log信息
    total_log = [] 
    for log_file in yday_log:
        log_path = os.path.join(log_dir, log_file)
        log_content = getLogContent(log_path)
        total_log.extend(log_content)

        #删除多余的log文件
        os.remove(log_path)
    
    if(len(total_log) > 0):        
        #按照时间排序,并进行存储
        sorted_log = sorted(total_log)
            
        g = open(os.path.join(log_dir, log_name), "w")

        for log_info in sorted_log:
            g.writelines(log_info + '\n')

        g.close()



def generatePattren(pattern):
    regex = ""

    try:
        part_list = pattern.split("|")

        pattern_list = map(lambda part : "(" + "|".join(part.split(",")) + ")" , part_list)

        pattern_str = "\\d+.?\\d*".join(pattern_list)
        regex = re.compile(pattern_str)
    except Exception, e:
        print(pattern, traceback.format_exc())
        
    return regex


def detectReponse(log, time_regex):
    '''
    检测是否是响应的log，响应的log返回响应时长 
    是否是报错的log
    '''
    if_log   = False
    if_error = False
    time = 0

    try:
        tmp = time_regex.search(log)

        if(tmp):
            if_log = True
            time   = float(re.search(r"\d+.?\d*", tmp.group()).group())
    
        if("ERROR" in log):
            if_error = True

    except Exception, e:
        print(log, traceback.format_exc())

    return if_log, if_error, time


def calculateTarget(time_list, error_list, time_limit):
    '''
    参数指标
    响应的请求数
    超时的请求数
    平均响应时长
    最大响应时长
    超时的占比
    '''
    
    log_count = len(time_list)

    max_time = 0
    avg_time = 0
    exceed_count = 0
    exceed_ratio = 0.0 

    if(log_count > 0):
        max_time = max(time_list)
        avg_time = sum(time_list) * 1.0 / log_count
        exceed_count = len(filter(lambda item : item > time_limit, time_list))
        exceed_ratio = exceed_count * 1.0 / log_count

    out = "response count : {:d},  exceed count : {:d}, error count : {:d}, avg time : {:f}, max time : {:f}, exceed ratio : {:f}".format(log_count, exceed_count, len(error_list), avg_time, max_time, exceed_ratio)

    return out


def logMonitor(log_dir, pattern, time_limit):
    yday_str = getDateBefore(1)
    log_name = "main.log." + yday_str
    log_path = os.path.join(log_dir, log_name)

    #监测输出的目录
    error_name =  "error.log."
    monitor_dir = os.path.join(log_dir, "monitor")
    makeDir(monitor_dir, error_name)
    monitor_path = os.path.join(monitor_dir, error_name + yday_str)

    time_regex = generatePattren(pattern)
    log_content = LoadCorpus(log_path)
    g = open(monitor_path, "w")

    time_list  = []
    error_list = []

    #记录响应的信息
    for log in log_content:
        is_log, is_error, time = detectReponse(log, time_regex)

        if(is_log):
            time_list.append(time)
            if(time > time_limit):
                g.writelines(log + "\n")

        if(is_error):
            error_list.append(log)

    #记录error信息
    if(len(error_list) > 0):
        g.writelines("\n-------error response-------\n")
        for error in error_list:
            g.writelines(error + '\n')
        g.writelines("\n\n")

    targets = calculateTarget(time_list, error_list, time_limit)

    g.writelines(targets + '\n')
    g.close()


def main():
    flags.mark_flag_as_required("log_dir")
    log_dir = FLAGS.log_dir

    flags.mark_flag_as_required("time_pattern")
    time_pattern = FLAGS.time_pattern

    flags.mark_flag_as_required("time_out")
    time_out = FLAGS.time_out

    #每天对分片的log信息合并
    mergeLog(log_dir)

    #监测错误和超时的日志
    logMonitor(log_dir, time_pattern, time_out)


if __name__ == "__main__":
    main()



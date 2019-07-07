智能客服NER线上服务


修改 start.sh 中的
进程数process_count
log存放的文件夹
起始的端口号
运行sh start.sh即可

sh stop.sh

collect_log.py
收集日志信息
昨天的分片的日志信息
按照时间顺序进行组合成单一的log信息
并删除分片的log信息


log.sh 执行collecy_log.py
写入crontab -e 中，定时任务
注意修改环境变量 和 log地址 

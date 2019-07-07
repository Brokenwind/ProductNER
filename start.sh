#!/bin/bash

#####
#python 环境下实现并行
#开多个进程，绑定不同的端口
#指定不同的log输出文件，为了解决log进程不安全的问题
#####

#进到service 目录
cd service

#杀死原有的nerService进程
#grep -v grep : 列出的进程中去除含有关键字“grep”的进程。
#cut -c 9-15  : 截取进程号PID
#xargs 传参杀死进程
ps -aux | grep nerService | grep -v grep |cut -c 9-15 |xargs kill -s 9

#开启的进程数
process_count=1

#起始端口号
port=8080

#存放log的目录,注意最后的"/"
log_dir="/home/webedit/hzjizhiwei/yx_ner/data/log/"

end=`expr ${process_count} - 1`

for k in $(seq 0 ${end})
do
    #copy service代码
    cp baseService.py nerService${k}.py 
    
    #各自的log名称
    log_name=${log_dir}main${k}.log

    #各自的端口号 
    port_number=`expr ${port} + ${k}`

    #运行各个不同的service代码，实现多进程
    nohup /home/python/bin/python2.7 -u nerService${k}.py \
        --log_name=$log_name \
        --port_number=$port_number \
        > /dev/null 2>&1 &

done


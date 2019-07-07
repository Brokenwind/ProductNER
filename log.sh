#!/bin/bash

#环境变量,否则定时任务不生效
source /home/webedit/.bashrc

cd util

#执行收集log的脚本
nohup python log_monitor.py \
  --log_dir=/home/webedit/hzjizhiwei/yx_ner/data/log \
  --time_pattern="cost : | ms" \
  --time_out=10 \ 
  > /dev/null 2>&1


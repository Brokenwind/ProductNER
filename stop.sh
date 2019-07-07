#杀死原有的nerService进程
#grep -v grep : 列出的进程中去除含有关键字“grep”的进程。
#cut -c 9-15  : 截取进程号PID
#xargs 传参杀死进程
ps -aux | grep nerService | grep -v grep |cut -c 9-15 |xargs kill -s 9


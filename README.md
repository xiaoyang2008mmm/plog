# plog
Python写的rsyslog日志服务器服务端

使用：
配置vi  /etc/rsyslog.conf 
\*\.\* @192.168.1.105:5514
保存退出
重启rsyslog服务
同样也可以接收nginx的syslog模块打过来的日志


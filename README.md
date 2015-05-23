# plog
Python写的rsyslog日志服务器服务端

使用：
配置</br>
vi  /etc/rsyslog.conf </br>
\*\.\* @192.168.1.105:5514</br>
保存退出</br>
重启rsyslog服务</br>
同样也可以接收nginx的syslog模块打过来的日志</br>
mysql启动日志</br>
/usr/bin/mysqld_safe --datadir=/var/lib/mysql --socket=/var/lib/mysql/mysql.sock --pid-file=/var/run/mysqld/mysqld.pid --basedir=/usr --user=mysql --syslog --syslog-tag=标签名字


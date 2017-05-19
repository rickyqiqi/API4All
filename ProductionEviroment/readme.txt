主要文件列表
apache http配置文件：/etc/httpd/conf/httpd.conf    -rw-r--r--    root root
apache https配置文件：/etc/httpd/conf/ssl.conf     -rw-r--r--    root root
https秘钥文件：/etc/httpd/conf.d/server.crt    -rw-r--r--    root root
                                 server.csr    -rw-r--r--    root root
                                 server.key    -rw-r--r--    root root
                                 server.pem    -rw-r--r--    root root
appser日志目录：/var/log/appserver    drwx------    apache apache
autotrader日志目录：/var/log/autotrader    drwx------    apache apache
redis配置文件：/etc/redis/redis.conf    -rw-r--r--    root root
redis初始化启动脚本：/etc/init.d/redis    -rexr-xr-x    root root

准备编译环境
yum update
yum install gcc automake autoconf libtool make curl curl-devel zlib-devel openssl-devel perl perl-devel
yum install -y tcl
yum install tcl-devel
yum install python-devel
yum install sqlite sqlite-devel

1.安装apache
yum -y install httpd
rpm -qa | grep httpd

启动/停止/重新启动/状态
service httpd start
service httpd stop
service httpd restart
service httpd status

2.安装mod_wsgi
yum -y install mod_wsgi

3.安装easy_install和pip
sudo yum -y install epel-release
sudo yum -y install python-pip
sudo yum clean all

4.安装flask
pip install flask
yum -y install mod_wsgi

5.创建Web App
将test.py和test.wsgi复制到/var/www/autotrader/目录下
修改这两个文件的属性：
chmod 644 test.py test.wsgi

6.在Apache中配置站点
a. 如果是http协议，修改如下文件内容：
nano /etc/httpd/conf/httpd.conf
文件最后加入以下内容：

LoadModule wsgi_module modules/mod_wsgi.so



<VirtualHost *:80>

    ServerAdmin example@company.com

    DocumentRoot /var/www/autotrader

    <Directory "/var/www/autotrader">

        Order allow,deny

        Allow from all

    </Directory>

    WSGIScriptAlias /flasktest /var/www/autotrader/test.wsgi

</VirtualHost>


b. 如果是https协议
步骤1：生成密钥
命令：openssl genrsa 1024 > server.key
说明：这是用128位rsa算法生成密钥，得到server.key文件
步骤2: 生成证书请求文件
命令：openssl req -new -key server.key > server.csr
说明：这是用步骤1的密钥生成证书请求文件server.csr, 这一步提很多问题，一一输入
步骤3: 生成证书
命令：openssl req -x509 -days 365 -key server.key -in server.csr > server.crt
说明：这是用步骤1,2的的密钥和证书请求生成证书server.crt，-days参数指明证书有效期，单位为天
客户端证书详见“https客户端.txt”

yum install mod_ssl

修改如下文件内容：
nano /etc/httpd/conf.d/ssl.conf
文件最后加入以下内容：
LoadModule ssl_module modules/mod_ssl.so

SSLCertificateFile /etc/httpd/conf.d/server.crt

SSLCertificateKeyFile /etc/httpd/conf.d/server.key


WSGIScriptAlias /flasktest "/var/www/autotrader/test.wsgi"

<Directory /var/www/autotrader>

    Order deny,allow

    Allow from all

    SSLOptions +StdEnvVars

</Directory>

7. 测试
重启apache：
service httpd restart
清除iptables规则：
iptables -F
iptables -X
查看iptables规则出现如下结果：
iptables -L -n
 Chain INPUT (policy ACCEPT)
 target       prot opt source                 destination         

Chain FORWARD (policy ACCEPT)
 target       prot opt source                 destination         

Chain OUTPUT (policy ACCEPT)
 target       prot opt source                 destination

浏览器输入http://localhost/flasktest/hello?name=CZY出现响应页面

测试完毕后，需要修改httpd.conf和ssl.conf中的WSGIScriptAlias行，改为
WSGIScriptAlias / "/var/www/autotrader/autotrader.wsgi"


8.安装redis 3.2.6
tar zxvf redis-3.2.6.tar.gz
make
make install

sudo useradd redis  
sudo mkdir -p /var/lib/redis  
sudo mkdir -p /var/log/redis  
sudo chown redis.redis /var/lib/redis 
sudo chown redis.redis /var/log/redis  

启动redis
redis-server &
通过启动命令检查Redis服务器状态  
netstat -nlt|grep 6379

开机自启动
mkdir -p /etc/redis/  
cp redis.conf /etc/redis/redis.conf
打开文件/etc/redis/redis.conf， 找到"daemonize no"改为"daemonize yes"，然后执行
redis-server /etc/redis/redis.conf
复制redis初始化启动脚本文件，脚本路径/etc/init.d/redis 

9.安装sqlcipher
tar zxvf sqlcipher-3.4.0.tar.gz
./configure -enable-tempstore=yes CFLAGS="-DSQLITE_HAS_CODEC" LDFLAGS="-lcrypto"
make
make install
ln -s /usr/local/lib/libsqlcipher.so.0 /usr/lib64/libsqlcipher.so.0
- 使用python3，安装pysqlcipher3，执行"pip install pysqlcipher3"
- 使用python2，安装pysqlcipher，执行"pip install pysqlcipher"

10.安装pycrypto库
pip install pycrypto

11.安装python redis库
easy_install redis
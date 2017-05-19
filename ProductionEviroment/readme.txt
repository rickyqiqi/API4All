��Ҫ�ļ��б�
apache http�����ļ���/etc/httpd/conf/httpd.conf    -rw-r--r--    root root
apache https�����ļ���/etc/httpd/conf/ssl.conf     -rw-r--r--    root root
https��Կ�ļ���/etc/httpd/conf.d/server.crt    -rw-r--r--    root root
                                 server.csr    -rw-r--r--    root root
                                 server.key    -rw-r--r--    root root
                                 server.pem    -rw-r--r--    root root
appser��־Ŀ¼��/var/log/appserver    drwx------    apache apache
autotrader��־Ŀ¼��/var/log/autotrader    drwx------    apache apache
redis�����ļ���/etc/redis/redis.conf    -rw-r--r--    root root
redis��ʼ�������ű���/etc/init.d/redis    -rexr-xr-x    root root

׼�����뻷��
yum update
yum install gcc automake autoconf libtool make curl curl-devel zlib-devel openssl-devel perl perl-devel
yum install -y tcl
yum install tcl-devel
yum install python-devel
yum install sqlite sqlite-devel

1.��װapache
yum -y install httpd
rpm -qa | grep httpd

����/ֹͣ/��������/״̬
service httpd start
service httpd stop
service httpd restart
service httpd status

2.��װmod_wsgi
yum -y install mod_wsgi

3.��װeasy_install��pip
sudo yum -y install epel-release
sudo yum -y install python-pip
sudo yum clean all

4.��װflask
pip install flask
yum -y install mod_wsgi

5.����Web App
��test.py��test.wsgi���Ƶ�/var/www/autotrader/Ŀ¼��
�޸��������ļ������ԣ�
chmod 644 test.py test.wsgi

6.��Apache������վ��
a. �����httpЭ�飬�޸������ļ����ݣ�
nano /etc/httpd/conf/httpd.conf
�ļ��������������ݣ�

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


b. �����httpsЭ��
����1��������Կ
���openssl genrsa 1024 > server.key
˵����������128λrsa�㷨������Կ���õ�server.key�ļ�
����2: ����֤�������ļ�
���openssl req -new -key server.key > server.csr
˵���������ò���1����Կ����֤�������ļ�server.csr, ��һ����ܶ����⣬һһ����
����3: ����֤��
���openssl req -x509 -days 365 -key server.key -in server.csr > server.crt
˵���������ò���1,2�ĵ���Կ��֤����������֤��server.crt��-days����ָ��֤����Ч�ڣ���λΪ��
�ͻ���֤�������https�ͻ���.txt��

yum install mod_ssl

�޸������ļ����ݣ�
nano /etc/httpd/conf.d/ssl.conf
�ļ��������������ݣ�
LoadModule ssl_module modules/mod_ssl.so

SSLCertificateFile /etc/httpd/conf.d/server.crt

SSLCertificateKeyFile /etc/httpd/conf.d/server.key


WSGIScriptAlias /flasktest "/var/www/autotrader/test.wsgi"

<Directory /var/www/autotrader>

    Order deny,allow

    Allow from all

    SSLOptions +StdEnvVars

</Directory>

7. ����
����apache��
service httpd restart
���iptables����
iptables -F
iptables -X
�鿴iptables����������½����
iptables -L -n
 Chain INPUT (policy ACCEPT)
 target       prot opt source                 destination         

Chain FORWARD (policy ACCEPT)
 target       prot opt source                 destination         

Chain OUTPUT (policy ACCEPT)
 target       prot opt source                 destination

���������http://localhost/flasktest/hello?name=CZY������Ӧҳ��

������Ϻ���Ҫ�޸�httpd.conf��ssl.conf�е�WSGIScriptAlias�У���Ϊ
WSGIScriptAlias / "/var/www/autotrader/autotrader.wsgi"


8.��װredis 3.2.6
tar zxvf redis-3.2.6.tar.gz
make
make install

sudo useradd redis  
sudo mkdir -p /var/lib/redis  
sudo mkdir -p /var/log/redis  
sudo chown redis.redis /var/lib/redis 
sudo chown redis.redis /var/log/redis  

����redis
redis-server &
ͨ������������Redis������״̬  
netstat -nlt|grep 6379

����������
mkdir -p /etc/redis/  
cp redis.conf /etc/redis/redis.conf
���ļ�/etc/redis/redis.conf�� �ҵ�"daemonize no"��Ϊ"daemonize yes"��Ȼ��ִ��
redis-server /etc/redis/redis.conf
����redis��ʼ�������ű��ļ����ű�·��/etc/init.d/redis 

9.��װsqlcipher
tar zxvf sqlcipher-3.4.0.tar.gz
./configure -enable-tempstore=yes CFLAGS="-DSQLITE_HAS_CODEC" LDFLAGS="-lcrypto"
make
make install
ln -s /usr/local/lib/libsqlcipher.so.0 /usr/lib64/libsqlcipher.so.0
- ʹ��python3����װpysqlcipher3��ִ��"pip install pysqlcipher3"
- ʹ��python2����װpysqlcipher��ִ��"pip install pysqlcipher"

10.��װpycrypto��
pip install pycrypto

11.��װpython redis��
easy_install redis
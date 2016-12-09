#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import logging
import logging.config
from pysqlcipher3 import dbapi2 as sqlite
import base64
from Crypto import Random
from Crypto.Cipher import AES

def send_mails():
    accountstruct = []
    accountdata = []
    mail_msg = ""
    org_recv = ""

    try:
        # 连接到SQLite数据库
        conn = sqlite.connect('/var/www/autotrader/sqlite3/mailtoclients.db')
        # 创建一个Cursor
        cursor = conn.cursor()
        # 秘钥
        cursor.execute("pragma key='autotrader@8'")
        # 查询邮件表数据结构
        cursor.execute('pragma table_info(mails)')
        mailsstruct = [list(item)[1] for item in cursor.fetchall()]
        # 执行邮件表查询语句
        cursor.execute('select * from mails')
        mailsline = cursor.fetchone()

        cursor.close()
        conn.close()

        if mailsline != None:
            for i in range(len(mailsstruct)):
                if mailsstruct[i] == 'content':
                    mail_msg = mailsline[i]
                elif mailsstruct[i] == 'receivers':
                    org_recv = mailsline[i]
                    receivers = org_recv.split(",")
    except:
        logger.error("客户邮件数据库读取失败")

    if mail_msg == "":
        return False

    logger.debug("发送邮件：%s, %s" % (mail_msg, org_recv))
        
    policyname = ""
    start = mail_msg.find('策略名称：')
    end = mail_msg.find('</p>')
    if start > 0 and end > start:
        policyname = mail_msg[start:end]

    key = b'Auto]8[Trader]@3'
    iv = b'@Trader[9t1]Auto'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_password64 = mail_pass.encode('utf-8')
    cipher_password = base64.decodestring(cipher_password64)
    password = cipher.decrypt(cipher_password)
    password = password.strip(b'\0')
    password = password.decode('utf-8')
    # 避免使用列表引用
    recvUnsent = receivers[:]
    # 按收件人一封封地发邮件，以避免被视为垃圾邮件
    for item in receivers:
        message = MIMEText(mail_msg, 'html', 'utf-8')
        message['From'] = "<%s>" %(sender)
        subject = policyname + '买卖信号'
        message['Subject'] = Header(subject, 'utf-8')
        message['To'] = "<%s>" %(item)
        logger.info("发送邮件至：%s", item)

        try:
            smtpObj = smtplib.SMTP()
            #smtpObj.set_debuglevel(1)
            smtpObj.connect(mail_host, 25)    # 25 为 SMTP 端口号
            smtpObj.login(mail_user, password)
            smtpObj.sendmail(sender, item, message.as_string())
            smtpObj.quit()
            # remove the item from unsent list
            recvUnsent.remove(item)
            logger.info("邮件发送成功")
        except smtplib.SMTPException:
            logger.error("无法发送邮件")

    try:
        # 连接到SQLite数据库
        conn = sqlite.connect('/var/www/autotrader/sqlite3/mailtoclients.db')
        # 创建一个Cursor
        cursor = conn.cursor()
        # 秘钥
        cursor.execute("pragma key='autotrader@8'")
        if recvUnsent != []:
            recvstr = ""
            for str in recvUnsent:
                recvstr = recvstr + str + ','
            # 删除最后一个逗号
            recvstr = recvstr[:-1]
            logger.debug("邮件信息更新客户邮件数据库：%s, %s" % (mail_msg, recvstr))
            cursor.execute('update mails set receivers=? where content=? and receivers=?', (recvstr, mail_msg, org_recv))
        else:
            logger.debug("邮件信息从客户邮件数据库中删除：%s, %s" % (mail_msg, org_recv))
            cursor.execute('delete from mails where content=? and receivers=?', (mail_msg, org_recv))

        cursor.close()
        conn.commit()
        conn.close()
    except:
        logger.error("客户邮件数据库更新失败")
    
    return True

logging.config.fileConfig("/var/www/autotrader/logger.conf")
logger = logging.getLogger("main")

# 第三方 SMTP 服务
mail_host=""  #设置服务器
mail_user=""    #用户名
mail_pass=""   #口令
sender = ""

try:
    # 连接到SQLite数据库
    conn = sqlite.connect('/var/www/autotrader/sqlite3/mailtoclients.db')
    # 创建一个Cursor
    cursor = conn.cursor()
    # 秘钥
    cursor.execute("pragma key='autotrader@8'")
    # 查询账户表数据结构
    cursor.execute('pragma table_info(account)')
    accountstruct = [list(item)[1] for item in cursor.fetchall()]
    # 执行账户表查询语句
    cursor.execute('select * from account')
    accountdata = cursor.fetchall()

    cursor.close()
    conn.close()
except:
    logger.error("客户邮件数据库读取失败")

for dataitem in accountdata:
    for i in range(len(accountstruct)):
        if accountstruct[i] == 'account':
            mail_user = dataitem[i]
        elif accountstruct[i] == 'password':
            mail_pass = dataitem[i]
        elif accountstruct[i] == 'sender':
            sender = dataitem[i]
        elif accountstruct[i] == 'smtphost':
            mail_host = dataitem[i]
    if mail_user != "" and mail_host != "":
        break

logger.debug("smtp账号信息：%s, %s, %s, %s" % (mail_user, mail_pass, sender, mail_host))

if mail_host == "":
    logger.error("SMTP主机配置空")
elif mail_user == "":
    logger.error("邮件发送账户空")
else:
    while True:
        # sleep for 5 seconds if no other mails to send
        if not send_mails():
            time.sleep(5)

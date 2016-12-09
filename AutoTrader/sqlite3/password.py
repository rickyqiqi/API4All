#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import getpass
from pysqlcipher3 import dbapi2 as sqlite
import base64
from Crypto import Random
from Crypto.Cipher import AES

if len(sys.argv) > 1:
    accountdata = []
    try:
        # 连接到SQLite数据库
        conn = sqlite.connect('/var/www/autotrader/sqlite3/%s' % (sys.argv[1]))
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
        print("客户邮件数据库读取失败")

    count = 0
    mail_user = []
    mail_pass = []
    sender = []
    mail_host = []
    print("\n------------------------------------------------------------------------------------")
    print("|                                ACCOUNT INFOMATION                                |")
    print("------------------------------------------------------------------------------------")
    print("NO.\tAccount Name\t\tPassword\t\t\tSender Information\tSMTP Host")
    for dataitem in accountdata:
        for i in range(len(accountstruct)):
            if accountstruct[i] == 'account':
                mail_user.append(dataitem[i])
            elif accountstruct[i] == 'password':
                mail_pass.append(dataitem[i])
            elif accountstruct[i] == 'sender':
                sender.append(dataitem[i])
            elif accountstruct[i] == 'smtphost':
                mail_host.append(dataitem[i])
        print("%d\t%s\t\t%s\t%s\t%s" % (count+1, mail_user[count], mail_pass[count].encode('utf-8'), sender[count], mail_host[count]))
        count = count + 1

    selection = 0
    while selection <= 0 or selection > count:
        selection = int(input('\nSelect to change password:'))
    selection = selection - 1

    print("\nAccount(\"%s\", \"%s\") Password To Be Changed" %(mail_user[selection], mail_host[selection]))

    key = b'Auto]8[Trader]@3'
    iv = b'@Trader[9t1]Auto'

    org_password_NOK = False
    if mail_pass[selection] != '':
        password = getpass.getpass('Please enter the original password:')
        length = len(password)
        remainder = length%AES.block_size
        if remainder != 0:
            password = password + ('\0' * (AES.block_size-remainder))
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_password = cipher.encrypt(password)
        cipher_password64 = base64.encodestring(cipher_password)
        if cipher_password64 == mail_pass[selection].encode('utf-8'):
            org_password_NOK = False
        else:
            org_password_NOK = True

    if not org_password_NOK:
        password = ''
        password2 = '\0'
        while password != password2:
            password = getpass.getpass('Please enter the new password:')
            password2 = getpass.getpass('Please enter the new password again:')
        length = len(password)
        remainder = length%AES.block_size
        if remainder != 0:
            password = password + ('\0' * (AES.block_size-remainder))
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_password = cipher.encrypt(password)
        cipher_password64 = base64.encodestring(cipher_password)
        try:
            # 连接到SQLite数据库
            conn = sqlite.connect('/var/www/autotrader/sqlite3/%s' % (sys.argv[1]))
            # 创建一个Cursor
            cursor = conn.cursor()
            # 秘钥
            cursor.execute("pragma key='autotrader@8'")
            cursor.execute('update account set password=? where account=? and password=? and sender=? and smtphost=?', (cipher_password64.decode('utf-8'), mail_user[selection], mail_pass[selection],sender[selection], mail_host[selection]))

            cursor.close()
            conn.commit()
            conn.close()

            print("Account(\"%s\", \"%s\") password updated!" %(mail_user[selection], mail_host[selection]))
        except:
            print("客户邮件数据库更新失败")
    else:
        print("Original password error!")
else:
    print("\nUsage: ./password.py [sqlcipher3_database_file]\n")
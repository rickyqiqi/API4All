#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import getpass
from pysqlcipher3 import dbapi2 as sqlite
import base64
from Crypto import Random
from Crypto.Cipher import AES

def changePassword(dbFile):
    accountdata = []
    try:
        # 连接到SQLite数据库
        conn = sqlite.connect('/var/www/autotrader/sqlite3/%s' % (dbFile))
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
    print("|                                Account Information                                |")
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
            conn = sqlite.connect('/var/www/autotrader/sqlite3/%s' % (dbFile))
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

def UpdateRecievers(dbFile):
    receiversstruct = []
    receiversdata = []
    try:
        # 连接到SQLite数据库
        conn = sqlite.connect('/var/www/autotrader/sqlite3/%s' % (dbFile))
        # 创建一个Cursor
        cursor = conn.cursor()
        # 秘钥
        cursor.execute("pragma key='autotrader@8'")
        # 查询收件人表数据结构
        cursor.execute('pragma table_info(receivers)')
        receiversstruct = [list(item)[1] for item in cursor.fetchall()]
        # 执行收件人表查询语句
        cursor.execute('select * from receivers where enabled=?', ('1',))
        receiversdata = cursor.fetchall()

        cursor.close()
        conn.close()
    except:
        print("客户邮件数据库读取失败")

    print("\n------------------------------------------------------------------------------------")
    print("|                              Receivers Information                               |")
    print("------------------------------------------------------------------------------------")
    if len(receiversstruct) > 0:
        submenu_title = "NO.\t"
        for i in range(len(receiversstruct)):
            if receiversstruct[i] == "address":
                submenu_title = submenu_title + "%s\t\t\t" % (receiversstruct[i])
            else:
                submenu_title = submenu_title + "%s\t\t" % (receiversstruct[i])
        print("%s" % (submenu_title))
        lineNO = 1
        for dataitem in receiversdata:
            lineStr = "%d\t" % (lineNO)
            for i in range(len(receiversstruct)):
                if receiversstruct[i] == "enabled":
                    lineStr = lineStr + "%d\t\t" % (dataitem[i])
                elif receiversstruct[i] == "address":
                    lineStr = lineStr + "%s\t" % (dataitem[i])
                    if len(dataitem[i]) < 16:
                        lineStr = lineStr + "\t"
                else:
                    lineStr = lineStr + "%s\t" % (dataitem[i])
            print("%s" % (lineStr))
            lineNO = lineNO + 1

    selection = ""
    while selection != "A" and selection != "a" and selection != "D" and selection != "d" and selection != "E" and selection != "e" :
        selection = input('\n\"A\" to Add, \"D\" to Delete, \"E\" to Exit:')
        if selection == "A" or selection == "a":
            print('Add a Reciever ...')
            mail_address = input('Mail Address:')
            mail_enable = 2
            while mail_enable != 1 and mail_enable != 0:
                mail_enable = int(input('Mail Enable?(1-enable, 0-disable):'))
            user_name = input('User Name:')
            print("%s to be Added ..." % (mail_address))
            confirm = ""
            while confirm != "y" and confirm != "Y" and confirm != "n" and confirm != "N":
                confirm = input('\"y\" to confirm, or \"n\" to cancel:')
                if confirm == "y" or confirm == "Y":
                    try:
                        # 连接到SQLite数据库
                        conn = sqlite.connect('/var/www/autotrader/sqlite3/%s' % (dbFile))
                        # 创建一个Cursor
                        cursor = conn.cursor()
                        # 秘钥
                        cursor.execute("pragma key='autotrader@8'")
                        cursor.execute('insert into receivers values (?, ?, ?)', (mail_address, mail_enable, user_name))
                        cursor.close()
                        conn.commit()
                        conn.close()
                    except:
                        print("客户邮件数据库更新失败")
                elif confirm == "n" or confirm == "N":
                    break
        elif selection == "D" or selection == "d":
            line = 0
            while line <= 0 or line > lineNO:
                line = int(input('\nSelect the NO. to Delete:'))
            print("%s to be deleted ..." % (receiversdata[line-1][0]))
            confirm = ""
            while confirm != "y" and confirm != "Y" and confirm != "n" and confirm != "N":
                confirm = input('\"y\" to confirm, or \"n\" to cancel:')
                if confirm == "y" or confirm == "Y":
                    try:
                        # 连接到SQLite数据库
                        conn = sqlite.connect('/var/www/autotrader/sqlite3/%s' % (dbFile))
                        # 创建一个Cursor
                        cursor = conn.cursor()
                        # 秘钥
                        cursor.execute("pragma key='autotrader@8'")
                        cursor.execute('delete from receivers where address=? and enabled=? and name=?', (receiversdata[line-1][0], receiversdata[line-1][1], receiversdata[line-1][2]))
                        cursor.close()
                        conn.commit()
                        conn.close()
                    except:
                        print("客户邮件数据库更新失败")
                elif confirm == "n" or confirm == "N":
                    break

        elif selection == "E" or selection == "e":
            print("Exit ...")

if len(sys.argv) > 1:
    print("\n------------------------------------------------------------------------------------")
    print("|                              MAIL TO CLIENTS DATABSE                             |")
    print("------------------------------------------------------------------------------------")
    print("NO.\tMenu")
    print("1\tUpdate Reciever List")
    print("2\tChange Sender Account Password")
    selection = 0
    while selection <= 0 or selection > 2:
        selection = int(input('\nSelect Menu:'))

    if selection == 1:
        UpdateRecievers(sys.argv[1])
    elif selection == 2:
        changePassword(sys.argv[1])
else:
    print("\nUsage: ./password.py [sqlcipher3_database_file]\n")
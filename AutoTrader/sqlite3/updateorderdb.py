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
        cursor.execute('pragma table_info(accounts)')
        accountstruct = [list(item)[1] for item in cursor.fetchall()]
        # 执行账户表查询语句
        cursor.execute('select * from accounts')
        accountdata = cursor.fetchall()

        cursor.close()
        conn.close()
    except:
        print("客户邮件数据库读取失败")

    count = 0
    UserID = []
    passwd = []
    Name = []
    PhoneNO = []
    ServerAccount = []
    print("\n------------------------------------------------------------------------------------")
    print("|                                Account Information                                |")
    print("------------------------------------------------------------------------------------")
    print("NO.\tUser ID\t\tPassword\t\t\tName\tPhone NO\tServer Account")
    for dataitem in accountdata:
        for i in range(len(accountstruct)):
            if accountstruct[i] == 'UserID':
                UserID.append(dataitem[i])
            elif accountstruct[i] == 'Password':
                passwd.append(dataitem[i])
            elif accountstruct[i] == 'Name':
                Name.append(dataitem[i])
            elif accountstruct[i] == 'PhoneNO':
                PhoneNO.append(dataitem[i])
            elif accountstruct[i] == 'ServerAccount':
                ServerAccount.append(dataitem[i])
        print("%d\t%s\t%s\t%s\t%s\t%d" % (count+1, UserID[count], passwd[count].encode('utf-8'), Name[count], PhoneNO[count], ServerAccount[count]))
        count = count + 1

    selection = 0
    while selection <= 0 or selection > count:
        selection = int(input('\nSelect to change password:'))
    selection = selection - 1

    print("\nAccount(\"%s\", \"%s\", \"%s\") Password To Be Changed" %(UserID[selection], Name[selection], PhoneNO[selection]))

    key = b'Auto]8[Trader]@3'
    iv = b'@Trader[9t1]Auto'

    org_password_NOK = False
    if passwd[selection] != '':
        password = getpass.getpass('Please enter the original password:')
        length = len(password)
        remainder = length%AES.block_size
        if remainder != 0:
            password = password + ('\0' * (AES.block_size-remainder))
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_password = cipher.encrypt(password)
        cipher_password64 = base64.encodestring(cipher_password)
        if cipher_password64 == passwd[selection].encode('utf-8'):
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
            cursor.execute('update accounts set Password=? where UserID=? and Password=? and Name=? and PhoneNO=? and ServerAccount=?', (cipher_password64.decode('utf-8'), UserID[selection], passwd[selection], Name[selection], PhoneNO[selection], ServerAccount[selection]))

            cursor.close()
            conn.commit()
            conn.close()

            print("Account(\"%s\", \"%s\", \"%s\") password updated!" %(UserID[selection], Name[selection], PhoneNO[selection]))
        except:
            print("客户邮件数据库更新失败")
    else:
        print("Original password error!")

if len(sys.argv) > 1:
    print("\n------------------------------------------------------------------------------------")
    print("|                                  ORDERS DATABSE                                  |")
    print("------------------------------------------------------------------------------------")
    print("NO.\tMenu")
    print("1\tChange Accounts Password")
    selection = 0
    while selection <= 0 or selection > 1:
        selection = int(input('\nSelect Menu:'))

    if selection == 1:
        changePassword(sys.argv[1])
else:
    print("\nUsage: ./%s [sqlcipher3_database_file]\n" % (sys.argv[0]))
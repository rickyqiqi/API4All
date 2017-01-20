#coding=utf-8

import os
import sys
import types
import time
import threading
import hashlib
import random
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from flask import Flask
from flask import request
import logging
import logging.config
from pysqlcipher3 import dbapi2 as sqlite
import base64
from Crypto import Random
from Crypto.Cipher import AES
from redis import Redis

app = Flask(__name__)

reload(sys)
sys.setdefaultencoding('utf-8')

logging.config.fileConfig("/var/www/autotrader/logger.conf")
logger = logging.getLogger("main")
telegramlogger = logging.getLogger("telegram")

# check if mail sender process in running, if not start it
cmd_line = 'python /var/www/autotrader/mailsender/mailsender.py'
cmd_output = os.popen("pgrep -f \'%s\'" % (cmd_line)).read()
if cmd_output == '':
    os.popen("%s &" % (cmd_line))

@app.route('/autotrader/authentiate', methods=['POST'])
def authentiate():
    # uncoded response data
    response_data = {"timestamp": 0, "rand": 0, "txnCode": -1}
    # request json string is in keys
    keys = request.form.keys()

    query_str = ""
    if request.query_string != "":
        query_str = '/' + str(request.query_string)
    telegramlogger.info(request.remote_addr + ' ==> ' + request.host + request.path + query_str + ': ' + str(keys))
    # check if there's only 1 json string key
    if len(keys) == 1:
        # get the json request string
        json_decode = json.loads(keys[0])
        if not (json_decode.has_key('rand') and type(json_decode["rand"]) == types.IntType):
            logger.error('JSON key \"rand\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('equipId') and type(json_decode["equipId"]) == types.UnicodeType):
            logger.error('JSON key \"equipId\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('encType') and type(json_decode["encType"]) == types.IntType):
            logger.error('JSON key \"encType\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('encKey') and type(json_decode["encKey"]) == types.UnicodeType):
            logger.error('JSON key \"encKey\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        else:
            # check if encrypt algorithm type is ok
            encType = json_decode['encType']
            if encType == 0:
                encKey = json_decode['encKey']

                key = b'Auto]8[Trader]@3'
                iv = b'@Trader[9t1]Auto'
                cipher = AES.new(key, AES.MODE_CBC, iv)
                cipher_enkey64 = (encKey[0]).encode('utf-8')
                cipher_encKey = base64.decodestring(cipher_enkey64)
                plainKey = cipher.decrypt(cipher_encKey)
                plainKey = plainKey.strip(b'\0')
                plainKey = plainKey.decode('utf-8')

                redis = Redis()
                pipe = redis.pipeline()
                pipe.set(json_decode["equipId"], plainKey)
                pipe.expire(user_key, 7200) # key expired after 2 hours
                pipe.execute()

                # response with success
                response_data["txnCode"] = 0
            else:
                # response with encrypt algorithm unkown error
                response_data["txnCode"] = 3
                logger.error('encrypt algorithm type (%d) unkown' %(encType))
    else :
        # response with parameters error
        response_data["txnCode"] = 1

    response_data["timestamp"] = int(time.time())
    response_data["rand"] = random.randrange(-2147483647, 2147483647)
    json_response = json.dumps(response_data)
    telegramlogger.info(request.host + ' ==> ' + request.remote_addr + ': ' + json_response)
    return json_response

@app.route('/autotrader/onlinestatus', methods=['POST'])
def onlinestatus():
    # uncoded response data
    response_data = {"timestamp": 0, "rand": 0, "txnCode": -1}
    # request json string is in keys
    keys = request.form.keys()

    query_str = ""
    if request.query_string != "":
        query_str = '/' + str(request.query_string)
    telegramlogger.info(request.remote_addr + ' ==> ' + request.host + request.path + query_str + ': ' + str(keys))
    # check if there's only 1 json string key
    if len(keys) == 1:
        # get the json request string
        json_decode = json.loads(keys[0])
        if not (json_decode.has_key('timestamp') and type(json_decode["timestamp"]) == types.IntType):
            logger.error('JSON key \"timestamp\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('rand') and type(json_decode["rand"]) == types.IntType):
            logger.error('JSON key \"rand\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('status') and type(json_decode["status"]) == types.IntType):
            logger.error('JSON key \"status\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        else:
            # if current time and request time stamp in range
            currenttime = int(time.time())
            requesttime = json_decode['timestamp']
            if abs(currenttime-requesttime) > 10:
                # response with time stamp error
                response_data["txnCode"] = 2
                logger.error('Request time stamp %d out of range' %requesttime)
            else:
                if requesttime != currenttime:
                    logger.warning('Server time is different - request: %d, local: %d' %(requesttime, currenttime))

                # response with success
                response_data["txnCode"] = 0
    else :
        # response with parameters error
        response_data["txnCode"] = 1

    response_data["timestamp"] = int(time.time())
    response_data["rand"] = random.randrange(-2147483647, 2147483647)
    json_response = json.dumps(response_data)
    telegramlogger.info(request.host + ' ==> ' + request.remote_addr + ': ' + json_response)
    return json_response

@app.route('/autotrader/stocktrade', methods=['POST'])
def stocktrade():
    # uncoded response data
    response_data = {"timestamp": 0, "rand": 0, "txnCode": -1}
    # request json string is in keys
    keys = request.form.keys()

    query_str = ""
    if request.query_string != "":
        query_str = '/' + str(request.query_string)
    telegramlogger.info(request.remote_addr + ' ==> ' + request.host + request.path + query_str + ': ' + str(keys))
    # check if there's only 1 json string key
    if len(keys) == 1:
        # get the json request string
        json_decode = json.loads(keys[0])
        if not (json_decode.has_key('timestamp') and type(json_decode["timestamp"]) == types.IntType):
            logger.error('JSON key \"timestamp\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('rand') and type(json_decode["rand"]) == types.IntType):
            logger.error('JSON key \"rand\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('accountNo') and type(json_decode["accountNo"]) == types.UnicodeType):
            logger.error('JSON key \"accountNo\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('password') and type(json_decode["password"]) == types.UnicodeType):
            logger.error('JSON key \"password\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('policyName') and type(json_decode["policyName"]) == types.UnicodeType):
            logger.error('JSON key \"policyName\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('marketCode') and type(json_decode["marketCode"]) == types.UnicodeType):
            logger.error('JSON key \"marketCode\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('txnTime') and type(json_decode["txnTime"]) == types.UnicodeType):
            logger.error('JSON key \"txnTime\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('security') and type(json_decode["security"]) == types.UnicodeType):
            logger.error('JSON key \"security\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('secname') and type(json_decode["secname"]) == types.UnicodeType):
            logger.error('JSON key \"secname\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('value') and (type(json_decode["value"]) == types.FloatType or type(json_decode["value"]) == types.IntType)):
            logger.error('JSON key \"value\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('price') and (type(json_decode["price"]) == types.FloatType or type(json_decode["price"]) == types.IntType)):
            logger.error('JSON key \"price\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        elif not (json_decode.has_key('orderId') and type(json_decode["orderId"]) == types.IntType):
            logger.error('JSON key \"orderId\" related error')
            # response with parameters error
            response_data["txnCode"] = 1
        else:
            # if current time and request time stamp in range
            currenttime = int(time.time())
            requesttime = json_decode['timestamp']
            if abs(currenttime-requesttime) > 10:
                # response with time stamp error
                response_data["txnCode"] = 2
                logger.error('Request time stamp %d out of range' %requesttime)
            else:
                if requesttime != currenttime:
                    logger.warning('Server time is different - request: %d, local: %d' %(requesttime, currenttime))

                passwd = []
                try:
                    # 连接到SQLite数据库
                    conn = sqlite.connect('/var/www/autotrader/sqlite3/orders.db')
                    # 创建一个Cursor
                    cursor = conn.cursor()
                    # 秘钥
                    cursor.execute("PRAGMA KEY='autotrader@8'")
                    # 执行账户表查询语句
                    cursor.execute('SELECT Password FROM accounts WHERE UserID=? AND ServerAccount=1', (json_decode["accountNo"],))
                    passwd = [list(item)[0] for item in cursor.fetchall()]

                    cursor.close()
                    conn.close()
                except:
                    logger.error("订单数据库读取失败")

                # check if the account NO. is valid
                if len(passwd) > 0:
                    key = b'Auto]8[Trader]@3'
                    iv = b'@Trader[9t1]Auto'
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    cipher_password64 = (passwd[0]).encode('utf-8')
                    cipher_password = base64.decodestring(cipher_password64)
                    password = cipher.decrypt(cipher_password)
                    password = password.strip(b'\0')
                    password = password.decode('utf-8')
                    # calculate the md5 value
                    m2 = hashlib.md5()
                    plainpasswd = str(json_decode["timestamp"]) + str(json_decode["rand"]) + str(password)
                    m2.update(plainpasswd)
                    if json_decode["password"] == m2.hexdigest():
                        if json_decode["marketCode"] == "cn":
                            ret = True
                            logger.debug("%s - To set stock %s (%s) to value %.4f, recommended price: %.2f, orderID: %d" \
                                  %(json_decode["policyName"], json_decode["secname"], json_decode["security"], json_decode["value"]*100, json_decode["price"], json_decode["orderId"]))
                            # data information to database
                            data_to_db(json_decode["policyName"], json_decode["security"], json_decode["secname"], json_decode["value"], json_decode["price"], json_decode["txnTime"], json_decode["orderId"], json_decode["marketCode"], json_decode["accountNo"])
                            # check if mail sender process in running, if not start it
                            cmd_line = 'python /var/www/autotrader/mailsender/mailsender.py'
                            cmd_output = os.popen("pgrep -f \'%s\'" % (cmd_line)).read()
                            if cmd_output == '':
                                os.popen("%s &" % (cmd_line))

                            if ret:
                                # response with success
                                response_data["txnCode"] = 0
                            else:
                                # response with parameters error
                                response_data["txnCode"] = 10
                                logger.error('Stock account process error')
                        else:
                            # response with parameters error
                            response_data["txnCode"] = 1
                            logger.error('Market code error')
                    else:
                        # response with password error
                        response_data["txnCode"] = 7
                        logger.error('Password error')
                else:
                    # response with account No invalid
                    response_data["txnCode"] = 6
                    logger.error('Invalid account NO.')
    else :
        # response with parameters error
        response_data["txnCode"] = 1
        logger.error('Json string error')

    response_data["timestamp"] = int(time.time())
    response_data["rand"] = random.randrange(-2147483647, 2147483647)
    json_response = json.dumps(response_data)
    telegramlogger.info(request.host + ' ==> ' + request.remote_addr + ': ' + json_response)
    return json_response

def data_to_db(policyname, security, secname, value, price, tradedatetime, orderId, marketCode, accountNo):
    try:
        # 连接到SQLite数据库
        conn = sqlite.connect('/var/www/autotrader/sqlite3/orders.db')
        # 创建一个Cursor
        cursor = conn.cursor()
        # 秘钥
        cursor.execute("PRAGMA KEY='autotrader@8'")
        # 更新订单表
        cursor.execute('INSERT INTO orders (tradeTime, policyName, security, secname, positions, price, orderId, marketCode, accountNo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (tradedatetime, policyname, security, secname, value, price, orderId, marketCode, accountNo))

        # 查询对应策略的表是否已经存在，如果股票持仓表存在就删除并重新生成
        tableName = policyname + '_' + accountNo + '_' + marketCode + '_当前持仓'
        sqlcmd = "DROP TABLE IF EXISTS %s" % (tableName)
        cursor.execute(sqlcmd)
        sqlcmd = "CREATE TABLE %s (secname TEXT, security TEXT, positions FLOAT, price FLOAT)" % (tableName)
        cursor.execute(sqlcmd)
        # 获取所有该策略持仓过的股票列表
        cursor.execute("SELECT security FROM orders WHERE policyName=? AND accountNo=? AND marketCode=? GROUP BY security", (policyname, accountNo, marketCode,))
        securitylist = [list(item)[0] for item in cursor.fetchall()]
        for i in range(len(securitylist)):
            # 找出相应股票的最新一次订单
            cursor.execute("SELECT secname, security, positions, price FROM orders WHERE security=? AND policyName=? AND accountNo=? AND marketCode=? ORDER BY tradeTime DESC LIMIT 0,1", (securitylist[i], policyname, accountNo, marketCode,))
            line1st = cursor.fetchone()
            if line1st[2] > 0:
                sqlcmd = "INSERT INTO %s (secname, security, positions, price) VALUES (?, ?, ?, ?)" % (tableName)
                cursor.execute(sqlcmd, (line1st[0], line1st[1], line1st[2], line1st[3]))
        # 找出最新交易日订单
        #cursor.execute("SELECT tradeTime FROM orders WHERE policyName=? AND accountNo=? AND marketCode=? ORDER BY tradeTime DESC LIMIT 0,1", (policyname, accountNo, marketCode,))
        #line1st = cursor.fetchone()
        #lastorderdate = line1st[0][:10]
        lastorderdate = tradedatetime[:10]
        tableName = policyname + '_' + accountNo + '_' + marketCode + '_最新下单'
        sqlcmd = "DROP TABLE IF EXISTS %s" % (tableName)
        cursor.execute(sqlcmd)
        sqlcmd = "CREATE TABLE %s AS SELECT tradeTime, secname, security, positions, price FROM orders WHERE policyName=? AND accountNo=? AND marketCode=? AND tradeTime>=?" % (tableName)
        cursor.execute(sqlcmd, (policyname, accountNo, marketCode, lastorderdate))
        cursor.close()
        conn.commit()
        conn.close()
    except:
        logger.error("订单数据库操作失败")

    try:
        # 连接到SQLite数据库
        conn = sqlite.connect('/var/www/autotrader/sqlite3/mailtoclients.db')
        # 创建一个Cursor
        cursor = conn.cursor()
        # 秘钥
        cursor.execute("PRAGMA KEY='autotrader@8'")
        # 查询收件人表数据结构
        cursor.execute('PRAGMA table_info(receivers)')
        receiversstruct = [list(item)[1] for item in cursor.fetchall()]
        # 执行收件人表查询语句
        cursor.execute('SELECT * FROM receivers WHERE enabled=?', ('1',))
        receiversdata = cursor.fetchall()
        
        for i in range(len(receiversstruct)):
            if receiversstruct[i] == 'address':
                receivers = [list(item)[i] for item in receiversdata]
                break

        mail_msg = """<p>策略名称：%s</p><p>调仓日期：%s</p><p>股票名称：%s</p><p>股票代码：%s</p><p>目标仓位：%.4f%%</p><p>目标价格：%.2f</p>""" %(policyname, tradedatetime, secname, security, value*100, price)
        recvstr = ""
        for str in receivers:
            recvstr = recvstr + str + ','
        # 删除最后一个逗号
        recvstr = recvstr[:-1]
        logger.debug("邮件信息存入客户邮件数据库：%s, %s" % (mail_msg, recvstr))
        cursor.execute('INSERT INTO mails (content, receivers) VALUES (?, ?)', (mail_msg, recvstr))

        cursor.close()
        conn.commit()
        conn.close()
    except:
        logger.error("客户邮件数据库操作失败")

if __name__ == '__main__':
    app.run(host='0.0.0.0')

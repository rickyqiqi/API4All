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
import sqlite3

app = Flask(__name__)

reload(sys)
sys.setdefaultencoding('utf-8')

logging.config.fileConfig("/var/www/autotrader/logger.conf")
logger = logging.getLogger("main")
telegramlogger = logging.getLogger("telegram")

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

                accountpasswds = {"19780112": "W2Qa9~wc01]lk>3,@jq"}
                # check if the account NO. is valid
                if json_decode["accountNo"] in accountpasswds.keys():
                    # calculate the md5 value
                    m2 = hashlib.md5()
                    plainpasswd = str(json_decode["timestamp"]) + str(json_decode["rand"]) + accountpasswds[json_decode["accountNo"]]
                    m2.update(plainpasswd)
                    if json_decode["password"] == m2.hexdigest():
                        if json_decode["marketCode"] == "cn":
                            ret = True
                            logger.debug("%s - To set stock %s (%s) to value %.4f, recommended price: %.2f, orderID: %d" \
                                  %(json_decode["policyName"], json_decode["secname"], json_decode["security"], json_decode["value"]*100, json_decode["price"], json_decode["orderId"]))
                            # mail information to database
                            mail_to_db(json_decode["policyName"], json_decode["security"], json_decode["secname"], json_decode["value"], json_decode["price"], json_decode["txnTime"])
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

def mail_to_db(policyname, security, secname, value, price, tradedatetime):
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect('/var/www/autotrader/sqlite3/mailtoclients.db')
        # 创建一个Cursor
        cursor = conn.cursor()
        # 查询收件人表数据结构
        cursor.execute('pragma table_info(receivers)')
        receiversstruct = [list(item)[1] for item in cursor.fetchall()]
        # 执行收件人表查询语句
        cursor.execute('select * from receivers where enabled=?', ('1',))
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
        cursor.execute('insert into mails (content, receivers) values (?, ?)', (mail_msg, recvstr))

        cursor.close()
        conn.commit()
        conn.close()
    except:
        logger.error("客户邮件数据库操作失败")

if __name__ == '__main__':
    app.run(host='0.0.0.0')

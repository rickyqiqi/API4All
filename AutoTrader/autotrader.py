#coding=utf-8

import types
import time
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

app = Flask(__name__)

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
                            logger.debug("To set stock %s (%s) to value %.4f, recommended price: %.2f, orderID: %d" \
                                  %(json_decode["secname"], json_decode["security"], json_decode["value"]*100, json_decode["price"], json_decode["orderId"]))

                            security = json_decode["security"]
                            secname = json_decode["secname"]
                            value = json_decode["value"]
                            price = json_decode["price"]
                            tradedatetime = json_decode["txnTime"]
                            mail_to_clients(security, secname, value, price, tradedatetime, '小市值策略改进版')

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

def mail_to_clients(security, secname, value, price, tradedatetime, policyname):
    # 第三方 SMTP 服务
    mail_host=""  #设置服务器
    mail_user=""    #用户名
    mail_pass=""   #口令
    sender = ""
    receivers = []  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

    mailinfofile = 'config/maillist.conf'
    try:
        fp = open(mailinfofile, 'r')
        jsoncontent = fp.read()
        fp.close()
        content = json.loads(jsoncontent)

        if 'smtphost' in content:
            mail_host = content["smtphost"]
        if 'account' in content:
            mail_user = content["account"]
        if 'password' in content:
            mail_pass = content["password"]
        if 'sender' in content:
            sender = content["sender"]
        if 'receivers' in content:
            receivers = content["receivers"]
    except:
        logger.error("配置文件%s读取错误" %(mailinfofile))

    if mail_host == "":
        logger.error("SMTP主机配置空")
        return
    elif mail_user == "":
        logger.error("邮件发送账户空")
        return
    elif len(receivers) == 0:
        logger.error("邮件接受列表空")
        return

    mail_msg = """<p>策略名称：%s</p><p>调仓日期：%s</p><p>股票名称：%s</p><p>股票代码：%s</p><p>目标仓位：%.4f%%</p><p>目标价格：%.2f</p>""" %(policyname, tradedatetime.strftime("%Y-%m-%d %H:%M:%S"), secname, security, value*100, price)

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
            smtpObj.login(mail_user,mail_pass)
            smtpObj.sendmail(sender, item, message.as_string())
            smtpObj.quit()
            logger.info("邮件发送成功")
        except smtplib.SMTPException:
            logger.error("无法发送邮件")

if __name__ == '__main__':
    app.run(host='0.0.0.0')

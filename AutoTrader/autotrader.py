#coding=utf-8

import types
import time
import hashlib
import random
import json
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
        if 'timestamp' in json_decode \
          and type(json_decode["timestamp"]) == types.IntType \
          and 'rand' in json_decode \
          and type(json_decode["rand"]) == types.IntType \
          and 'status' in json_decode \
          and type(json_decode["status"]) == types.IntType:
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
        else:
            # response with parameters error
            response_data["txnCode"] = 1
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
        if 'timestamp' in json_decode \
          and type(json_decode["timestamp"]) == types.IntType \
          and 'rand' in json_decode \
          and type(json_decode["rand"]) == types.IntType \
          and 'accountNo' in json_decode \
          and type(json_decode["accountNo"]) == types.UnicodeType \
          and 'password' in json_decode \
          and type(json_decode["password"]) == types.UnicodeType \
          and 'marketCode' in json_decode \
          and type(json_decode["marketCode"]) == types.UnicodeType \
          and 'txnTime' in json_decode \
          and type(json_decode["txnTime"]) == types.UnicodeType \
          and 'security' in json_decode \
          and type(json_decode["security"]) == types.UnicodeType \
          and 'secname' in json_decode \
          and type(json_decode["secname"]) == types.UnicodeType \
          and 'value' in json_decode \
          and (type(json_decode["value"]) == types.FloatType or type(json_decode["value"]) == types.IntType) \
          and 'price' in json_decode \
          and (type(json_decode["price"]) == types.FloatType or type(json_decode["price"]) == types.IntType) \
          and 'orderId' in json_decode \
          and type(json_decode["orderId"]) == types.IntType:
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
        else:
            # response with parameters error
            response_data["txnCode"] = 1
            logger.error('Item or item type error in json string')
    else :
        # response with parameters error
        response_data["txnCode"] = 1
        logger.error('Json string error')

    response_data["timestamp"] = int(time.time())
    response_data["rand"] = random.randrange(-2147483647, 2147483647)
    json_response = json.dumps(response_data)
    telegramlogger.info(request.host + ' ==> ' + request.remote_addr + ': ' + json_response)
    return json_response

if __name__ == '__main__':
    app.run(host='0.0.0.0')

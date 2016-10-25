#coding=utf-8

import time
import hashlib
import random
import json
import urllib
import urllib2

# config.py
# inform autotrader
def autotrader_stock_trade(stockinfolist):
    msg_data = {"timestamp": 0, "rand": 0, "terminalId": "", "password": "", "tradeSN": 301005, "txnTime": "", "stocksInfo": []}
    terminalpasswds = {"600001": "W2Qa9~wc01]lk>3,@jq"}

    msg_data["timestamp"] = int(time.time())
    msg_data["rand"] = random.randrange(-2147483647, 2147483647)
    msg_data["terminalId"] = "600001"
    # calculate the md5 value
    m1 = hashlib.md5()
    plainpasswd = str(msg_data["timestamp"]) + str(msg_data["rand"]) + terminalpasswds[msg_data["terminalId"] ]
    m1.update(plainpasswd)
    msg_data["password"] = m1.hexdigest()
    msg_data["tradeSN"] = 301005
    msg_data["txnTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    msg_data["stocksInfo"] = stockinfolist

    json_data = json.dumps(msg_data)

    requrl = 'http://139.196.50.19:5000/stocktrade'
    req = urllib2.Request(url = requrl, data = json_data)
    res_data = urllib2.urlopen(req)
    response = res_data.read()
    # get the json request string
    json_decode = json.loads(response)
    if 'timestamp' in json_decode \
      and 'rand' in json_decode \
      and 'txnCode' in json_decode:
        # if current time and request time stamp in range
        currenttime = int(time.time())
        responsetime = json_decode['timestamp']
        if abs(currenttime-responsetime) > 10:
            # response with time stamp error
            print('Response time stamp %d out of range' %responsetime)
        else:
            return json_decode["txnCode"]
    return 1
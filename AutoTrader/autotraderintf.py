#coding=utf-8

import types
import time
import hashlib
import random
import json
import urllib
import urllib2

# autotraderintf.py
# inform autotrader
# security: 股票代码
# filled: 要成交的股票数量
# price: 平均成交价格, 已经成交的股票的平均成交价格(一个订单可能分多次成交)
# order_id: 订单ID
# 返回值：响应码
def autotrader_stock_trade(security, filled, price, orderid):
    msg_data = {}
    terminalpasswds = {"19780112": "W2Qa9~wc01]lk>3,@jq"}

    msg_data["timestamp"] = int(time.time())
    msg_data["rand"] = random.randrange(-2147483647, 2147483647)
    msg_data["terminalId"] = "19780112"
    # calculate the md5 value
    m1 = hashlib.md5()
    plainpasswd = str(msg_data["timestamp"]) + str(msg_data["rand"]) + terminalpasswds[msg_data["terminalId"] ]
    m1.update(plainpasswd)
    msg_data["password"] = m1.hexdigest()
    msg_data["txnTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    msg_data["security"] = security
    msg_data["filled"] = filled
    msg_data["price"] = price
    msg_data["orderId"] = orderid

    json_data = json.dumps(msg_data)

    requrl = 'http://139.196.50.19:5000/stocktrade'
    req = urllib2.Request(url = requrl, data = json_data)
    res_data = urllib2.urlopen(req)
    response = res_data.read()
    # get the json request string
    json_decode = json.loads(response)
    if 'timestamp' in json_decode \
      and type(json_decode["timestamp"]) == types.IntType \
      and 'rand' in json_decode \
      and type(json_decode["rand"]) == types.IntType \
      and 'txnCode' in json_decode \
      and type(json_decode["rand"]) == types.IntType:
        # if current time and request time stamp in range
        currenttime = int(time.time())
        responsetime = json_decode['timestamp']
        if abs(currenttime-responsetime) > 10:
            # response with time stamp error
            print('Response time stamp %d out of range' %responsetime)
        else:
            return json_decode["txnCode"]
    return 1 # inform parameter error

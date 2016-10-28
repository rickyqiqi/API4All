#coding=utf-8

import types
import time
import hashlib
import random
import json
import urllib
import urllib2
from kuanke.user_space_api import *

# autotraderintf.py
# autotrader股票记录交易
# security: 股票代码
# value: 股票仓位总值
# price: 平均成交价格, 已经成交的股票的平均成交价格(一个订单可能分多次成交)
# order_id: 订单ID
# 返回值：无
def autotrader_stock_trade(security, value, price, orderid):
    msg_data = {}

    terminalpasswds = {"19780112": "W2Qa9~wc01]lk>3,@jq"}

    msg_data["timestamp"] = int(time.time())
    msg_data["rand"] = random.randrange(-2147483647, 2147483647)
    msg_data["terminalId"] = "19780112"
    # calculate the md5 value
    m1 = hashlib.md5()
    plainpasswd = str(msg_data["timestamp"]) + str(msg_data["rand"]) + terminalpasswds[msg_data["terminalId"]]
    m1.update(plainpasswd)
    msg_data["password"] = m1.hexdigest()
    msg_data["txnTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    msg_data["security"] = security
    msg_data["value"] = value
    msg_data["price"] = price
    msg_data["orderId"] = orderid

    json_data = json.dumps(msg_data)

    # record offline json data
    add_record_offline("stocktrade", json_data)
    # do record offline
    do_record_offline()

# autotrader离线股票记录交易
# 返回值：无
def do_record_offline():
    # 检查离线记录文件是否有未完成的离线交易
    record_offline = get_record_offline()
    if record_offline != None:
        log.info("记录类型: %s， 记录内容：%s" %(record_offline[0], record_offline[1]))
        # 重发离线交易记录
        if record_offline[0] == "stocktrade":
            requrl = 'http://139.196.50.19:5000/stocktrade'
            log.info("URL: %s" %(requrl))

            msg_data = json.loads(record_offline[1])

            terminalpasswds = {"19780112": "W2Qa9~wc01]lk>3,@jq"}

            msg_data["timestamp"] = int(time.time())
            msg_data["rand"] = random.randrange(-2147483647, 2147483647)
            # calculate the md5 value
            m1 = hashlib.md5()
            plainpasswd = str(msg_data["timestamp"]) + str(msg_data["rand"]) + terminalpasswds[msg_data["terminalId"]]
            m1.update(plainpasswd)
            msg_data["password"] = m1.hexdigest()

            json_data = json.dumps(msg_data)
            log.info("Request: %s" %(json_data))

            txncode = 1
            try:
                req = urllib2.Request(url = requrl, data = json_data)
                res_data = urllib2.urlopen(req)
                response = res_data.read()
                log.info("Response: %s" %(response))

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
                        log.error('响应时间戳(%d)超时' %responsetime)
                    else:
                        txncode = json_decode["txnCode"]
                        log.info("Autotrader响应值：%d" %(txncode))
            except:
                log.error('autotrader服务器通信失败')
            # delete the offline json data if response OK
            if txncode == 0:
                # 删除这条离线记录
                rm_1st_record_offline()
        else:
            # 未知类型交易记录，直接删除
            log.error('删除未知记录类型: %s, 记录内容：%s' %(record_offline[0], record_offline[1]))
            rm_1st_record_offline()

# 增加离线记录
# recordtype: 记录类型
# jsonrequest: 记录json请求
# 返回值：无
def add_record_offline(recordtype, jsonrequest):
    pathname = "data/offline/"
    filename = pathname + "record.json"
    stocktradeoff = recordtype + "," + jsonrequest + "\n"
    content = ""
    try:
        orgcontent = read_file(filename)
        contentOK = False
        if len(orgcontent) > 32:
            data = orgcontent[:-32]
            signature = orgcontent[-32:]
            # calculate the md5 value
            m1 = hashlib.md5()
            m1.update(data)
            # check if md5 ok
            # use orignal content + new content if OK
            # backup the corrupted file and
            if signature == m1.hexdigest():
                content = data
                contentOK = True
        # check if file content check is not OK
        if not contentOK and orgcontent != "":
            log.error("离线交易记录文件(%s)数据异常" %(filename))
            try:
                write_file(filename+".bak", orgcontent)
            except:
                log.error("写备份离线交易记录文件(%s)错误" %(filename))
            content = ""
    except:
        pass

    # add new transaction content and new md5 string in
    content += stocktradeoff
    m2 = hashlib.md5()
    m2.update(content)
    content += m2.hexdigest()
    try:
        write_file(filename, content)
    except:
        log.error("写离线交易记录文件(%s)错误" %(filename))

# 获取一条离线记录
# 返回值：记录字符串
def get_record_offline():
    pathname = "data/offline/"
    filename = pathname + "record.json"
    content = ""
    try:
        orgcontent = read_file(filename)
        contentOK = False
        if len(orgcontent) > 32:
            data = orgcontent[:-32]
            signature = orgcontent[-32:]
            # calculate the md5 value
            m1 = hashlib.md5()
            m1.update(data)
            # check if md5 ok
            # use orignal content + new content if OK
            # backup the corrupted file and
            if signature == m1.hexdigest():
                content = data
                contentOK = True
        # check if file content check is not OK
        if not contentOK and orgcontent != "":
            log.error("离线交易记录文件(%s)数据异常" %(filename))
            try:
                write_file(filename+".bak", orgcontent)
            except:
                log.error("写备份离线交易记录文件(%s)错误" %(filename))
            content = ""
    except:
        pass

    result = None
    if content != "":
        # find the end of 1st line
        content = content[:content.index('\n')]
        npos = content.index(',')
        result = content[:npos], content[npos+1:]

    return result

# 删除第一条离线记录
# 返回值：无
def rm_1st_record_offline():
    pathname = "data/offline/"
    filename = pathname + "record.json"
    content = ""
    try:
        orgcontent = read_file(filename)
        contentOK = False
        if len(orgcontent) > 32:
            data = orgcontent[:-32]
            signature = orgcontent[-32:]
            # calculate the md5 value
            m1 = hashlib.md5()
            m1.update(data)
            # check if md5 ok
            # use orignal content + new content if OK
            # backup the corrupted file and
            if signature == m1.hexdigest():
                content = data
                contentOK = True
        # check if file content check is not OK
        if not contentOK and orgcontent != "":
            log.error("离线交易记录文件(%s)数据异常" %(filename))
            try:
                write_file(filename+".bak", orgcontent)
            except:
                log.error("写备份离线交易记录文件(%s)错误" %(filename))
            content = ""
    except:
        log.info("离线交易记录文件(%s)不存在" %(filename))

    if content != "":
        # find the end of 1st line
        nPos = content.index('\n')
        # check if it's not the last line in file
        if nPos+1 < len(content):
            # store the data left back into the file
            dataleft = content[nPos+1:]
            m3 = hashlib.md5()
            m3.update(content)
            dataleft += m3.hexdigest()
            try:
                write_file(filename, dataleft)
            except:
                log.error("写离线交易记录文件(%s)错误" %(filename))
        else:
            # last line read out, store a blank file
            try:
                write_file(filename, "")
            except:
                log.error("写离线交易记录文件(%s)错误" %(filename))

# 删除所有离线记录
# 返回值：无
def rm_all_records_offline():
    pathname = "data/offline/"
    filename = pathname + "record.json"
    try:
        orgcontent = read_file(filename)
        contentOK = False
        if len(orgcontent) > 32:
            log.error("离线交易记录文件(%s)准备删除" %(filename))
    except:
        pass
    # store a blank file
    try:
        write_file(filename, "")
    except:
        log.error("写离线交易记录文件(%s)错误" %(filename))
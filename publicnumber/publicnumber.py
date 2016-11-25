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

logging.config.fileConfig("/var/www/publicnumber/logger.conf")
logger = logging.getLogger("main")
telegramlogger = logging.getLogger("telegram")

@app.route('/publicnumber/checksignature', methods=['GET'])
def checkSignature():
    query_str = ""
    if request.query_string != "":
        query_str = '/' + str(request.query_string)
    telegramlogger.info(request.remote_addr + ' ==> ' + request.host + request.path + query_str + ': ' + str(request.form.keys()))
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    random = request.args.get('nonce', '')
    token = '<Quant=+[888]+=Policy>'

    tmpdict = [token, timestamp, random]
    tmpdict.sort()
    logger.info(str(tmpdict))
    tmpstr = str(tmpdict[0]) + str(tmpdict[1]) + str(tmpdict[2])
    logger.info(tmpstr)
    sha1value = hashlib.sha1(tmpstr)
    logger.info(str(sha1value))
    sha1str = sha1value.hexdigest()
    logger.info(sha1str)

    response = ""
    if sha1str == signature:
        response = request.args.get('echostr', '')

    telegramlogger.info(request.host + ' ==> ' + request.remote_addr + ': ' + response)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0')

import time
import random
import json
from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/stocktrade', methods=['POST'])
def stocktrade():
    # uncoded response data
    response_data = {"timestamp": 0, "rand": 0, "txnCode": -1}
    # request json string is in keys
    keys = request.form.keys()

    jsonstrOK = True
    # check if there's only 1 json string key
    if len(keys) == 1:
        # get the json request string
        json_decode = json.loads(keys[0])
        if 'timestamp' in json_decode \
          and 'rand' in json_decode \
          and 'terminalId' in json_decode \
          and 'password' in json_decode \
          and 'tradeSN' in json_decode \
          and 'txnTime' in json_decode \
          and 'stocksInfo' in json_decode:
            # if current time and request time stamp in range
            currenttime = int(time.time())
            requesttime = json_decode['timestamp']
            if abs(currenttime-requesttime) > 10:
                jsonstrOK = False
                print('Request time stamp %d out of range' %requesttime)
            else:
                print('request: %d, local: %d' %(requesttime, currenttime))
                # response with success
                response_data["txnCode"] = 0
        else:
            jsonstrOK = False
    else :
        jsonstrOK = False

    if not jsonstrOK:
        # response with parameters error
        response_data["txnCode"] = 1
    response_data["timestamp"] = int(time.time())
    response_data["rand"] = random.randrange(-2147483647, 2147483647)
    return json.dumps(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

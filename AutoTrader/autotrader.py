import time
import hashlib
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
                # response with time stamp error
                response_data["txnCode"] = 2
                print('Request time stamp %d out of range' %requesttime)
            else:
                if requesttime != currenttime:
                    print('Server time is different - request: %d, local: %d' %(requesttime, currenttime))

                terminalpasswds = {"600001": "W2Qa9~wc01]lk>3,@jq"}
                # check if the terminal id is valid
                if json_decode["terminalId"] in terminalpasswds.keys():
                    # calculate the md5 value
                    m2 = hashlib.md5()
                    plainpasswd = str(json_decode["timestamp"]) + str(json_decode["rand"]) + terminalpasswds[json_decode["terminalId"]]
                    m2.update(plainpasswd)
                    if json_decode["password"] == m2.hexdigest():
                        ret = True
                        for stockinfo in json_decode["stocksInfo"]:
                            if 'stockCode' in stockinfo \
                              and 'position' in stockinfo \
                              and 'price' in stockinfo:
                                print("To set stock %s to position %d, recommended price: %.2f" \
                                      %(stockinfo["stockCode"], stockinfo["position"], stockinfo["price"]))
                            else:
                                ret = False
                                break
                        if ret:
                            # response with success
                            response_data["txnCode"] = 0
                        else:
                            # response with parameters error
                            response_data["txnCode"] = 1
                    else:
                        # response with password error
                        response_data["txnCode"] = 7
                        print('Password error')
                else:
                    # response with terminal invalid
                    response_data["txnCode"] = 6
                    print('Invalid terminal')
        else:
            # response with parameters error
            response_data["txnCode"] = 1
    else :
        # response with parameters error
        response_data["txnCode"] = 1

    response_data["timestamp"] = int(time.time())
    response_data["rand"] = random.randrange(-2147483647, 2147483647)
    return json.dumps(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

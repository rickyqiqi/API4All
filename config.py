#coding=utf-8

import json
from kuanke.user_space_api import *

# config.py
# 获取备选股票
def get_candidates():
    # 是否使用指数池选股配置
    indexStock2Select = False
    # 备选股票池，空表示所有股票备选
    candidates = []
    # 指数池，默认沪深300指数
    indexpool = ["000300.XSHG", "000905.XSHG"]
    # 配置文件名称
    if g.real_market_simulate:
        configfilename = 'realmarket.conf'
    else:
        configfilename = 'loopback.conf'

    try:
        jsoncontent = read_file(configfilename)
        content = json.loads(jsoncontent)

        if 'indexStock2Select' in content:
            indexStock2Select = content["indexStock2Select"]
        if 'candidates' in content:
            candidates = content["candidates"]
        if 'indexpool' in content:
            indexpool = content["indexpool"]
    except:
        log.error("配置文件%s读取错误" %(configfilename))

    log.info("是否使用指数池选股配置: %s" %(indexStock2Select))
    log.info("备选股票池: %s" %(str(candidates)))
    log.info("指数池: %s" %(str(indexpool)))

    if indexStock2Select:
        for index in indexpool:
            candidates += get_index_stocks(index)
    else:
        if len(candidates) == 0:
            candidates = list(get_all_securities(['stock']).index)

    return candidates
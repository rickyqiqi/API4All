#coding=utf-8

import types
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

# 获取配置值
def get_variables_updated(addstring):
    # 配置值文件
    if g.real_market_simulate:
        configfilename = 'varreal%s.conf' %(addstring)
    else:
        configfilename = 'varloop%s.conf' %(addstring)

    try:
        jsoncontent = read_file(configfilename)
        content = json.loads(jsoncontent)

        if 'version' in content and type(content["version"]) == types.FloatType:
            version = content["version"]
            # 更新初始化函数里的赋值
            if version > g.version:
                # 需更新的数值写在这
                if 'g.is_rank_stock_score_plus_allowed' in content and type(content["g.is_rank_stock_score_plus_allowed"]) == types.BooleanType:
                    g.is_rank_stock_score_plus_allowed = content["g.is_rank_stock_score_plus_allowed"]
                if 'g.buy_stock_count' in content and type(content["g.buy_stock_count"]) == types.IntType:
                    g.buy_stock_count = content["g.buy_stock_count"]
                if 'g.is_stop_loss_by_portfolio_loss_rate' in content and type(content["g.is_stop_loss_by_portfolio_loss_rate"]) == types.BooleanType:
                    g.is_stop_loss_by_portfolio_loss_rate = content["g.is_stop_loss_by_portfolio_loss_rate"]
                if 'g.is_mail_inform_enabled' in content and type(content["g.is_mail_inform_enabled"]) == types.BooleanType:
                    g.is_mail_inform_enabled = content["g.is_mail_inform_enabled"]
                if 'g.is_autotrader_inform_enabled' in content and type(content["g.is_autotrader_inform_enabled"]) == types.BooleanType:
                    g.is_autotrader_inform_enabled = content["g.is_autotrader_inform_enabled"]

                g.version = version
                return True
    except:
        log.error("配置文件%s读取错误" %(configfilename))

    return False
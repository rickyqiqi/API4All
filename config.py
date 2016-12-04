#coding=utf-8

import types
import json
from kuanke.user_space_api import *

# 获取配置值
def get_variables_updated(addstring):
    # 配置值文件
    if g.real_market_simulate:
        configfilename = 'config/varreal%s.conf' %(addstring)
    else:
        configfilename = 'config/varloop%s.conf' %(addstring)

    try:
        jsoncontent = read_file(configfilename)
        content = json.loads(jsoncontent)

        if content.has_key('version') and type(content["version"]) == types.FloatType:
            version = content["version"]
            # 更新初始化函数里的赋值
            if version > g.version:
                # 需更新的数值写在这
                if content.has_key('g.is_rank_stock_score_plus_allowed') and type(content["g.is_rank_stock_score_plus_allowed"]) == types.BooleanType:
                    g.is_rank_stock_score_plus_allowed = content["g.is_rank_stock_score_plus_allowed"]
                if content.has_key('g.buy_stock_count') and type(content["g.buy_stock_count"]) == types.IntType:
                    g.buy_stock_count = content["g.buy_stock_count"]
                if content.has_key('g.is_stop_loss_by_portfolio_loss_rate') and type(content["g.is_stop_loss_by_portfolio_loss_rate"]) == types.BooleanType:
                    g.is_stop_loss_by_portfolio_loss_rate = content["g.is_stop_loss_by_portfolio_loss_rate"]
                if content.has_key('g.is_mail_inform_enabled') and type(content["g.is_mail_inform_enabled"]) == types.BooleanType:
                    g.is_mail_inform_enabled = content["g.is_mail_inform_enabled"]
                if content.has_key('g.is_autotrader_inform_enabled') and type(content["g.is_autotrader_inform_enabled"]) == types.BooleanType:
                    g.is_autotrader_inform_enabled = content["g.is_autotrader_inform_enabled"]
                if content.has_key('g.stock_candidates') and type(content["g.stock_candidates"]) == types.ListType:
                    g.stock_candidates = content["g.stock_candidates"]
                if content.has_key('g.index_stock_2_select') and type(content["g.index_stock_2_select"]) == types.BooleanType:
                    g.index_stock_2_select = content["g.index_stock_2_select"]
                if content.has_key('g.index_pool') and type(content["g.index_pool"]) == types.ListType:
                    g.index_pool = content["g.index_pool"]
                if content.has_key('g.blacklist') and type(content["g.blacklist"]) == types.ListType:
                    g.blacklist = content["g.blacklist"]
                if content.has_key('g.indebug' ) and type(content["g.indebug"]) == types.BooleanType:
                    g.indebug = content["g.indebug"]
                if content.has_key('g.large_market_share_index_pool_used' ) and type(content["g.large_market_share_index_pool_used"]) == types.BooleanType:
                    g.large_market_share_index_pool_used = content["g.large_market_share_index_pool_used"]
                if content.has_key('g.large_market_share_index') and type(content["g.large_market_share_index"]) == types.UnicodeType:
                    g.large_market_share_index = content["g.large_market_share_index"]
                if content.has_key('g.large_market_share_trend_judge_param') and type(content["g.large_market_share_trend_judge_param"]) == types.FloatType:
                    g.large_market_share_trend_judge_param = content["g.large_market_share_trend_judge_param"]

                g.version = version
                return True
    except:
        log.error("配置文件%s读取错误" %(configfilename))

    return False

# 配置股票黑名单
# 列出当且极不适宜购买的股票
# 注：1. 黑名单有时效性，回测的时候最好不使用，模拟交易建议使用
#     2. 用一模块或者大数据分析收集这类股票，定时更新
def get_blacklist(context):
    list_In_Effective = []
    # 根据当天日期取得当日有效黑名单列表
    for list in g.blacklist:
        if context.current_dt >= datetime.datetime.strptime(list['start_date'],'%Y-%m-%d') and context.current_dt < datetime.datetime.strptime(list['end_date'],'%Y-%m-%d'):
            list_In_Effective += list['stock_list']
            
    return list_In_Effective
#策略概述：《小市值策略改进版》
#https://www.joinquant.com/post/2035?tag=new
#1.选择eps>0的所有股票，按市值从小到大排序，选择前100支候选
#2.剔除创业板，ST,*,退，停牌等股票
#3.选择市值最小的20只（前20只）候选
#4.给候选股票评分, 每天下午2点50分执行。
#lowPrice130 = 前130天内最低价格
#highPrice130 = 前130天内最高价格
#avg15 = 前15天均价
#currPrice = 当前价格
#score = ((currPrice-lowPrice130)+(currPrice-highPrice130)+(currPrice-avg15))/currPrice
#5.将候选股票的score得分，从小到大排序。选择最小的4支持仓。
#6.持股3天轮换，如果一样的就继续持有，不一样的就换掉。
#7.大盘止损使用上证50，与中小板R 指数。如果都小于20天前的101%，则清空仓位不交易。
################################################################################
#2016/8/9
#关于止损策略，我有点说漏了。
#仓位股票使用跟踪止损，每分钟监测，如果有更高价则记录之，如果从最高价回撤9.9%，则抛掉，当天14：50马上重新选股持仓。
#8.识别大盘“三只乌鸦”的形态，如果发现，当天就清仓。
################################################################################
#2016/8/13
#9.根据不同的时间段设置滑点与手续费
#10.剔除创业板
#11.删除了“三只乌鸦”形态识别
#12.修改了中小板指数替代创业板指数作为二八中的八参照
#13.增加了bstd作为个股在持仓3天内，能承受的最大跌幅判断
#14.每分钟监测股价，如果有更高价则记录之，如果从最高价回撤9.9%，则抛掉


import types
import json
from sqlalchemy import desc
import numpy as np
import pandas as pd
from scipy import stats
from autotraderintf import *
from mailintf import *

# 获取配置值
def get_variables_updated(context, addstring):
    valueUpdated = False
    # 配置值文件
    if g.real_market_simulate:
        configfilename = 'config/real_%s.conf' %(addstring)
    else:
        configfilename = 'config/loop_%s.conf' %(addstring)

    try:
        jsoncontent = read_file(configfilename)
        content = json.loads(jsoncontent)

        # 需更新的数值写在这
        if content.has_key('g.policy_name' ) and type(content["g.policy_name"]) == types.UnicodeType \
            and g.policy_name != content["g.policy_name"]:
            g.policy_name = content["g.policy_name"]
            valueUpdated = True
        if content.has_key('g.capitalValue') and type(content["g.capitalValue"]) == types.IntType \
            and g.capitalValue != content["g.capitalValue"]:
            # 回测或模拟盘设置阶段设置的初始总金额 - 本金总金额 = 利润
            currentProfit = (context.portfolio.total_value - g.totalValueDifference) - g.capitalValue
            g.capitalValue = content["g.capitalValue"]
            valueUpdated = True
            # 金额总差值 = 当前总值 - 新本金总金额 - 之前的利润
            g.totalValueDifference = context.portfolio.total_value - g.capitalValue - currentProfit
        if content.has_key('g.indebug' ) and type(content["g.indebug"]) == types.BooleanType \
            and g.indebug != content["g.indebug"]:
            g.indebug = content["g.indebug"]
            valueUpdated = True
        if content.has_key('g.stockCount') and type(content["g.stockCount"]) == types.IntType \
            and g.stockCount != content["g.stockCount"]:
            g.stockCount = content["g.stockCount"]
            valueUpdated = True
        if content.has_key('g.period') and type(content["g.period"]) == types.IntType \
            and g.period != content["g.period"]:
            g.period = content["g.period"]
            valueUpdated = True
        if content.has_key('g.minPE') and type(content["g.minPE"]) == types.IntType \
            and g.minPE != content["g.minPE"]:
            g.minPE = content["g.minPE"]
            valueUpdated = True
        if content.has_key('g.maxPE') and type(content["g.maxPE"]) == types.IntType \
            and g.maxPE != content["g.maxPE"]:
            g.maxPE = content["g.maxPE"]
            valueUpdated = True
        if content.has_key('g.PEG') and (type(content["g.PEG"]) == types.FloatType or type(content["g.PEG"]) == types.IntType) \
            and g.PEG != content["g.PEG"]:
            g.PEG = content["g.PEG"]
            valueUpdated = True
        if content.has_key('g.minEPS') and type(content["g.minEPS"]) == types.IntType \
            and g.minEPS != content["g.minEPS"]:
            g.minEPS = content["g.minEPS"]
            valueUpdated = True
        if content.has_key('g.minIncNetProfit') and (type(content["g.minIncNetProfit"]) == types.FloatType or type(content["g.minIncNetProfit"]) == types.IntType) \
            and g.minIncNetProfit != content["g.minIncNetProfit"]:
            g.minIncNetProfit = content["g.minIncNetProfit"]
            valueUpdated = True
        if content.has_key('g.incReturnInROE') and (type(content["g.incReturnInROE"]) == types.FloatType or type(content["g.incReturnInROE"]) == types.IntType) \
            and g.incReturnInROE != content["g.incReturnInROE"]:
            g.incReturnInROE = content["g.incReturnInROE"]
            valueUpdated = True
        #if content.has_key('g.topdropthreshold') and (type(content["g.topdropthreshold"]) == types.FloatType) \
        #    and g.topdropthreshold != content["g.topdropthreshold"]:
        #    g.topdropthreshold = content["g.topdropthreshold"]
        #    valueUpdated = True
        if content.has_key('g.recommend_freq') and type(content["g.recommend_freq"]) == types.IntType \
            and g.recommend_freq != content["g.recommend_freq"]:
            g.recommend_freq = content["g.recommend_freq"]
            valueUpdated = True
        if content.has_key('g.rank_stock_score_plus_allowed') and type(content["g.rank_stock_score_plus_allowed"]) == types.BooleanType \
            and g.rank_stock_score_plus_allowed != content["g.rank_stock_score_plus_allowed"]:
            g.rank_stock_score_plus_allowed = content["g.rank_stock_score_plus_allowed"]
            valueUpdated = True
        if content.has_key('g.autotrader_inform_enabled') and type(content["g.autotrader_inform_enabled"]) == types.BooleanType \
            and g.autotrader_inform_enabled != content["g.autotrader_inform_enabled"]:
            g.autotrader_inform_enabled = content["g.autotrader_inform_enabled"]
            valueUpdated = True
        if content.has_key('g.stock_appointed') and type(content["g.stock_appointed"]) == types.ListType \
            and g.stock_appointed != content["g.stock_appointed"]:
            g.stock_appointed = content["g.stock_appointed"]
            valueUpdated = True
        if content.has_key('g.stock_candidates') and type(content["g.stock_candidates"]) == types.ListType \
            and g.stock_candidates != content["g.stock_candidates"]:
            g.stock_candidates = content["g.stock_candidates"]
            valueUpdated = True
        if content.has_key('g.index_stock_2_select') and type(content["g.index_stock_2_select"]) == types.BooleanType \
            and g.index_stock_2_select != content["g.index_stock_2_select"]:
            g.index_stock_2_select = content["g.index_stock_2_select"]
            valueUpdated = True
        if content.has_key('g.index_pool') and type(content["g.index_pool"]) == types.ListType \
            and g.index_pool != content["g.index_pool"]:
            g.index_pool = content["g.index_pool"]
            valueUpdated = True

    except:
        log.error("配置文件%s读取错误" %(configfilename))

    return valueUpdated

def initialize(context):# 参数版本号
    # additional string in variable configuration file name
    g.addstring = "smallvalueII"

    g.policy_name = '小市值价值发掘策略'

    # 初始总金额或调整后总金额
    g.capitalValue = 50000
    # 金额总差值 = 当前总值 - 新本金总金额 - 之前的利润(0)
    g.totalValueDifference = context.portfolio.total_value - g.capitalValue

    # 是否在调试模式下
    g.indebug = False
    # 在线状态响应码
    g.online_response_code = 0

    # run_params: 表示此次运行的参数, 有如下属性
    # start_date: 回测/模拟开始日期, datetime.date对象
    # end_date: 回测/模拟结束日期, datetime.date对象
    # type: 运行方式, 如下三个字符串之一
    # 'simple_backtest': 回测, 通过点击’编译运行’运行
    # 'full_backtest': 回测, 通过点击’运行回测’运行
    # 'sim_trade': 模拟交易
    g.real_market_simulate = False
    if context.run_params.type == 'sim_trade':
        # 使用真实价格回测(模拟盘推荐如此，回测请注释)
        set_option('use_real_price', True)
        g.real_market_simulate = True

    # 加载统计模块
    g.trade_stat = trade_stat()

    g.zs1 =  '000016.XSHG' #上证50指数
    g.zs2 =  '000300.XSHG' #'000300.XSHG' #沪深300指数
    g.zs8 =  '399101.XSHE' #'159902.XSHE' #'399005.XSHE' #中小板指数

    g.lag = 20 # 回看前20天

    g.ret1 = 0
    g.ret2 = 0
    g.ret8 = 0
    g.ret_last5d = []
    g.gradient1 = 0
    g.gradient2 = 0
    g.gradient8 = 0

    # 对比标的
    set_benchmark('000300.XSHG') 
    g.stocks = []
    g.stockCount = 4
    g.buyStockCount = 10
    g.days = 0
    g.period = 3
    g.adjust_position_hour = 14
    g.adjust_position_minute = 50
    g.minPE = None
    g.maxPE = None
    g.PEG = None
    g.minEPS = 0
    g.minIncNetProfit = None
    g.incReturnInROE = None
    # 需要调仓标记
    g.todobuy = False
    g.maxrbstd = {}
    g.exceptions = []
    g.stockscrashed = []
    g.stopstocks = []
    #g.maxvalue = {} # 购买之后的最高价列表
    #g.minutesinlowprice = {} # 股价低于最高价向下降幅阈值计时（分钟）
    #g.minutesthreshold = 120 # 股价计时阈值（分钟）
    #g.topdropthreshold = 0.05 # 股价低于最高价向下降幅阈值
    g.stockrecommend = []
    g.recommend_freq = 5
    # 股票多头趋势加分项参数
    g.rank_stock_score_plus_allowed = True
    if g.rank_stock_score_plus_allowed:
        # 测试多头趋势的均线长度
        g.ma_lengths = [5,10,20,60,120]
        # 测试买入回踩的均线长度
        g.test_ma_length = 10
        # 买入时回踩但必须站住的均线
        g.stand_ma_length = 10
        # 多头趋势天数
        g.in_trend_days = 7

    # 配置是否开启autotrader通知
    g.autotrader_inform_enabled = False

    # 指定股票列表
    # "510050.XSHG" - 华夏上证50ETF
    # "160706.XSHE" - 嘉实沪深300ETF联接LOF
    # "159902.XSHE" - 华夏中小板ETF
    g.stock_appointed = []
    # 备选股票池，空表示所有股票备选
    g.stock_candidates = []
    # 是否使用指数池选股配置
    g.index_stock_2_select = False
    # 指数池
    # '000016.XSHG' - 上证50指数
    # '000300.XSHG' - 沪深300指数
    # '399005.XSHE' - 中小板指数
    g.index_pool = []

    # 打印策略参数
    log_param()

def log_param():
    log.info("---------------------------------------------")
    log.info("策略名称: %s" %(g.policy_name))
    log.info("是否是调试模式: %s" %(g.indebug))
    log.info("调仓日频率: %d日" %(g.period))
    log.info("调仓时间: %s:%s" %(g.adjust_position_hour, g.adjust_position_minute))
    log.info("初始总金额或调整后总金额: %d" %(g.capitalValue))
    log.info("买入股票数目: %d" %(g.stockCount))
    if g.maxPE != None and g.minPE != None and g.maxPE > g.minPE :
        log.info("选股PE值范围: %d~%d" %(g.minPE, g.maxPE))
    if g.PEG != None :
        log.info("选股PEG指标(市盈率相对盈利增长比率)值: %.02f%%" %(g.PEG*100))
    if g.minEPS != None :
        log.info("选股最小EPS值: %d" %(g.minEPS))
    if g.minIncNetProfit != None :
        log.info("选股最小净利润增长率值: %.02f%%" %(g.minIncNetProfit*100))
    if g.incReturnInROE != None :
        log.info("选股扣除非经常损益净资产收益率占比值: %.02f%%" %(g.incReturnInROE*100))
    #log.info("股价低于最高价向下降幅阈值: %.02f%%" %(g.topdropthreshold*100))
    log.info("推荐股票频率: %d分钟" %(g.recommend_freq))
    log.info("是否开启股票多头趋势加分: %s" %(g.rank_stock_score_plus_allowed))
    log.info("是否开启autotrader通知: %s" %(g.autotrader_inform_enabled))

    if len(g.stock_appointed) > 0:
        log.info("指定股票列表: %s" %(str(g.stock_appointed)))
    else:
        log.info("是否使用指数池选股配置: %s" %(g.index_stock_2_select))
        if g.index_stock_2_select:
            log.info("指数池: %s" %(str(g.index_pool)))
        else:
            log.info("备选股票池: %s" %(str(g.stock_candidates)))
    log.info("---------------------------------------------")

def getStockPrice(stock, interval):
    h = attribute_history(stock, interval, unit='1d', fields=('close'), skip_paused=True)
    return h['close'].values[0]

def unpaused(stockspool):
    current_data=get_current_data()
    return [s for s in stockspool if not current_data[s].paused]    

#过滤掉带*或者ST类及创业板股票
def filterStarName(stock_list):
    curr_data = get_current_data()
    return  [stock for stock in stock_list if 'ST' not in curr_data[stock].name and
        '*' not in curr_data[stock].name and '退' not in curr_data[stock].name and 
        not stock.startswith('300')]

def sell_all_stocks(context):
    for stock in context.portfolio.positions.keys():
            position = context.portfolio.positions[stock]
            close_position(context, position)
            curr_data = get_current_data()
            log.info("Sell: %s(%s)" %(curr_data[stock].name, stock))
    #很关键！第一次写程序的时候没有这一句，会造成下面的无法买入。
    g.days = 0          

# 计算买入信号
# 输入所有多头趋势股票
# 返回一list，包含所有在趋势内但是踩到测量均线的股票
def buy_signal(available_stocks, context):
    in_trend_stocks = get_in_trends(available_stocks, context)

    # 建立空list 
    signal = []
    # 对于所有多头趋势股票
    for security in in_trend_stocks:
        # 获取历史收盘价
        past_prices = attribute_history(security,g.test_ma_length, '1d', 'close', skip_paused = True)
        # 计算均线
        test_ma = sum(past_prices).iloc[0] / g.test_ma_length
        # 获取站住均线数据
        past_prices_2 = attribute_history(security, g.stand_ma_length, '1d', 'close', skip_paused= True) 
        # 计算均线
        stand_ma = sum(past_prices_2).iloc[0] / g.stand_ma_length
        # 获取昨日信息
        previous_history = attribute_history(security, 1, '1d', ['close','low'])
        # 昨日收盘价
        current_price = previous_history['close'].iloc[0]
        # 昨日最低价
        previous_low = previous_history['low'].iloc[0]
        # 如果该股票没有持仓，并且前收盘价低于目标均线
        if current_price <= test_ma :
            # 加入信号list 
            signal.append(security)
    # 输出信号
    return(signal)

# 获取所有多头趋势股票
# 输入一list有效股票
# 输出一list，为所有符合从小到长均线排列从大到小的股票
def get_in_trends(available_stocks, context):
    # 建立需要入选的股票list，只要发现股票有两根均线不符合多头趋势，就加入删除名单并停止计算
    stockselected = []
    # 对于所有有效股票
    for security in available_stocks:
        # 获取最长ma长度
        longest_ma = max(g.ma_lengths)
        # 今日日期
        date = context.current_dt
        # 获取过去价格
        all_past_prices = attribute_history(security,longest_ma + g.in_trend_days -1, '1d', 'close',  skip_paused = True)
        # 对于认定趋势的每一天
        for day in range(g.in_trend_days):
            # 筛去尾部的-day天数据
            if day == 0:
                past_prices = all_past_prices
            else:
                past_prices = all_past_prices[:-day]
            # 建立空均线值list 
            mas = []
            # 对于所有均线长度
            for length in g.ma_lengths:
                # 截取相应数据
                ma_data = past_prices[-length:]
                # 算均值
                ma = sum(ma_data).iloc[0]/ length
                # 计入list 
                mas.append(ma)
            # 从大到小排列均值list 
            sorted_mas = sorted(mas)
            sorted_mas.reverse()
            # 如果排列之后和之前不
            if mas == sorted_mas:
                # 加入入选名单行列
                stockselected.append(security)
                # 不继续进行运算
                break
    # 返回趋势股票list 
    return(stockselected)

def Multi_Select_Stocks(context, data):
    #更新排除之前被止盈止损的股票，允许其进入筛选备选股池
    for dstock in g.exceptions :
        # 当前价格相对于之前止盈、止损价格的涨跌幅度
        if (dstock['stopvalue'] != 0.0) and ((data[dstock['stock']].close-dstock['stopvalue'])/dstock['stopvalue'] > 0.15):
            g.exceptions.remove(dstock)
        elif (dstock['targetvalue'] != 0.0) and ((data[dstock['stock']].close-dstock['targetvalue'])/dstock['targetvalue'] < -0.15):
            g.exceptions.remove(dstock)

    # 指定股票列表非空，则直接返回指定股票列表
    if len(g.stock_appointed) > 0:
        return g.stock_appointed

    # 获取备选股票
    stocks = []
    # 是否使用指数池选股配置
    if g.index_stock_2_select:
        #log.info("指数股票池：%s" %(str(g.index_pool)))
        # 指数池
        for index in g.index_pool:
            stocks += get_index_stocks(index)
    else:
        # 备选股票池，空表示所有股票备选
        if len(g.stock_candidates) == 0:
            #log.info("所有股票池")
            candidates = get_all_securities(['stock'])
            #排除新股
            stocks = candidates[(context.current_dt.date() - candidates.start_date) > datetime.timedelta(60)].index
        else:
            #log.info("备选股票池: %s" %(str(g.stock_candidates)))
            stocks = g.stock_candidates

    #stocks  = stocks.index
    date=context.current_dt.strftime("%Y-%m-%d")
    st=get_extras('is_st', stocks, start_date=date, end_date=date, df=True)
    st=st.loc[date]
    stocks = list(st[st==False].index)
    stocks = unpaused(stocks)
    stocks = filterStarName(stocks)

    if g.rank_stock_score_plus_allowed:
        addscorelist = get_in_trends(stocks, context)

    q = query(valuation.code).filter(
        valuation.code.in_(stocks)
    )
    if g.maxPE != None and g.minPE != None and g.maxPE > g.minPE :
        q = q.filter(
            valuation.pe_ratio > g.minPE, 
            valuation.pe_ratio < g.maxPE
            )
    # 满足设定的PEG指标(市盈率相对盈利增长比率)
    if g.PEG != None :
        q = q.filter(
            valuation.pe_ratio < indicator.inc_net_profit_year_on_year*g.PEG,
            )
    if g.minEPS != None :
        q = q.filter(
            indicator.eps > g.minEPS,
            )
    if g.minIncNetProfit != None :
        q = q.filter(
            indicator.inc_net_profit_year_on_year > (g.minIncNetProfit*100),
            )
    # 扣除非经常损益后的净资产收益率/净资产收益率ROE需要达到一定比例
    # 即非经常损益占净资产比例不能太大
    if g.incReturnInROE != None :
        q = q.filter(
            indicator.inc_return > (indicator.roe*g.incReturnInROE),
            )
    # 按市值升序排列
    q = q.order_by(
        valuation.market_cap.asc()
    ).limit(
        # 最多返回20个
        20
    )
    df = get_fundamentals(q)
    stocks = df.code.values

    stock_select={}
    for s in stocks:
        #排除之前被止盈止损的股票
        skipit = False
        for dstock in g.exceptions :
            if dstock['stock'] == s :
                skipit = True
                break
        if skipit:
            log.info('排除之前被止盈止损的股票')
            log.info('%s' %(s))
            continue

        #排除符合止盈止损条件的股票
        if stock_monitor(context, data, s) != 'NormalProfit':
            continue
#        # 排除当天下跌幅度过大并出现下跌趋势的股票
#        if isStockBearish(s , data, 15, 0.03, 0.02) :
#            continue

        #排除现价涨停且未持有(已持有的涨停股继续持有)、跌停的股票
        if (data[s].close <= data[s].low_limit) or ((data[s].close >= data[s].high_limit) and (s not in context.portfolio.positions.keys())) :
            continue

        h = attribute_history(s, 130, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        lowPrice130 = h.low.min()
        highPrice130 = h.high.max()
        avg15 = data[s].mavg(15)
        currPrice = data[s].close
        #score = (currPrice-lowPrice130)+(currPrice-highPrice130)+(currPrice-avg15)
        score = ((currPrice-lowPrice130)+(currPrice-highPrice130)+(currPrice-avg15))/currPrice
        if g.rank_stock_score_plus_allowed:
            if s in addscorelist :
                score -= 0.08
        stock_select[s] = score

    # 确保有股票被选中
    if len(stock_select) > 0 :
        dfs = pd.DataFrame(stock_select.values(),index=stock_select.keys())
        dfs.columns=['score']
        dfs=dfs.sort(columns='score',ascending=True)
        return dfs.index[:g.stockCount].values.tolist()

    # 返回空列表
    return []

def stock_monitor(context, data, stock):
    # maxd = 个股250天内最大的3日跌幅
    # avgd = 个股250天内平均的3日跌幅
    # bstd = (maxd+avgd)/2, 此bstd即为个股在持仓3天内，能承受的最大跌幅
    # maxr = 个股250天内最大的3日涨幅，个股盈利超过其历史值maxr的时候，则立刻清仓止盈
    h = attribute_history(stock, 250, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
    maxr = 0.00
    maxd = 0.00
    avgd = 0.00
    dcount = 0
    for i in range(1, len(h)-3):
        # 个股连续3日涨跌幅
        dr3days = 0.00
        if (not isnan(h.close[i+2])) and (not isnan(h.close[i-1])):
            dr3days = (h.close[i+2]-h.close[i-1])/h.close[i-1]
        if dr3days > maxr:
            maxr = dr3days
        if dr3days < maxd:
            maxd = dr3days
        if dr3days < 0:
            avgd += dr3days
            dcount += 1
    if dcount > 0 :
        avgd = avgd/dcount
    bstd = (maxd+avgd)/2

    # 当前价格超出止盈止损值，则卖出该股票
    dr3cur = (data[stock].close-h.close[-2])/h.close[-2]
    if dr3cur >= maxr:
        return 'TargetProfitArrived'
    if dr3cur <= bstd:
        return 'StopProfitArrived'
    return 'NormalProfit'

def isStockBearish(stock, data, interval, breakrate=0.03, lastbreakrate=0.02):
    h = attribute_history(stock, interval, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
    # 当前价格相比当日最高价或前一日收盘价下跌3%以上
    if (not isnan(h['close'].values[-1])) and (data[stock].close < (1-breakrate)*min(h['close'].values[-1], data[stock].high)) :
        breakout = True
        for i in range(1, interval) :
            # 当前价格低于前几日中某个超过2%阴线下跌日（收盘价低于最高价2%以上，或低于前日收盘价2%以上）的最低价，且该日之后几天未有效突破该日最高价
            if (not isnan(h['close'].values[i])) and (not isnan(h['close'].values[i-1])) and (not isnan(h['low'].values[i])) and (not isnan(h['high'].values[i])) \
                and (h['close'].values[i] < (1-lastbreakrate)*min(h['close'].values[i-1], h['high'].values[i])) and (data[stock].close < h['low'].values[i]) :
                for l in range(i+1, interval) :
                    if (not isnan(h['close'].values[l])) and (not isnan(h['high'].values[i])) and (h['close'].values[l] > h['high'].values[i]) :
                        breakout = False
                        break
        if breakout :
            log.info('.............股票跌幅过大...............')
            return True
    return False

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    # 检查变量是否在文件中更新
    if g.real_market_simulate and get_variables_updated(context, g.addstring):
        # 打印策略参数
        log_param()

    if (g.real_market_simulate or g.indebug) and g.autotrader_inform_enabled:
        # 检查服务器在线状态(避免回测时检查该状态严重影响回测速度，每10分钟检查一次)
        if g.real_market_simulate and (context.current_dt.minute % 10 == 0):
            # 通信状态变化，发邮件通知
            rspcode = autotrader_online_status(0)
            if rspcode != g.online_response_code:
                g.online_response_code = rspcode
                mail_to_report(rspcode)
        # 检查离线记录文件是否有未完成的离线交易，完成离线交易
        if g.online_response_code == 0:
            do_record_offline()

    # 获得当前时间
    hour = context.current_dt.hour
    minute = context.current_dt.minute

#    if isThreeBlackCrows(g.zs2, data) and isThreeBlackCrows(g.zs8, data):
#        for stock in g.stocks:
#            if context.portfolio.positions[stock].sellable_amount > 0:
#                #有仓位就清仓
#    		    log.info('三只乌鸦，清仓')
#    		    sell_all_stocks(context)
#    	#设置为周期的最后第2天，避免当天再次买入股票
#    	g.days = g.period-1
#        return

    # 检查止盈止损条件，并操作股票
    for stock in g.stocks:
        if context.portfolio.positions[stock].sellable_amount > 0:
            # 每分钟监测，如果有更高价则记录之，如果从最高价回撤一定比例，则抛掉
            #try:
            #    if data[stock].close > g.maxvalue[stock] :
            #        g.maxvalue[stock] = data[stock].close
            #except KeyError:
            #    g.maxvalue[stock] = data[stock].close
            #if ((data[stock].close - g.maxvalue[stock]) / g.maxvalue[stock]) <= -g.topdropthreshold :
            #    if g.minutesinlowprice[stock] == 0:
            #        curr_data = get_current_data()
            #        log.info('当前%s（%s）股价（%.02f）低于最高价（%.02f）向下降幅阈值' %(curr_data[stock].name, stock, data[stock].close, g.maxvalue[stock]))
            #    g.minutesinlowprice[stock] += 1
            #else:
            #    # 不连续状态则归零
            #    if g.minutesinlowprice[stock] < g.minutesthreshold:
            #        g.minutesinlowprice[stock] = 0
            # 股价持续低于最高价向下降幅阈值则止损
            #if g.minutesinlowprice[stock] >= g.minutesthreshold:
            #    position = context.portfolio.positions[stock]
            #    if close_position(context, position):
            #        g.todobuy = True
            #        log.info('持续低于最高价向下降幅阈值，止损: ')
            #        g.exceptions.append({'stock': stock, 'stopvalue': data[stock].close, 'targetvalue': 0.0})
            #        curr_data = get_current_data()
            #        log.info('Sell: %s(%s), %02f, %02f' %(curr_data[stock].name, stock,data[stock].close,g.maxvalue[stock]))

            # 获取最近2日收盘价
            h = attribute_history(stock, 2, unit='1d', fields=('close'), skip_paused=True)
            # 对当天下跌幅度过大的股票进行计数统计
            if data[stock].close  < 0.955*h['close'].values[-1] :
                if g.stockscrashed.count(stock) == 0:
                    g.stockscrashed.append(stock)
            # 当前价格超出止盈止损值，则卖出该股票
            dr3cur = (data[stock].close-h['close'].values[-2])/h['close'].values[-2]
            if dr3cur <= g.maxrbstd[stock]['bstd']:
                position = context.portfolio.positions[stock]
                if close_position(context, position):
                    g.todobuy = True
                    log.info('止损: ')
                    g.exceptions.append({'stock': stock, 'stopvalue': data[stock].close, 'targetvalue': 0.0})
                    curr_data = get_current_data()
                    log.info('Sell: %s(%s)' %(curr_data[stock].name, stock))
                # 如果该股票未包含在止损列表中，则添加进去
                if g.stopstocks.count(stock) == 0:
                    g.stopstocks.append(stock)
            elif dr3cur >= g.maxrbstd[stock]['maxr']*1.100:
                position = context.portfolio.positions[stock]
                if close_position(context, position):
                    g.todobuy = True
                    log.info('止盈: ')
                    g.exceptions.append({'stock': stock, 'stopvalue': 0.0, 'targetvalue': data[stock].close})
                    curr_data = get_current_data()
                    log.info('Sell: %s(%s)' %(curr_data[stock].name, stock))

    stopfactor = 1
    if g.stockCount > 2:
        stopfactor = 2
    # 当天下跌幅度过大的股票超过一定比例，或者超过一半的所持股票止损，清仓观望
    if (len(g.stocks) > 0) and (len(g.stockscrashed)*4.0/3 >= len(g.stocks) or len(g.stopstocks)*stopfactor >= len(g.stocks)) :
        g.todobuy = False
        if context.portfolio.positions_value > 0:
            #有仓位就清仓
            log.info('多只股票达到止损线，清仓')
            sell_all_stocks(context)
            # 修整1天，设置为周期的最后第2天，避免当天再次买入股票
            g.days = g.period-1

    pos_adjust_time = (hour == g.adjust_position_hour and minute== g.adjust_position_minute)
    # 有仓位、调仓时间或实盘时检查二八指标
    if (context.portfolio.positions_value > 0) or pos_adjust_time or g.real_market_simulate:
        # 获取前一天指数收盘价
        #hs1 = getStockPrice(g.zs1, g.lag)
        hs2 = getStockPrice(g.zs2, g.lag)
        hs8 = getStockPrice(g.zs8, g.lag)
        #cp1 = data[g.zs1].close
        cp2 = data[g.zs2].close
        cp8 = data[g.zs8].close

        #cmp1result = True
        cmp2result = True
        cmp8result = True

        #if (not isnan(hs1)) and (not isnan(cp1)):
        #    g.ret1 = (cp1 - hs1) / hs1
        #    if g.ret1>-0.004 :
        #        cmp1result = False
        #else:
        #    g.ret1 = 0
        if (not isnan(hs2)) and (not isnan(cp2)):
            g.ret2 = (cp2 - hs2) / hs2
            if g.ret2>-0.004 :
                cmp2result = False
        else:
            g.ret2 = 0
        if (not isnan(hs8)) and (not isnan(cp8)):
            g.ret8 = (cp8 - hs8) / hs8
            if g.ret8>-0.004 :
                cmp8result = False
        else:
            g.ret8 = 0
        #record(index1=g.ret1, index2=g.ret2, index8=g.ret8)
        record(index2=g.ret2, index8=g.ret8)

    # 检查二八指标是否达到降幅下限，如达到则清仓观望
    if context.portfolio.positions_value > 0 :
        if (cmp2result and cmp8result) or (isStockBearish(g.zs2, data, 5, 0.04, 0.03) or isStockBearish(g.zs8, data, 5, 0.04, 0.03)) :
            #有仓位就清仓
            log.info('二八未满足条件，清仓')
            sell_all_stocks(context)
            # 修整1天，设置为周期的最后第2天，避免当天再次买入股票
            g.days = g.period-1

    # 推荐股票
    if (minute % g.recommend_freq == 0) :
        if (g.real_market_simulate or g.indebug) :  
            stockrecommend = Multi_Select_Stocks(context, data)
            stockrecommend.sort()
            if cmp(g.stockrecommend, stockrecommend) != 0 :
                g.stockrecommend = stockrecommend
                output = ''
                curr_data = get_current_data()
                for stock in g.stockrecommend:
                    output += '%s(%s), ' % (curr_data[stock].name, stock)
                output = output[:-2]
                log.info('当前推荐股票：%s' %(output))

    # 每天下午14:50调仓
    if pos_adjust_time:
        #log.error("%s" % (str(g.ret_last5d)))
        #log.error("%f, %f, %f" %(g.ret1, g.ret2, g.ret8))
        if context.current_dt >= datetime.datetime(2006, 10, 10) and len(g.ret_last5d) >= 5:
            #g.gradient1 = g.ret1 - g.ret_last5d[0][0]
            g.gradient2 = g.ret2 - g.ret_last5d[0][1]
            g.gradient8 = g.ret8 - g.ret_last5d[0][2]

            #if g.gradient1 <= -0.01 and g.gradient2 <= -0.01 and g.gradient8 <= -0.01:
            #    log.error("所有指数向下趋势，减仓")

        #奇怪，低于101%时清仓，回测效果出奇得好。
        #超大盘指数只有在5日上涨斜率向上的情况下，满足101%涨幅时允许买入
        #if (g.ret1>0.01 and g.gradient1>0.01) or g.ret2>0.01 or g.ret8>0.01 :
        if g.ret2>0.01 or g.ret8>0.01 :
            g.days += 1
            if g.todobuy or (g.days % g.period == 1):            
                log.info('持有，每%d天进行调仓' %(g.period))
                buy_stocks(context, data)
                update_maxr_bstd(context)
        else :
            log.info('清仓')
            sell_all_stocks(context)

# 开仓，买入指定价值的证券
# 报单成功并成交（包括全部成交或部分成交，此时成交量大于0），返回True
# 报单失败或者报单成功但被取消（此时成交量等于0），返回False
def open_position(context, security, value):
    order = order_target_value_(context, security, value)
    if order != None and order.filled > 0:
        return True
    return False

# 平仓，卖出指定持仓
# 平仓成功并全部成交，返回True
# 报单失败或者报单成功但被取消（此时成交量等于0），或者报单非全部成交，返回False
def close_position(context, position):
    security = position.security
    order = order_target_value_(context, security, 0) # 可能会因停牌失败
    if order != None:
        if order.filled > 0:
            # 只要有成交，无论全部成交还是部分成交，则统计盈亏
            g.trade_stat.watch(security, order.filled, position.avg_cost, position.price)

        if order.status == OrderStatus.held and order.filled == order.amount:
            return True

    return False

# 自定义下单
# 根据Joinquant文档，当前报单函数都是阻塞执行，报单函数（如order_target_value）返回即表示报单完成
# 报单成功返回报单（不代表一定会成交），否则返回None
def order_target_value_(context, security, value):
    if value == 0:
        log.debug("Selling out %s" % (security))
    else:
        log.debug("Order %s to value %f" % (security, value))
        
    # 如果股票停牌，创建报单会失败，order_target_value 返回None
    # 如果股票涨跌停，创建报单会成功，order_target_value 返回Order，但是报单会取消
    # 部成部撤的报单，聚宽状态是已撤，此时成交量>0，可通过成交量判断是否有成交
    order = order_target_value(security, value)
    # 模拟式盘情况下，订单非空
    if (g.real_market_simulate or g.indebug) and order != None:
        tradedatetime = context.current_dt
        posInPercent = value / (context.portfolio.total_value - g.totalValueDifference)
        curr_data = get_current_data()
        secname = curr_data[order.security].name
        if g.autotrader_inform_enabled:
            # inform auto trader to do the trade
            autotrader_stock_trade(g.policy_name, order.security, secname, posInPercent, order.price, tradedatetime, order.order_id)
            if g.online_response_code == 0:
                rspcode = do_record_offline()
                if rspcode != g.online_response_code:
                    g.online_response_code = rspcode
                    rspcode = mail_to_report(rspcode)
    return order

def isThreeBlackCrows(stock, data):
    his =  attribute_history(stock, 2, '1d', ('close','open'), skip_paused=True, df=False)
    closeArray = list(his['close'])
    closeArray.append(data[stock].close)
    openArray = list(his['open'])
    openArray.append(get_current_data()[stock].day_open)
#    if closeArray[0]-0.045:
    if closeArray[0]<openArray[0] and closeArray[1]<openArray[1] and closeArray[2]<openArray[2]:
        if closeArray[-1]/closeArray[0]-1>-0.045:
            his =  attribute_history(stock, 4, '1d', ('close','open'), skip_paused=True, df=False)
            closeArray1 = his['close']
            if closeArray[0]/closeArray1[0]-1>0:
                return True
    return False

def buy_stocks(context, data):
    g.stocks = Multi_Select_Stocks(context, data)
    if len(g.stocks) <= 0 :
        return

    set_universe(g.stocks)

    # close stock positions not in the current universe
    for stock in context.portfolio.positions.keys():
        #确保股票数大于0，且该股票不在新选中的股票池内
        if (context.portfolio.positions[stock].total_amount > 0) and (stock not in g.stocks):
            position = context.portfolio.positions[stock]
            if not close_position(context, position) :
                #售出股票失败（如停牌股票）的情况，需要删除后面几个多余的备选股票，使股票数保持4个
                g.stocks.pop()
                g.stocks.insert(0, stock)
            curr_data = get_current_data()
            log.info('Rank Outof 10, Sell: %s(%s)' %(curr_data[stock].name, stock))

    #初始化新选中的股票的最高价
    #for stock in g.stocks :
    #    if stock not in context.portfolio.positions.keys():
    #        g.maxvalue[stock] = data[stock].close
    #        #初始化股价低于最高价向下降幅阈值计时
    #        g.minutesinlowprice[stock] = 0

    valid_count = 0
    for stock in context.portfolio.positions.keys():
        if context.portfolio.positions[stock].total_amount > 0:
            valid_count = valid_count + 1
    # place equally weighted orders
    #已有股票数量>=4个，则直接返回
    if valid_count < len(g.stocks):
        value = (context.portfolio.total_value - g.totalValueDifference) / len(g.stocks)
        for stock in g.stocks:
            open_position(context, stock, value)
            curr_data = get_current_data()
            log.info('buy: %s(%s)' %(curr_data[stock].name, stock))

def update_maxr_bstd(context):
    g.maxrbstd = {}
    for stock in g.stocks:
        # maxd = 个股250天内最大的3日跌幅
        # avgd = 个股250天内平均的3日跌幅
        # bstd = (maxd+avgd)/2, 此bstd即为个股在持仓3天内，能承受的最大跌幅
        # maxr = 个股250天内最大的3日涨幅，个股盈利超过其历史值maxr的时候，则立刻清仓止盈
        h = attribute_history(stock, 250, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        maxr = 0.00
        maxd = 0.00
        avgd = 0.00
        dcount = 0
        for i in range(1, len(h)-3):
            # 个股连续3日涨跌幅
            dr3days = 0.00
            if (not isnan(h.close[i+2])) and (not isnan(h.close[i-1])):
                dr3days = (h.close[i+2]-h.close[i-1])/h.close[i-1]
            if dr3days > maxr:
                maxr = dr3days
            if dr3days < maxd:
                maxd = dr3days
            if dr3days < 0:
                avgd += dr3days
                dcount += 1
        if dcount > 0 :
            avgd = avgd/dcount
        bstd = (maxd+avgd)/2

        g.maxrbstd[stock] = {'maxr': maxr, 'bstd': bstd}

#================================================================================
#每天开盘前
#================================================================================
def before_trading_start(context):
    # 检查变量是否在文件中更新
    if get_variables_updated(context, g.addstring):
        # 打印策略参数
        log_param()

    # 将滑点设置为0
    set_slippage(FixedSlippage(0)) 
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    # 设置手续费，每笔交易时的手续费是, 买入时券商佣金，卖出时券商佣金加千分之一印花税, 每笔交易最低扣5块钱
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.00027, sell_cost=0.00127, min_cost=5)) 
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))

    # 计算并记录当日个股250天内最大的3日涨幅及能承受的最大跌幅
    update_maxr_bstd(context)

    #初始化购买之后的最高价，剔除不在持仓范围内的股票最高价元素
    #maxvalue = {}
    #minutesinlowprice = {}
    #for stock in context.portfolio.positions.keys():
    #    if stock in g.stocks:
    #        try:
    #            maxvalue[stock] = g.maxvalue[stock]
    #        except KeyError:
    #            maxvalue[stock] = 0.01
    #        #记录上一日股价低于最高价向下降幅阈值计时值
    #        try:
    #            minutesinlowprice[stock] = g.minutesinlowprice[stock]
    #        except KeyError:
    #            minutesinlowprice[stock] = 0
    #    else:
    #        h = attribute_history(stock, 1, unit='1d', fields=('close'), skip_paused=True)
    #        if (len(h) > 0) and (not isnan(h.close[-1])):
    #            maxvalue[stock] = h.close[-1]
    #        else:
    #            maxvalue[stock] = 0.01
    #        #初始化股价低于最高价向下降幅阈值计时
    #        minutesinlowprice[stock] = 0
    #g.minutesinlowprice = minutesinlowprice
    #g.maxvalue = maxvalue

#================================================================================
#每天收盘后
#================================================================================
def after_trading_end(context):
    g.trade_stat.report(context)

    while len(g.ret_last5d) >= 5:
        g.ret_last5d.pop()
    g.ret_last5d.insert(0, (g.ret1, g.ret2, g.ret8))
    g.ret1 = 0
    g.ret2 = 0
    g.ret8 = 0
    g.gradient1 = 0
    g.gradient2 = 0
    g.gradient8 = 0

    g.todobuy = False
    g.stockscrashed = []
    g.stopstocks = []

    # 模拟实盘情况下执行
    if (g.real_market_simulate or g.indebug) and g.autotrader_inform_enabled:
        # 删除当天未完成的离线交易记录
        rm_all_records_offline()

    # 得到当前未完成订单
    orders = get_open_orders()
    for _order in orders.values():
        log.info("canceled uncompleted order: %s" %(_order.order_id))
    pass

# 交易统计类
class trade_stat():
    def __init__(self):
        self.trade_total_count = 0
        self.trade_success_count = 0
        self.statis = {'win': [], 'loss': []}
        
    def reset(self):
        self.trade_total_count = 0
        self.trade_success_count = 0
        self.statis = {'win': [], 'loss': []}
    
    # 记录交易次数便于统计胜率
    # 卖出成功后针对卖出的量进行盈亏统计
    def watch(self, stock, sold_amount, avg_cost, cur_price):
        self.trade_total_count += 1
        current_value = sold_amount * cur_price
        cost = sold_amount * avg_cost

        percent = round((current_value - cost) / cost * 100, 2)
        if current_value > cost:
            self.trade_success_count += 1
            win = [stock, percent]
            self.statis['win'].append(win)
        else:
            loss = [stock, percent]
            self.statis['loss'].append(loss)
        
    def report(self, context):
        cash = context.portfolio.cash - g.totalValueDifference
        totol_value = context.portfolio.total_value - g.totalValueDifference
        position = 1 - cash/totol_value
        log.info("收盘后持仓概况:%s" % str(list(context.portfolio.positions)))
        log.info("仓位概况:%.2f" % position)
        self.print_win_rate(context.current_dt.strftime("%Y-%m-%d"), context.current_dt.strftime("%Y-%m-%d"), context)

    # 打印胜率
    def print_win_rate(self, current_date, print_date, context):
        if str(current_date) == str(print_date):
            win_rate = 0
            if 0 < self.trade_total_count and 0 < self.trade_success_count:
                win_rate = round(self.trade_success_count / float(self.trade_total_count), 3)

            most_win = self.statis_most_win_percent()
            most_loss = self.statis_most_loss_percent()
            starting_cash = g.capitalValue
            total_profit = self.statis_total_profit(context)
            if len(most_win)==0 or len(most_loss)==0:
                return

            print "-"
            print '------------绩效报表------------'
            print '交易次数: {0}, 盈利次数: {1}, 胜率: {2}'.format(self.trade_total_count, self.trade_success_count, str(win_rate * 100) + str('%'))
            print '单次盈利最高: {0}, 盈利比例: {1}%'.format(most_win['stock'], most_win['value'])
            print '单次亏损最高: {0}, 亏损比例: {1}%'.format(most_loss['stock'], most_loss['value'])
            print '总资产: {0}, 本金: {1}, 盈利: {2}, 盈亏比率：{3}%'.format(starting_cash + total_profit, starting_cash, total_profit, total_profit / starting_cash * 100)
            print '--------------------------------'
            print "-"

    # 统计单次盈利最高的股票
    def statis_most_win_percent(self):
        result = {}
        for statis in self.statis['win']:
            if {} == result:
                result['stock'] = statis[0]
                result['value'] = statis[1]
            else:
                if statis[1] > result['value']:
                    result['stock'] = statis[0]
                    result['value'] = statis[1]

        return result

    # 统计单次亏损最高的股票
    def statis_most_loss_percent(self):
        result = {}
        for statis in self.statis['loss']:
            if {} == result:
                result['stock'] = statis[0]
                result['value'] = statis[1]
            else:
                if statis[1] < result['value']:
                    result['stock'] = statis[0]
                    result['value'] = statis[1]

        return result

    # 统计总盈利金额    
    def statis_total_profit(self, context):
        return (context.portfolio.total_value - g.totalValueDifference) - g.capitalValue

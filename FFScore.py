# 克隆自聚宽文章：https://www.joinquant.com/post/4872
# 标题：华泰价值选股之FFScore模型
# 作者：小兵哥

import numpy as np
import talib
import pandas
import datetime as dt
import talib as tl
import pandas as pd
import tradestat

def initialize(context):
    #用沪深 300 做回报基准
    set_benchmark('000300.XSHG')
    # 滑点、真实价格
    set_slippage(FixedSlippage(0.000))
    set_option('use_real_price', True)

    # 关闭部分log
    log.set_level('order', 'error')

    # 开盘前运行
    run_daily(before_market_open, time='before_open') 
    # 开盘时运行
    run_daily(market_open, time='every_bar')
    # 收盘后运行
    run_daily(after_market_close, time='after_close')

    # 加载统计模块
    g.trade_stat = tradestat.trade_stat()

def after_code_changed(context):

    # initialize 运行机制多变和复杂，所有变量都挪到 after_code_changed 里
    g.quantlib = quantlib()
    # 调仓参数
    g.quantlib.fun_set_var(context, 'hold_cycle', 21)
    g.quantlib.fun_set_var(context, 'hold_periods', 0)
    g.quantlib.fun_set_var(context, 'stock_list', [])
    # '000300.XSHG' #沪深300指数 #'000016.XSHG' #上证50指数
    # '159902.XSHE' #'399005.XSHE' #中小板指数
    g.quantlib.fun_set_var(context, 'banchmark', '000300.XSHG')
    # 指数是否处于风险区域
    g.quantlib.fun_set_var(context, 'index_in_risk', False)
    # 指数布林线是否强势区域
    g.quantlib.fun_set_var(context, 'index_in_strong_tone', False)
    # 卖出股票信号
    g.quantlib.fun_set_var(context, 'sell_stock_signal', False)
    # 执行清仓操作
    g.quantlib.fun_set_var(context, 'clear_positions', False)

    # 分配策略的市值比例
    context.FFScore_ratio = 1.0

    # 定义股票池
    moneyfund = ['511880.XSHG']

    # 上市不足 60 天的剔除掉
    context.moneyfund = g.quantlib.fun_delNewShare(context, moneyfund, 60)

## 开盘前运行函数     
def before_market_open(context):
    # 当日是否出现新最低价
    g.newlowprice = False
    # 当日是否出现新最高价
    g.newhighprice = False

## 收盘后运行函数  
def after_market_close(context):
    log.info('##############################################################')
    g.trade_stat.report(context)
    log.info('##############################################################\n\n')

def bollinger_bands(codes, timeperiod=20, nbdevup=2, nbdevdn=2):
    '''
            多股票布林带
    依赖库：
        import talib as tl
        import pandas as pd
    参数：
        codes: 股票代码列表
        timeperiod: 滑动窗口长度
        nbdevup: 上边带标准差倍数
        nbdevdn: 下边带标准差倍数
    返回：
        DataFrame:  index: codes;  columns: ['lower','middle', 'upper']
    范例：
        df = bollinger_bands(['000001.XSHG','000016.XSHG','399333.XSHE'])
        print df.lower['000016.XSHG']
        print df
    '''
    
    if isinstance(codes, str):
        codes = [codes]
    #df = get_price(codes, end_date='2017-05-26', frequency='daily', fields='close', count=timeperiod*2)['close']
    df = history(timeperiod*2, '1d', 'close' , codes, skip_paused=True)
    def func(xs): 
        u, m, l = tl.BBANDS(xs.values, timeperiod, nbdevup, nbdevdn)
        return pd.Series({"upper":u[-1],"middle":m[-1],"lower":l[-1]},name=xs.name)
    return df.apply(func).T

# 获取前n个单位时间当时的收盘价
def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, ('close'), True)['close'][0]

def market_open(context):

    indexprice = get_close_price(context.banchmark, 1, '1m')

    # 计算对比标杆指数布林线参数
    df = bollinger_bands([context.banchmark])
    # 布林线上轨上沿阈值
    upperlimit = (df.upper[0] + (df.upper[0] - df.middle[0]) / 5)
    # 布林线下轨下沿阈值
    lowerlimit = (df.lower[0] - (df.middle[0] - df.lower[0]) / 5)
    # 布林线中轨上沿阈值
    middleupperlimit = (df.middle[0] + (df.upper[0] - df.middle[0]) / 5)
    # 布林线中轨下沿阈值
    middlelowerlimit = (df.middle[0] - (df.middle[0] - df.lower[0]) / 5)

    # 记录上一次指数强势状态
    last_index_status = context.index_in_strong_tone
    # 计算指数强弱
    if context.index_in_strong_tone and indexprice < middlelowerlimit:
        context.index_in_strong_tone = False
    elif not context.index_in_strong_tone and indexprice > middleupperlimit:
        context.index_in_strong_tone = True

    if last_index_status != context.index_in_strong_tone:
        log.info("之前 - %d, 现在 - %d" %(last_index_status, context.index_in_strong_tone))

    # 强势转为弱势区域
    # 或强势区域进入布林线上轨上方
    # 清仓
    if not context.index_in_risk and last_index_status:
        if not context.index_in_strong_tone:
            # 指数进入风险区域
            context.index_in_risk = True
            context.sell_stock_signal = True
            log.info("当前布林线上轨: %f, 中轨: %f, 下轨: %f" % (df.upper[0], df.middle[0], df.lower[0]))
            log.info("当前布林线中轨上沿阈值: %f, 中轨下沿阈值: %f, 指数: %f" % (middleupperlimit, middlelowerlimit, indexprice))
            log.info("强势转为弱势区域")
        elif indexprice >= upperlimit:
            # 指数进入风险区域
            context.index_in_risk = True
            log.info("当前布林线上轨: %f, 中轨: %f, 下轨: %f" % (df.upper[0], df.middle[0], df.lower[0]))
            log.info("当前布林线上轨上沿阈值: %f, 指数: %f" % (upperlimit, indexprice))
            log.info("强势区域进入布林线上轨上方")
    # 弱势转为强势区域
    # 或弱势区域进入布林线下轨下方
    # 建仓
    elif context.index_in_risk and not last_index_status:
        if context.index_in_strong_tone:
            # 指数进入非风险区域
            context.index_in_risk = False
            context.sell_stock_signal = False
            log.info("当前布林线上轨: %f, 中轨: %f, 下轨: %f" % (df.upper[0], df.middle[0], df.lower[0]))
            log.info("当前布林线中轨上沿阈值: %f, 中轨下沿阈值: %f, 指数: %f" % (middleupperlimit, middlelowerlimit, indexprice))
            log.info("弱势转为强势区域")
        elif indexprice <= lowerlimit:
            # 指数进入非风险区域
            context.index_in_risk = False
            log.info("当前布林线上轨: %f, 中轨: %f, 下轨: %f" % (df.upper[0], df.middle[0], df.lower[0]))
            log.info("当前布林线下轨下沿阈值: %f, 指数: %f" % (lowerlimit, indexprice))
            log.info("弱势区域进入布林线下轨下方")

    # 指数处于风险区域且回归至布林线中轨上沿阈值以下，则卖出股票
    if not context.sell_stock_signal and context.index_in_risk and indexprice < middleupperlimit:
        log.info("风险区域且回归至布林线中轨上沿阈值以下")
        context.sell_stock_signal = True
    # 指数处于非风险区域且回归至布林线中轨下沿阈值以上，则买入股票
    elif context.sell_stock_signal and not context.index_in_risk and indexprice > middlelowerlimit:
        log.info("非风险区域且回归至布林线中轨下沿阈值以上")
        context.sell_stock_signal = False
    # 指数处于非风险区域且回归至布林线中轨下沿阈值以下，则卖出股票
    elif not context.sell_stock_signal and not context.index_in_risk and indexprice <= middlelowerlimit:
        log.info("非风险区域且回归至布林线中轨下沿阈值以下")
        context.sell_stock_signal = True
    # 指数处于非风险区域且回归至布林线中轨上沿阈值以上，则买入股票
    elif context.sell_stock_signal and context.index_in_risk and indexprice >= middleupperlimit:
        log.info("非风险区域且回归至布林线中轨下沿阈值以上")
        context.sell_stock_signal = False

    # 允许调仓标记
    clear_positions = context.sell_stock_signal
    # 指数值位于布林线下轨上沿且仓位为空
    if context.portfolio.positions_value <= 0 and not context.sell_stock_signal:
        # 获取指数n日内的最低价
        close_data = attribute_history(context.banchmark, 3, '1d', ['low'])
        lowprice = close_data['low'].min()
        # 出现新最低价则当日直接不交易
        if indexprice < lowprice:
            g.newlowprice = True
        if not g.newlowprice:
            # 允许买入
            clear_positions = False
    # 指数值位于布林线上轨上沿且仓位非空
    elif context.portfolio.positions_value > 0 and context.sell_stock_signal:
        # 获取指数n日内的最高价
        close_data = attribute_history(context.banchmark, 3, '1d', ['high'])
        highprice = close_data['high'].max()
        # 出现新最高价则当日直接不交易
        if indexprice > highprice:
            g.newhighprice = True
        if not g.newhighprice:
            # 清仓
            clear_positions = True

    if context.clear_positions != clear_positions:
        context.clear_positions = clear_positions
        if context.clear_positions:
            log.info("==> 清仓，卖出所有股票")
        else:
            log.info("==> 允许买入或调仓")

    if context.clear_positions:
        context.stock_list = []
        position_ratio = {}
        for stock in context.portfolio.positions.keys():
            position_ratio[stock] = 0
        context.position_ratio = position_ratio
        # 调仓，执行交易
        trade_style = False    # True 会交易进行类似 100股的买卖，False 则只有在仓位变动 >25% 的时候，才产生交易
        if context.hold_periods == context.hold_cycle:
            trade_style = True
        g.quantlib.fun_do_trade(context, context.position_ratio, context.moneyfund, trade_style)

    # 判断是否允许调仓且到达调仓每日时间
    elif context.current_dt.hour == 10 and context.current_dt.minute == 30:
        # 引用 lib
        g.FFScore  = FFScore_lib()

        # 检查是否需要调仓
        rebalance_flag, context.hold_periods, msg = \
            g.quantlib.fun_needRebalance('策略', context.stock_list, \
                context.hold_periods, context.hold_cycle)

        if rebalance_flag:
            statsDate = context.current_dt.date()

            # 计算策略的持仓
            position_ratio = g.FFScore.algo(context, context.FFScore_ratio, context.portfolio.total_value)

            context.stock_list = position_ratio.keys()

            # 卖掉已有且不在待购清单里的股票
            for stock in context.portfolio.positions.keys():
                if stock not in position_ratio:
                    position_ratio[stock] = 0
            context.position_ratio = position_ratio

        # 调仓，执行交易
        trade_style = False    # True 会交易进行类似 100股的买卖，False 则只有在仓位变动 >25% 的时候，才产生交易
        if context.hold_periods == context.hold_cycle:
            trade_style = True
        g.quantlib.fun_do_trade(context, context.position_ratio, context.moneyfund, trade_style)

class FFScore_lib():

    def __init__(self, _period = '1d'):
        pass

    def algo(self, context, algo_ratio, total_value):
        '''
        FFScore algorithms
        输入参数：FFScore_ratio, protfolio_value
        输出参数：FFScore_trade_ratio
        自有类  : FFScore_lib
        调用类  : quantlib
        '''
        # 调仓
        statsDate = context.current_dt.date()
        # 取得待购列表
        stock_list = self.fun_get_stock_list(context, statsDate)

        # 分配仓位
        equity_ratio, bonds_ratio = g.quantlib.fun_assetAllocationSystem(stock_list, context.moneyfund, statsDate)

        # 根据预设的风险敞口，计算交易时的比例
        trade_ratio = g.quantlib.fun_calPosition(equity_ratio, bonds_ratio, algo_ratio, context.moneyfund, total_value, statsDate)

        return trade_ratio

    def fun_get_stock_list(self, context, statsDate):
        def __cal_FFScore(stock_list, FFScore, new_list):
            for stock in stock_list:
                if stock in new_list:
                    if stock in FFScore:
                        FFScore[stock] += 1
                    else:
                        FFScore[stock] = 1
                elif stock not in FFScore:
                    FFScore[stock] = 0
            return FFScore

        df = get_fundamentals(
            query(valuation.code, valuation.pb_ratio),
            date = statsDate - dt.timedelta(1)
        )
        # 1）市净率全市场从小到大前20%（剔除市净率为负的股票）
        df = df.sort(['pb_ratio'], ascending=[True])
        df = df.reset_index(drop = True)
        df = df[df.pb_ratio > 0]
        df = df.reset_index(drop = True)
        df = df[0:int(len(df)*0.05)]  #股票太多，所以变更了比例
        stock_list = list(df['code'])

        #2) 盈利水平打分
        # 2.1 资产收益率（ROE）：收益率为正数时ROE=1，否则为0。
        df = get_fundamentals(
            query(indicator.code, indicator.roe),
            date = statsDate - dt.timedelta(1)
        )
        df = df[df.code.isin(stock_list)]
        df = df.reset_index(drop = True)
        df = df[df.roe > 0]
        df = df.reset_index(drop=True)
        list_roe = list(df['code'])

        FFScore = {}
        FFScore = __cal_FFScore(stock_list, FFScore, list_roe)
        
        #2.2 资产收益率变化（△ROA）：当期最新可得财务报告的ROA同比的变化。变化为正数时△ROA=1，否则为0。
        df = get_fundamentals(
            query(indicator.code, indicator.roa),
            date = statsDate - dt.timedelta(1)
        )
        # 此算法不严谨，先简单实现，看看大体效果
        df2 = get_fundamentals(
            query(indicator.code, indicator.roa),
            date = statsDate - dt.timedelta(365)
        )
        df = df[df.code.isin(stock_list)]
        df = df.reset_index(drop = True)
        df.index = list(df['code'])
        df = df.drop(['code'], axis=1)
        dict1 = df.to_dict()['roa']

        df2 = df2[df2.code.isin(stock_list)]
        df2 = df2.reset_index(drop = True)
        df2.index = list(df2['code'])
        df2 = df2.drop(['code'], axis=1)
        dict2 = df2.to_dict()['roa']
        
        tmpList = []
        for stock in dict1.keys():
            if stock in dict2:
                if dict1[stock] > dict2[stock]:
                    tmpList.append(stock)
        FFScore = __cal_FFScore(stock_list, FFScore, tmpList)

        # 3)财务杠杆和流动性
        # 3.1 杠杆变化（△LEVER）：杠杆通过非流动负债合计除以非流动资产合计计算，杠杆变化为当期最新可得财务报告的杠杆同比的变化。变化为负数时△LEVER=1，否则为0。
        df = get_fundamentals(
            query(balance.code, balance.total_non_current_assets, balance.total_non_current_liability),
            date = statsDate - dt.timedelta(1)
        )
        # 此算法不严谨，先简单实现，看看大体效果
        df2 = get_fundamentals(
            query(balance.code, balance.total_non_current_assets, balance.total_non_current_liability),
            date = statsDate - dt.timedelta(365)
        )
        
        df3 = get_fundamentals(
            query(balance.code, balance.total_non_current_assets, balance.total_non_current_liability),
            date = statsDate - dt.timedelta(730)
        )

        df['total_non_current_assets_before'] = df2['total_non_current_assets']
        df = df.dropna()
        df = df[df.code.isin(stock_list)]
        df['LEVER'] = 2.0*df['total_non_current_liability'] / (df['total_non_current_assets'] + df['total_non_current_assets_before'])
        df.index = list(df['code'])
        df = df.drop(['code', 'total_non_current_assets', 'total_non_current_liability', 'total_non_current_assets_before'], axis=1)
        dict1 = df.to_dict()['LEVER']

        df2['total_non_current_assets_before'] = df3['total_non_current_assets']
        df2 = df2.dropna()
        df2 = df2[df2.code.isin(stock_list)]
        df2['LEVER'] = 2.0*df2['total_non_current_liability'] / (df2['total_non_current_assets'] + df2['total_non_current_assets_before'])
        df2.index = list(df2['code'])
        df2 = df2.drop(['code', 'total_non_current_assets', 'total_non_current_liability', 'total_non_current_assets_before'], axis=1)
        dict2 = df2.to_dict()['LEVER']

        tmpList = []
        for stock in dict1.keys():
            if stock in dict2:
                if dict1[stock] < dict2[stock]:
                    tmpList.append(stock)
        FFScore = __cal_FFScore(stock_list, FFScore, tmpList)
        '''
        df = get_fundamentals(
            query(balance.code, balance.total_non_current_assets, balance.total_non_current_liability),
            date = statsDate - dt.timedelta(1)
        )
        # 此算法不严谨，先简单实现，看看大体效果
        df2 = get_fundamentals(
            query(balance.code, balance.total_non_current_assets, balance.total_non_current_liability),
            date = statsDate - dt.timedelta(365)
        )

        df = df[df.code.isin(stock_list)]
        df['LEVER'] = df['total_non_current_liability'] / df['total_non_current_assets']
        df.index = list(df['code'])
        df = df.drop(['code', 'total_non_current_assets', 'total_non_current_liability'], axis=1)
        dict1 = df.to_dict()['LEVER']

        df2 = df2[df2.code.isin(stock_list)]
        df2['LEVER'] = df2['total_non_current_liability'] / df2['total_non_current_assets']
        df2.index = list(df2['code'])
        df2 = df2.drop(['code', 'total_non_current_assets', 'total_non_current_liability'], axis=1)
        dict2 = df2.to_dict()['LEVER']

        tmpList = []
        for stock in dict1.keys():
            if stock in dict2:
                if dict1[stock] < dict2[stock]:
                    tmpList.append(stock)
        FFScore = __cal_FFScore(stock_list, FFScore, tmpList)
        '''
        # 4）运营效率
        # 4.1 流动资产周转率变化（△CATURN）： 流动资产周转率变化为当期最新可得财务报告的资产周转率同比的变化。变化为正数时△CATURN =1，否则为0。
        # 主营业务收入与流动资产的比例来反映流动资产的周转速度，来衡量企业在生产运营上对流动资产的利用效率。
        df = get_fundamentals(
            query(balance.code, balance.total_current_assets, income.total_operating_revenue, income.non_operating_revenue),
            date = statsDate - dt.timedelta(1)
        )
        # 此算法不严谨，先简单实现，看看大体效果
        df2 = get_fundamentals(
            query(balance.code, balance.total_current_assets, income.total_operating_revenue, income.non_operating_revenue),
            date = statsDate - dt.timedelta(365)
        )

        df3 = get_fundamentals(
            query(balance.code, balance.total_current_assets, income.total_operating_revenue, income.non_operating_revenue),
            date = statsDate - dt.timedelta(730)
        )

        df['total_current_assets_before'] = df2['total_current_assets']
        df = df.dropna()
        df = df[df.code.isin(stock_list)]
        df['CATURN'] = (df['total_operating_revenue'] - df['non_operating_revenue']) / (df['total_current_assets'] + df['total_current_assets_before'])
        df.index = list(df['code'])
        df = df.drop(['code', 'total_current_assets', 'total_operating_revenue', 'non_operating_revenue', 'total_current_assets_before'], axis=1)
        dict1 = df.to_dict()['CATURN']

        df2['total_current_assets_before'] = df3['total_current_assets']
        df2 = df2.dropna()
        df2 = df2[df2.code.isin(stock_list)]
        df2['CATURN'] = (df2['total_operating_revenue'] - df2['non_operating_revenue']) / (df2['total_current_assets'] + df2['total_current_assets_before'])
        df2.index = list(df2['code'])
        df2 = df2.drop(['code', 'total_current_assets', 'total_operating_revenue', 'non_operating_revenue', 'total_current_assets_before'], axis=1)
        dict2 = df2.to_dict()['CATURN']
        
        tmpList = []
        for stock in dict1.keys():
            if stock in dict2:
                if dict1[stock] > dict2[stock]:
                    tmpList.append(stock)
        FFScore = __cal_FFScore(stock_list, FFScore, tmpList)

        # 4.2 资产周转率变化（△TURN）： 资产周转率通过总资产周转率除以平均资产总值计算，资产周转率变化为当期最新可得财务报告的资产周转率同比的变化。变化为正数时△TURN =1，否则为0
        df = get_fundamentals(
            query(balance.code, income.total_operating_revenue, income.non_operating_revenue, balance.total_current_assets, balance.total_non_current_assets),
            date = statsDate - dt.timedelta(1)
        )
        df2 = get_fundamentals(
            query(balance.code, income.total_operating_revenue, income.non_operating_revenue, balance.total_current_assets, balance.total_non_current_assets),
            date = statsDate - dt.timedelta(365)
        )
        df3 = get_fundamentals(
            query(balance.code, income.total_operating_revenue, income.non_operating_revenue, balance.total_current_assets, balance.total_non_current_assets),
            date = statsDate - dt.timedelta(730)
        )

        df['total_assets'] = df['total_current_assets'] + df['total_non_current_assets']
        df2['total_assets'] = df2['total_current_assets'] + df2['total_non_current_assets']
        df3['total_assets'] = df3['total_current_assets'] + df3['total_non_current_assets']
        df['total_assets_before'] = df2['total_assets']
        df2['total_assets_before'] = df3['total_assets']
        df = df.dropna()
        df2 = df2.dropna()

        df = df[df.code.isin(stock_list)]
        df['TURN'] = (df['total_operating_revenue'] - df['non_operating_revenue']) / (df['total_assets'] + df['total_assets_before'])
        df.index = list(df['code'])
        df = df.drop(['code', 'total_operating_revenue', 'non_operating_revenue', 'total_current_assets', 'total_non_current_assets', 'total_assets', 'total_assets_before'], axis=1)
        dict1 = df.to_dict()['TURN']

        df2 = df2[df2.code.isin(stock_list)]
        df2['TURN'] = (df2['total_operating_revenue'] - df2['non_operating_revenue']) / (df2['total_assets'] + df2['total_assets_before'])
        df2.index = list(df2['code'])
        df2 = df2.drop(['code', 'total_operating_revenue', 'non_operating_revenue', 'total_current_assets', 'total_non_current_assets', 'total_assets', 'total_assets_before'], axis=1)
        dict2 = df2.to_dict()['TURN']

        tmpList = []
        for stock in dict1.keys():
            if stock in dict2:
                if dict1[stock] > dict2[stock]:
                    tmpList.append(stock)
        FFScore = __cal_FFScore(stock_list, FFScore, tmpList)

        stock_list = []
        for stock in FFScore.keys():
            if FFScore[stock] == 5:
                stock_list.append(stock)

        stock_list = g.quantlib.unpaused(stock_list)
        stock_list = g.quantlib.remove_st(stock_list, statsDate)

        return stock_list

class quantlib():
    def __init__(self, _period = '1d'):
        pass

    def fun_set_var(self, context, var_name, var_value):
        if var_name not in dir(context):
            setattr(context, var_name, var_value)

    def fun_needRebalance(self, algo_name, stock_list, hold_periods, hold_cycle):
        msg = ""
        msg += algo_name + "离下次调仓还剩 " + str(hold_periods) + " 天\n"
        rebalance_flag = False
        
        if len(stock_list) <= 1:
            msg += algo_name + "调仓，因为持股数为 0 \n"
            rebalance_flag = True
        elif hold_periods == 0:
            msg += algo_name + "调仓，因为持股天数剩余为 0 \n"
            rebalance_flag = True

        if rebalance_flag:
            hold_periods = hold_cycle
        else:
            hold_periods -= 1

        return rebalance_flag, hold_periods, msg

    def fun_assetAllocationSystem(self, buylist, moneyfund, statsDate=None):
        def __fun_getEquity_ratio(__stocklist, statsDate):
            __ratio = {}
            if __stocklist:
                for stock in __stocklist:
                    # 等权重
                    __ratio[stock] = 1.0/len(__stocklist)

            return __ratio

        equity_ratio = __fun_getEquity_ratio(buylist, statsDate)
        bonds_ratio  = __fun_getEquity_ratio(moneyfund, statsDate)
    
        return equity_ratio, bonds_ratio

    def fun_calPosition(self, equity_ratio, bonds_ratio, algo_ratio, moneyfund, total_value, statsDate=None):
        # 简化，不调整
        trade_ratio = equity_ratio

        return trade_ratio

    def fun_do_trade(self, context, trade_ratio, moneyfund, trade_style):
    
        def __fun_tradeStock(context, curPrice, stock, ratio, trade_style):
            total_value = context.portfolio.total_value
            if stock in moneyfund:
                self.fun_tradeBond(context, stock, total_value * ratio)
            else:
                curValue = context.portfolio.positions[stock].total_amount * curPrice
                Quota = total_value * ratio
                if Quota:
                    if abs(Quota - curValue) / Quota >= 0.25 or trade_style:
                        if Quota > curValue:
                            if curPrice > context.portfolio.positions[stock].avg_cost:
                                self.fun_trade(context, stock, Quota)
                        else:
                            self.fun_trade(context, stock, Quota)
                else:
                    if curValue > 0:
                        self.fun_trade(context, stock, Quota)
    
        trade_list = trade_ratio.keys()
        myholdstock = context.portfolio.positions.keys()
        stock_list = list(set(trade_list).union(set(myholdstock)))
        total_value = context.portfolio.total_value
    
        # 已有仓位
        holdDict = {}
        h = history(1, '1d', 'close', stock_list, df=False)
        for stock in myholdstock:
            tmpW = round((context.portfolio.positions[stock].total_amount * h[stock])/total_value, 2)
            holdDict[stock] = float(tmpW)
    
        # 对已有仓位做排序
        tmpDict = {}
        for stock in holdDict:
            if stock in trade_ratio:
                tmpDict[stock] = round((trade_ratio[stock] - holdDict[stock]), 2)
        tradeOrder = sorted(tmpDict.items(), key=lambda d:d[1], reverse=False)

        # 交易已有仓位的股票，从减仓的开始，腾空现金
        _tmplist = []
        for idx in tradeOrder:
            stock = idx[0]
            __fun_tradeStock(context, h[stock][-1], stock, trade_ratio[stock], trade_style)
            _tmplist.append(stock)

        # 交易新股票
        for i in range(len(trade_list)):
            stock = trade_list[i]
            if len(_tmplist) != 0 :
                if stock not in _tmplist:
                    __fun_tradeStock(context, h[stock][-1], stock, trade_ratio[stock], trade_style)
            else:
                __fun_tradeStock(context, h[stock][-1], stock, trade_ratio[stock], trade_style)

    def fun_tradeBond(self, context, stock, Value):
        h = history(1, '1d', 'close', stock, df=False)
        curPrice = h[stock]
        curValue = float(context.portfolio.positions[stock].total_amount * curPrice)
        deltaValue = abs(Value - curValue)
        if deltaValue > (curPrice*100):
            if Value > curValue:
                cash = context.portfolio.cash
                if cash > (curPrice*100):
                    self.fun_trade(context, stock, Value)
            else:
                # 如果是银华日利，多卖 100 股，避免个股买少了
                if stock == '511880.XSHG':
                    Value -= curPrice*100
                self.fun_trade(context, stock, Value)

    def unpaused(self, stocklist):
        current_data = get_current_data()
        return [s for s in stocklist if not current_data[s].paused]

    def remove_st(self, stocklist, statsDate):
        # 去除ST，*ST
        #statsDate = statsDate.strftime("%Y-%m-%d")
        st = get_extras('is_st', stocklist, start_date=statsDate, end_date=statsDate, df=True)
        st = st.loc[statsDate]
        stocklist = list(st[st==False].index)

        return stocklist

    # 剔除上市时间较短的产品
    def fun_delNewShare(self, context, equity, deltaday):
        deltaDate = context.current_dt.date() - dt.timedelta(deltaday)
    
        tmpList = []
        for stock in equity:
            if get_security_info(stock).start_date < deltaDate:
                tmpList.append(stock)
    
        return tmpList

    def fun_trade(self, context, stock, value):
        self.fun_setCommission(context, stock)
        position = context.portfolio.positions[stock]
        order = order_target_value(stock, value)
        if order != None and value == 0:
            if order.filled > 0:
                # 只要有成交，无论全部成交还是部分成交，则统计盈亏
                g.trade_stat.watch(stock, order.filled, position.avg_cost, position.price)

    def fun_setCommission(self, context, stock):
        if stock in context.moneyfund:
            set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0, close_commission=0, close_today_commission=0, min_commission=0), type='fund')
        else:
            set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
#策略概述：《小市值策略改进版》
#https://www.joinquant.com/post/2035?tag=new
#1.选择动态市盈率>0的所有股票，按市值从小到大排序，选择前100支候选
#2.剔除创业板，ST,*,退，停牌等股票
#3.选择市值最小的20只（前20只）候选
#4.给候选股票评分, 每天下午2点50分执行。
#lowPrice130 = 前130天内最低价格
#highPrice130 = 前130天内最高价格
#avg15 = 前15天均价
#currPrice = 当前价格
#score = (currPrice-lowPrice130)+(currPrice-highPrice130)+(currPrice-avg15)
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


from sqlalchemy import desc
import numpy as np
import pandas as pd
from scipy import stats

def initialize(context):
    # 对比标的
    set_benchmark('000300.XSHG') 
    g.stocks = []
    g.stockCount = 4
    g.buyStockCount = 10
    g.days = 0
    g.period = 3
    

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
            order_target_value(stock, 0)
            print('Sell: ',stock)
    #很关键！第一次写程序的时候没有这一句，会造成下面的无法买入。
    g.days = 0          

def Multi_Select_Stocks(context, data):
    stocks = get_all_securities(['stock'])
    #排除新股
    stocks = stocks[(context.current_dt.date() - stocks.start_date) > datetime.timedelta(60)].index
    #stocks  = stocks.index
    date=context.current_dt.strftime("%Y-%m-%d")
    st=get_extras('is_st', stocks, start_date=date, end_date=date, df=True)
    st=st.loc[date]
    stocks = list(st[st==False].index)
    stocks = unpaused(stocks)
    stocks = filterStarName(stocks)

    q = query(
        valuation.code,
        ).filter(
        valuation.pe_ratio > 0,
        valuation.code.in_(stocks)
    ).order_by(
        # 按市值升序排列
        valuation.market_cap.asc()
    ).limit(
        # 最多返回20个
        20
    )
    df = get_fundamentals(q)
    stocks = df.code.values

    stock_select={}
    for s in stocks:
        h = attribute_history(s, 130, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        lowPrice130 = h.low.min()
        highPrice130 = h.high.max()
        avg15 = data[s].mavg(15)
        currPrice = data[s].close
        score = (currPrice-lowPrice130)+(currPrice-highPrice130)+(currPrice-avg15)
        stock_select[s] = score
        
    dfs = pd.DataFrame(stock_select.values(),index=stock_select.keys())
    dfs.columns=['score']
    dfs=dfs.sort(columns='score',ascending=True)
    return dfs.index[:g.stockCount]

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    # 获得当前时间
    hour = context.current_dt.hour
    minute = context.current_dt.minute

    # 每天下午14:53调仓
    if hour ==14 and minute==50:
        lag = 20 # 回看前20天
        # 获得当前总资产
        value = context.portfolio.portfolio_value
        
        zs2 =  '000016.XSHG' #上证50指数
        zs8 =  '399005.XSHE' #中小板指数
    
        hs2 = getStockPrice(zs2, lag)
        hs8 = getStockPrice(zs8, lag)
        cp2 = data[zs2].close
        cp8 = data[zs8].close
        
        if (not isnan(hs2)) and (not isnan(cp2)):
            ret2 = (cp2 - hs2) / hs2;
        else:
            ret2 = 0
        if (not isnan(hs8)) and (not isnan(cp8)):
            ret8 = (cp8 - hs8) / hs8;
        else:
            ret8 = 0
        #print(ret2,ret8)
        
        #奇怪，低于101%时清仓，回测效果出奇得好。
        if ret2>0.01 or ret8>0.01 :   
            print('持有，每3天进行调仓')
            buy_stocks(context, data)
        else :
            print('清仓')
            sell_all_stocks(context)            

def buy_stocks(context, data):
    g.days += 1
    if g.days % g.period == 1:            
            
        buylist = Multi_Select_Stocks(context, data)
        
        #排除涨停、跌停股
        g.stocks = []
        for stock in buylist:
            if data[stock].low_limit < data[stock].close < data[stock].high_limit :
                g.stocks.append(stock)
            #已持有的涨停股，继续持有    
            elif (data[stock].close == data[stock].high_limit) and (stock in context.portfolio.positions.keys()):
                g.stocks.append(stock)
            if len(g.stocks)>=g.buyStockCount:
                break
        #print(g.stocks)
        set_universe(g.stocks)
        
        # close stock positions not in the current universe
        cntSuspension=0
        for stock in context.portfolio.positions.keys():
            if stock not in g.stocks:
                print('Rank Outof 10, Sell: ',stock)
                if order_target_value(stock, 0)==None :
                    #售出股票失败，则计数加1
                    cntSuspension +=1
        #由于可能出现售出股票失败（如停牌股票）的情况，需要删除后面几个多余的备选股票，是股票数保持4个
        g.stocks = g.stocks[:len(g.stocks)-cntSuspension]
        
        valid_count = 0
        for stock in context.portfolio.positions.keys():
            if context.portfolio.positions[stock].total_amount > 0:
                valid_count = valid_count + 1
        # place equally weighted orders
        if len(g.stocks) == 0 or valid_count >= len(g.stocks):
            #已有股票数量>=4个，则直接返回
            return
        
        for stock in g.stocks:
            order_target_value(stock, context.portfolio.portfolio_value/len(g.stocks))

#================================================================================
#每天开盘前
#================================================================================
def before_trading_start(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0)) 
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    # 设置手续费，每笔交易时的手续费是, 买入时券商佣金，卖出时券商佣金加千分之一印花税, 每笔交易最低扣5块钱
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.00025, sell_cost=0.00125, min_cost=5)) 
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))

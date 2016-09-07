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
    g.maxrbstd = {}
    g.exceptions = []
    g.stopstocks = 0
    #g.maxvalue = {} # 购买之后的最高价列表
    #g.stockrecommend = []
    

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
            curr_data = get_current_data()
            print curr_data[stock].name
    #很关键！第一次写程序的时候没有这一句，会造成下面的无法买入。
    g.days = 0          

def Multi_Select_Stocks(context, data):
    #更新排除之前被止盈止损的股票，允许其进入筛选备选股池
    for dstock in g.exceptions :
        # 当前价格相对于之前止盈、止损价格的涨跌幅度
        if (dstock['stopvalue'] != 0.0) and ((data[dstock['stock']].close-dstock['stopvalue'])/dstock['stopvalue'] > 0.15):
            g.exceptions.remove(dstock)
        elif (dstock['targetvalue'] != 0.0) and ((data[dstock['stock']].close-dstock['targetvalue'])/dstock['targetvalue'] < -0.15):
            g.exceptions.remove(dstock)

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
        indicator.eps > 0,
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
        #排除之前被止盈止损的股票
        skipit = False
        for dstock in g.exceptions :
            if dstock['stock'] == s :
                skipit = True
                break
        if skipit:
            print('排除之前被止盈止损的股票')
            print s
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
#            print '.............股票跌幅过大...............'
            return True
    return False

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    # 获得当前时间
    hour = context.current_dt.hour
    minute = context.current_dt.minute
        
    zs2 =  '000300.XSHG' #'000300.XSHG' #沪深300指数 #'000016.XSHG' #上证50指数
    zs8 =  '159902.XSHE' #'159902.XSHE' #'399005.XSHE' #中小板指数
    if context.current_dt>datetime.datetime(2008,7, 28):
        zs8 =  '399005.XSHE'

    lag = 20 # 回看前20天

#    if isThreeBlackCrows(zs2, data) and isThreeBlackCrows(zs8, data):
#        for stock in g.stocks:
#            if context.portfolio.positions[stock].sellable_amount > 0:
#                #有仓位就清仓
#    		    print ('三只乌鸦，清仓')
#    		    sell_all_stocks(context)
#    	#设置为2，避免当天再次买入股票
#    	g.days = 2
#        return

    # 检查止盈止损条件，并操作股票
    todobuy = False
    stockscrashed = 0
    for stock in g.stocks:
        if context.portfolio.positions[stock].sellable_amount > 0:
            # 每分钟监测，如果有更高价则记录之，如果从最高价回撤9.9%，则抛掉
            #try:
            #    if data[stock].close > g.maxvalue[stock] :
            #        g.maxvalue[stock] = data[stock].close
            #except KeyError:
            #    g.maxvalue[stock] = data[stock].close
            #if ((data[stock].close - g.maxvalue[stock]) / g.maxvalue[stock]) < -0.099 :
            #    if order_target_value(stock, 0) !=None :
            #        todobuy = True
            #        print('止损: ')
            #        g.exceptions.append({'stock': stock, 'days': 0})
            #        print('Sell: ',stock,data[stock].close,g.maxvalue[stock])
            #        curr_data = get_current_data()
            #        print curr_data[stock].name

            # 对当天下跌幅度过大的股票进行计数统计
            #if isStockBearish(stock, data, 5, 0.05, 0.02) :
            if data[stock].close  < 0.955*getStockPrice(stock, 1) :
                stockscrashed += 1
            # 当前价格超出止盈止损值，则卖出该股票
            dr3cur = (data[stock].close-context.portfolio.positions[stock].avg_cost)/context.portfolio.positions[stock].avg_cost
            if dr3cur <= g.maxrbstd[stock]['bstd']:
                if order_target_value(stock, 0) != None:
                    todobuy = True
                    g.stopstocks += 1
                    print('止损: ')
                    g.exceptions.append({'stock': stock, 'stopvalue': data[stock].close, 'targetvalue': 0.0})
                    print('Sell: ',stock)
                    curr_data = get_current_data()
                    print curr_data[stock].name
            elif dr3cur >= g.maxrbstd[stock]['maxr']*1.100:
                if order_target_value(stock, 0) != None:
                    todobuy = True
                    print('止盈: ')
                    g.exceptions.append({'stock': stock, 'stopvalue': 0.0, 'targetvalue': data[stock].close})
                    print('Sell: ',stock)
                    curr_data = get_current_data()
                    print curr_data[stock].name

    # 当天下跌幅度过大的股票超过一定比例，或者超过一半的所持股票止损，清仓观望
    if stockscrashed*4.0/3 >= len(g.stocks) or g.stopstocks*2 >= len(g.stocks) :
        todobuy = False
        if context.portfolio.positions_value > 0:
            #有仓位就清仓
    	    print ('多只股票达到止损线，清仓')
    	    sell_all_stocks(context)
    	    # 修整1天，设置为2，避免当天再次买入股票
    	    g.days = 2

    # 检查二八指标是否达到降幅下限，如达到则清仓观望
    if context.portfolio.positions_value > 0:
        hs2 = getStockPrice(zs2, lag)
        hs8 = getStockPrice(zs8, lag)
        cp2 = data[zs2].close
        cp8 = data[zs8].close

        cmp2result = True
        cmp8result = True
        if (not isnan(hs2)) and (not isnan(cp2)):
            ret2 = (cp2 - hs2) / hs2;
            if ret2>-0.004 :
                cmp2result = False
        else:
            ret2 = 0
        if (not isnan(hs8)) and (not isnan(cp8)):
            ret8 = (cp8 - hs8) / hs8;
            if ret8>-0.004 :
                cmp8result = False
        else:
            ret8 = 0
        if (cmp2result and cmp8result) or (isStockBearish(zs2, data, 5, 0.04, 0.03) or isStockBearish(zs8, data, 5, 0.04, 0.03)) :
            #有仓位就清仓
    	    print ('二八未满足条件，清仓')
    	    sell_all_stocks(context)
    	    # 修整1天，设置为2，避免当天再次买入股票
    	    g.days = 2

#    if (minute%30 == 0) :
#        hs2 = getStockPrice(zs2, lag)
#        hs8 = getStockPrice(zs8, lag)
#        cp2 = data[zs2].close
#        cp8 = data[zs8].close

#        if (not isnan(hs2)) and (not isnan(cp2)):
#            ret2 = (cp2 - hs2) / hs2;
#        else:
#            ret2 = 0
#        if (not isnan(hs8)) and (not isnan(cp8)):
#            ret8 = (cp8 - hs8) / hs8;
#        else:
#            ret8 = 0
        #print(ret2,ret8)
        
        #奇怪，低于101%时清仓，回测效果出奇得好。
#        if ret2>0.01 or ret8>0.01 :  
#            stockrecommend = Multi_Select_Stocks(context, data)
#            stockrecommend.sort()
#            if cmp(g.stockrecommend, stockrecommend) != 0 :
#                g.stockrecommend = stockrecommend
#                print '推荐股票'
#                print g.stockrecommend
#        elif g.stockrecommend != []:
#            g.stockrecommend = []
#            print('不推荐买入股票')

    # 每天下午14:53调仓
    if hour ==14 and minute==50:
        # 获得当前总资产
        value = context.portfolio.portfolio_value
    
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
        print '----二八指数20日涨幅----'
        print(ret2,ret8)
        
        #奇怪，低于101%时清仓，回测效果出奇得好。
        if ret2>0.01 or ret8>0.01 :  
            g.days += 1
            if todobuy or (g.days % g.period == 1):            
                print('持有，每3天进行调仓')
                buy_stocks(context, data)
                update_maxr_bstd(context)
        else :
            print('清仓')
            sell_all_stocks(context)

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
            if order_target_value(stock, 0)==None :
                #售出股票失败（如停牌股票）的情况，需要删除后面几个多余的备选股票，使股票数保持4个
                g.stocks.pop()
                g.stocks.insert(0, stock)
            print('Rank Outof 10, Sell: ',stock)
            curr_data = get_current_data()
            print curr_data[stock].name

    #初始化新选中的股票的最高价
    #for stock in g.stocks :
    #    if stock not in context.portfolio.positions.keys():
    #        g.maxvalue[stock] = data[stock].close

    valid_count = 0
    for stock in context.portfolio.positions.keys():
        if context.portfolio.positions[stock].total_amount > 0:
            valid_count = valid_count + 1
    # place equally weighted orders
    #已有股票数量>=4个，则直接返回
    if valid_count < len(g.stocks):
        for stock in g.stocks:
            order_target_value(stock, context.portfolio.portfolio_value/len(g.stocks))
            print('buy: ',stock)
            curr_data = get_current_data()
            print curr_data[stock].name

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
    #for stock in context.portfolio.positions.keys():
    #    if stock in g.stocks:
    #        try:
    #            maxvalue[stock] = g.maxvalue[stock]
    #        except KeyError:
    #            maxvalue[stock] = 0
    #    else:
    #        h = attribute_history(stock, 1, unit='1d', fields=('close'), skip_paused=True)
    #        if (len(h) > 0) and (not isnan(h.close[-1])):
    #            maxvalue[stock] = h.close[-1]
    #        else:
    #            maxvalue[stock] = 0
    #g.maxvalue = maxvalue
    
    g.stopstocks = 0

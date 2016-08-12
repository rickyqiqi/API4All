'''
=================================================
总体回测前设置参数和回测
=================================================
'''
def initialize(context):
    set_params()    #1设置策参数
    set_variables() #2设置中间变量
    set_backtest()  #3设置回测条件

#1 设置参数
def set_params():
    # 设置基准收益
    set_benchmark('000300.XSHG') 
    g.lag = 20
    g.hour = 14
    g.minute = 53
    
    g.hs =  '000300.XSHG' #300指数
    g.zz =  '000905.XSHG'#500指数
        
    g.ETF300 = '510300.XSHG'#'510300.XSHG'
    g.ETF500 = '510500.XSHG'#'510500.XSHG'


#2 设置中间变量
def set_variables():
    return

#3 设置回测条件
def set_backtest():
    set_option('use_real_price', True) #用真实价格交易
    log.set_level('order', 'error')



'''
=================================================
每天开盘前
=================================================
'''
#每天开盘前要做的事情
def before_trading_start(context):
    set_slip_fee(context) 

#4 
# 根据不同的时间段设置滑点与手续费

def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0)) 
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5)) 
        
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
            
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
                
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))




'''
=================================================
每日交易时
=================================================
''' 
def handle_data(context, data):
    # 获得当前时间
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    
    # 每天收盘时调整仓位
    if hour == g.hour and minute == g.minute:
        signal = get_signal(context)

        lag = 20 # 回看前20天
        # 获得当前总资产
        value = context.portfolio.portfolio_value

        zs2 =  '000016.XSHG' #上证50指数
        zs8 =  '399006.XSHE' #创业板指数

        hs2 = getStockPrice(zs2, lag)[0]
        hs8 = getStockPrice(zs8, lag)[0]
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
        else :
            print('清仓')
            signal = 'sell_the_stocks'
            
        if isThreeBlackCrows('000016.XSHG', data):
            signal = 'sell_the_stocks'

        if signal == 'sell_the_stocks':
            sell_the_stocks(context)
        elif signal == 'ETF300' or signal == 'ETF500':
            buy_the_stocks(context,signal)

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

#5
#获取信号
def get_signal(context):
    
    #沪深300与中证500的当日收盘价
    hs300,cp300 = getStockPrice(g.hs, g.lag)
    zz500,cp500  = getStockPrice(g.zz, g.lag)
        
    #计算前20日变动
    hs300increase = (cp300 - hs300) / hs300
    zz500increase = (cp500 - zz500) / zz500
        
    hold300 = context.portfolio.positions[g.ETF300].total_amount
    hold500 = context.portfolio.positions[g.ETF500].total_amount
    
    if (hs300increase<=0 and hold300>0) or (zz500increase<=0 and hold500>0):
        return 'sell_the_stocks'
    elif hs300increase>zz500increase and hs300increase>0 and (hold300==0 and hold500==0):
        return 'ETF300'
    elif zz500increase>hs300increase and zz500increase>0 and (hold300==0 and hold500==0):
        return 'ETF500'

#6
#取得股票某个区间内的所有收盘价（用于取前20日和当前 收盘价）
def getStockPrice(stock, interval):
    h = attribute_history(stock, interval, unit='1d', fields=('close'), skip_paused=True)
    return (h['close'].values[0],h['close'].values[-1])

#7
#卖出股票
def sell_the_stocks(context):
    for stock in context.portfolio.positions.keys():
        return (log.info("Selling %s" % stock), order_target_value(stock, 0))

#8
#买入股票
def buy_the_stocks(context,signal):
    return (log.info("Buying %s"% signal ),order_value(eval('g.%s'% signal), context.portfolio.cash))
    
'''
=================================================
每日收盘后（本策略中不需要）
=================================================
'''  
def after_trading_end(context):
    return


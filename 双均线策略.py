#双均线策略
# 2015-01-01 到 2016-03-08, ￥2000000, 每天

'''
================================================================================
总体回测前
================================================================================
'''
#总体回测前要做的事情
def initialize(context):
    set_params()    #1设置策参数
    set_variables() #2设置中间变量
    set_backtest()  #3设置回测条件
    
#1
#设置策略参数
def set_params():
    g.tc=15  # 调仓频率
    g.N=4 #持仓数目
    g.security = ["601688.XSHG","000513.XSHE","002736.XSHE","000333.XSHE","000651.XSHE","000413.XSHE"]#设置股票池

#2
#设置中间变量
def set_variables():
    return

#3
#设置回测条件
def set_backtest():
    set_option('use_real_price', True) #用真实价格交易
    log.set_level('order', 'error')






'''
================================================================================
每天开盘前
================================================================================
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
================================================================================
每天交易时
================================================================================
'''
def handle_data(context, data):
    # 将总资金等分为g.N份，为每只股票配资
    capital_unit = context.portfolio.portfolio_value/g.N
    toSell = signal_stock_sell(context,data)
    toBuy = signal_stock_buy(context,data)
    # 执行卖出操作以腾出资金
    for i in range(len(g.security)):
        if toSell[i]==1:
            order_target_value(g.security[i],0)
    # 执行买入操作
    for i in range(len(g.security)):
        if toBuy[i]==1:
            order_target_value(g.security[i],capital_unit)  
    if not (1 in toBuy) or (1 in toSell):
        # log.info("今日无操作")
        send_message("今日无操作")


#5
#获得卖出信号
#输入：context, data
#输出：sell - list
def signal_stock_sell(context,data):
    sell = [0]*len(g.security)
    for i in range(len(g.security)):
    # 算出今天和昨天的两个指数移动均线的值，我们这里假设长线是60天，短线是1天(前一天的收盘价)
        (ema_long_pre,ema_long_now) = get_EMA(g.security[i],60,data)
        (ema_short_pre,ema_short_now) = get_EMA(g.security[i],1,data)
        # 如果短均线从上往下穿越长均线，则为死叉信号，标记卖出
        if ema_short_now < ema_long_now and ema_short_pre > ema_long_pre and context.portfolio.positions[g.security[i]].sellable_amount > 0:
            sell[i]=1
    return sell
        

#6
#获得买入信号
#输入：context, data
#输出：buy - list
def signal_stock_buy(context,data):
    buy = [0]*len(g.security)
    for i in range(len(g.security)):
    # 算出今天和昨天的两个指数移动均线的值，我们这里假设长线是60天，短线是1天(前一天的收盘价)
        (ema_long_pre,ema_long_now) = get_EMA(g.security[i],60,data)
        (ema_short_pre,ema_short_now) = get_EMA(g.security[i],1,data)
        # 如果短均线从下往上穿越长均线，则为金叉信号，标记买入
        if ema_short_now > ema_long_now and ema_short_pre < ema_long_pre and context.portfolio.positions[g.security[i]].sellable_amount == 0 :
            buy[i]=1
    return buy


#7
# 计算移动平均线数据
# 输入：股票代码-字符串，移动平均线天数-整数
# 输出：算术平均值-浮点数
def get_MA(security_code,days):
    # 获得前days天的数据，详见API
    a=attribute_history(security_code, days, '1d', ('close'))
    # 定义一个局部变量sum，用于求和
    sum=0
    # 对前days天的收盘价进行求和
    for i in range(1,days+1):
        sum+=a['close'][-i]
    # 求和之后除以天数就可以的得到算术平均值啦
    return sum/days

#8
# 计算指数移动平均线数据
# 输入：股票代码-字符串，移动指数平均线天数-整数，data
# 输出：今天和昨天的移动指数平均数-浮点数
def get_EMA(security_code,days,data):
    # 如果只有一天的话,前一天的收盘价就是移动平均
    if days==1:
    # 获得前两天的收盘价数据，一个作为上一期的移动平均值，后一个作为当期的移动平均值
        t = attribute_history(security_code, 2, '1d', ('close'))
        return t['close'][-2],t['close'][-1]
    else:
    # 如果全局变量g.EMAs不存在的话，创建一个字典类型的变量，用来记录已经计算出来的EMA值
        if 'EMAs' not in dir(g):
            g.EMAs={}
        # 字典的关键字用股票编码和天数连接起来唯一确定，以免不同股票或者不同天数的指数移动平均弄在一起了
        key="%s%d" %(security_code,days)
        # 如果关键字存在，说明之前已经计算过EMA了，直接迭代即可
        if key in g.EMAs:
            #计算alpha值
            alpha=(days-1.0)/(days+1.0)
            # 获得前一天的EMA（这个是保存下来的了）
            EMA_pre=g.EMAs[key]
            # EMA迭代计算
            EMA_now=EMA_pre*alpha+data[security_code].close*(1.0-alpha)
            # 写入新的EMA值
            g.EMAs[key]=EMA_now
            # 给用户返回昨天和今天的两个EMA值
            return (EMA_pre,EMA_now)
        # 如果关键字不存在，说明之前没有计算过这个EMA，因此要初始化
        else:
            # 获得days天的移动平均
            ma=get_MA(security_code,days) 
            # 如果滑动平均存在（不返回NaN）的话，那么我们已经有足够数据可以对这个EMA初始化了
            if not(isnan(ma)):
                g.EMAs[key]=ma
                # 因为刚刚初始化，所以前一期的EMA还不存在
                return (float("nan"),ma)
            else:
                # 移动平均数据不足days天，只好返回NaN值
                return (float("nan"),float("nan"))





'''
================================================================================
每天收盘后
================================================================================
'''
# 每日收盘后要做的事情（本策略中不需要）
def after_trading_end(context):
    return



#�������
# 2012-01-01 �� 2016-03-10, ��1000000, ����
'''
================================================================================
����ز�ǰ
================================================================================
'''
#����ز�ǰҪ��������
def initialize(context):
    set_params()        #1���ò߲���
    set_variables()     #2�����м����
    set_backtest()      #3���ûز�����
    
#1
#���ò��Բ���
def set_params():
    g.security = '000063.XSHE'
    # ϵͳ1���е�trailing date
    g.short_in_date = 20
    # ϵͳ2���е�trailing date
    g.long_in_date = 55
    # ϵͳ1 exiting market trailing date
    g.short_out_date = 10
    # ϵͳ2 exiting market trailing date
    g.long_out_date = 20
    # g.dollars_per_share�Ǳ�Ĺ�Ʊÿ����һ����С��λ��1�ֹ�Ʊ���ܼ۸�仯����
    # �ڹ�����С�仯����0.01Ԫ�����Ծ���0.01��100=1
    g.dollars_per_share = 1
    # �ɳ��ܵ������ʧ��
    g.loss = 0.1
    # �����������ʧ�ʣ��������Ϊ��
    g.adjust = 0.8
    # ����Nֵ������
    g.number_days = 20
    # �������Ԫ
    g.unit_limit = 4
    # ϵͳ1������ռ�ܽ�����
    g.ratio = 0.8
    
#2
#�����м����
def set_variables():
    # ��ʼ��Ԫ
    g.unit = 1000
    # A list storing info of N
    g.N = []
    # Record the number of days for this trading system
    g.days = 0
    # ϵͳ1��ͻ�Ƽ۸�
    g.break_price1 = 0
    # ϵͳ2��ͻ�Ƽ۸�
    g.break_price2 = 0
    # ϵͳ1���Ĳ���
    g.sys1 = 0
    # ϵͳ2���Ĳ���
    g.sys2 = 0
    # ϵͳ1ִ����ϵͳ2��ִ��
    g.system1 = True

#3
#���ûز�����
def set_backtest():
    # ��Ϊ�жϲ��Ժû���һϵ�з���ֵ����Ļ�׼
    set_benchmark(g.security)
    set_option('use_real_price',True) #����ʵ�۸���
    log.set_level('order','error') # ���ñ���ȼ�




'''
================================================================================
ÿ�쿪��ǰ
================================================================================
'''
#ÿ�쿪��ǰҪ��������
def before_trading_start(context):
    set_slip_fee(context) 


#4 ���ݲ�ͬ��ʱ������û�����������
def set_slip_fee(context):
    # ����������Ϊ0
    set_slippage(FixedSlippage(0)) 
    # ���ݲ�ͬ��ʱ�������������
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
ÿ�콻��ʱ
================================================================================
'''
# �����ӻز�
def handle_data(context, data):
    dt = context.current_dt # ��ǰ����
    current_price = data[g.security].price # ��ǰ�۸�N
    if dt.hour==9 and dt.minute==30:
        g.days += 1
        calculate_N() #����N��ֵ
    if g.days > g.number_days:
        # ��ǰ���еĹ�Ʊ���ֽ���ܼ�ֵ
        value = context.portfolio.portfolio_value
        # �ɻ��ѵ��ֽ�
        cash = context.portfolio.cash 
        if g.sys1 == 0 and g.sys2 == 0:
            # ����ʧ�ʴ���g.loss�����������С���ɳ����ֽ���ܼ�ֵ
            if value < (1-g.loss)*context.portfolio.starting_cash:
                cash *= g.adjust
                value *= g.adjust
                
        # ������Ԫ�����ļ۸�
        dollar_volatility = g.dollars_per_share*(g.N)[-1]
        # �������ԣ����������ĵ�λ
        g.unit = value*0.01/dollar_volatility

        # ϵͳ1�Ĳ���
        g.system1 = True
        if g.sys1 == 0:
            market_in(current_price, g.ratio*cash, g.short_in_date)
        else:
            stop_loss(current_price)
            market_add(current_price, g.ratio*cash, g.short_in_date)    
            market_out(current_price, g.short_out_date)

        # ϵͳ2�Ĳ���
        g.system1 == False
        if g.sys2==0:
            market_in(current_price, (1-g.ratio)*cash, g.long_in_date)
        else:
            stop_loss(current_price)
            market_add(current_price, (1-g.ratio)*cash, g.long_in_date)
            market_out(current_price, g.long_out_date)   
  

#5
# ���㵱ǰN��ֵ
# ���룺none
# �����N��ֵ�ĸ����б�-list����
def calculate_N():
    # �����������С�ڵ���20��
    if g.days <= g.number_days:
        price = attribute_history(g.security, g.days, '1d',('high','low','close'))
        lst = []
        for i in range(0, g.days):
            h_l = price['high'][i]-price['low'][i]
            h_c = price['high'][i]-price['close'][i]
            c_l = price['close'][i]-price['low'][i]
            # ���� True Range
            True_Range = max(h_l, h_c, c_l)
            lst.append(True_Range)
        # ����ǰg.days��С�ڵ���20�����True_Rangeƽ��ֵ������ǰN��ֵ��
        current_N = np.mean(np.array(lst))
        (g.N).append(current_N)
        
    # ���������������20��
    else:
        price = attribute_history(g.security, 1, '1d',('high','low','close'))
        h_l = price['high'][0]-price['low'][0]
        h_c = price['high'][0]-price['close'][0]
        c_l = price['close'][0]-price['low'][0]
        # Calculate the True Range
        True_Range = max(h_l, h_c, c_l)
        # ����ǰg.number_days������20�����True_Rangeƽ��ֵ������ǰN��ֵ��
        current_N = (True_Range + (g.number_days-1)*(g.N)[-1])/g.number_days
        (g.N).append(current_N)


#6
# ���У�����ϵͳ1��ϵͳ2�Ƿ�Ӧ�����У�����ϵͳ1��ϵͳ2��ͻ�Ƽ۸�
# ���꽫�����ʽ��Ϊ2���֣�һ�����ʽ�ϵͳ1ִ�У�һ�����ʽ�ϵͳ2ִ��
# ���룺��ǰ�۸�-float, �ֽ�-float, ����-int
# �����none
def market_in(current_price, cash, in_date):
    # Get the price for the past "in_date" days
    price = attribute_history(g.security, in_date, '1d', ('close'))
    # Build position if current price is higher than highest in past
    if current_price > max(price['close']):
        # ���������ù�Ʊ�Ĺ���
        num_of_shares = cash/current_price
        if num_of_shares >= g.unit:
            print "����"
            print current_price
            print max(price['close'])
            if g.system1 == True:
                if g.sys1 < int(g.unit_limit*g.unit):
                    order(g.security, int(g.unit))
                    g.sys1 += int(g.unit)
                    g.break_price1 = current_price
            else:
                if g.sys2 < int(g.unit_limit*g.unit):
                    order(g.security, int(g.unit))
                    g.sys2 += int(g.unit)
                    g.break_price2 = current_price


#7
# �Ӳֺ���
# ���룺��ǰ�۸�-float, �ֽ�-float, ����-int
# �����none
def market_add(current_price, cash, in_date):
    if g.system1 == True:
        break_price=g.break_price1
    else:
        break_price=g.break_price2
    # ÿ����0.5N���Ӳ�һ����Ԫ
    if current_price >= break_price + 0.5*(g.N)[-1]: 
        num_of_shares = cash/current_price
        # �Ӳ�
        if num_of_shares >= g.unit: 
            print "�Ӳ�"
            print g.sys1
            print g.sys2
            print current_price
            print break_price + 0.5*(g.N)[-1]
       
            if g.system1 == True:
                if g.sys1 < int(g.unit_limit*g.unit):
                    order(g.security, int(g.unit))
                    g.sys1 += int(g.unit)
                    g.break_price1 = current_price
            else:
                if g.sys2 < int(g.unit_limit*g.unit):
                    order(g.security, int(g.unit))
                    g.sys2 += int(g.unit)
                    g.break_price2 = current_price


#8
# �볡����
# ���룺��ǰ�۸�-float, ����-int
# �����none
def market_out(current_price, out_date):
    # Function for leaving the market
    price = attribute_history(g.security, out_date, '1d', ('close'))
    # ����ǰ�۸����ǰout_date������̼۵���Сֵ, ���������гֲ�
    if current_price < min(price['close']):
        print "�볡"
        print current_price
        print min(price['close'])
        if g.system1 == True:
            if g.sys1>0:
                order(g.security, -g.sys1)
                g.sys1 = 0
        else:
            if g.sys2>0:
                order(g.security, -g.sys2)
                g.sys2 = 0


#9
# ֹ����
# ���룺��ǰ�۸�-float
# �����none
def stop_loss(current_price):
    # ��ʧ����2N��������Ʊ
    if g.system1 == True:
        break_price = g.break_price1
    else:
        break_price = g.break_price2
    # If the price has decreased by 2N, then clear all position
    if current_price < (break_price - 2*(g.N)[-1]):
        print "ֹ��"
        print current_price
        print break_price - 2*(g.N)[-1]
        if g.system1 == True:
            order(g.security, -g.sys1)
            g.sys1 = 0  
        else:
            order(g.security, -g.sys2)
            g.sys2 = 0




'''
================================================================================
ÿ�����̺�
================================================================================
'''
# ÿ�����̺�Ҫ�������飨�������в���Ҫ��
def after_trading_end(context):
    return
################################################################################
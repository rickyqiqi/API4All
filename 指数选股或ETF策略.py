#���Ը�������С��ֵ���ԸĽ��桷
#https://www.joinquant.com/post/2035?tag=new
#1.ѡ��eps>0�����й�Ʊ������ֵ��С��������ѡ��ǰ100֧��ѡ
#2.�޳���ҵ�壬ST,*,�ˣ�ͣ�Ƶȹ�Ʊ
#3.ѡ����ֵ��С��20ֻ��ǰ20ֻ����ѡ
#4.����ѡ��Ʊ����, ÿ������2��50��ִ�С�
#lowPrice130 = ǰ130������ͼ۸�
#highPrice130 = ǰ130������߼۸�
#avg15 = ǰ15�����
#currPrice = ��ǰ�۸�
#score = ((currPrice-lowPrice130)+(currPrice-highPrice130)+(currPrice-avg15))/currPrice
#5.����ѡ��Ʊ��score�÷֣���С��������ѡ����С��4֧�ֲ֡�
#6.�ֹ�3���ֻ������һ���ľͼ������У���һ���ľͻ�����
#7.����ֹ��ʹ����֤50������С��R ָ���������С��20��ǰ��101%������ղ�λ�����ס�
################################################################################
#2016/8/9
#����ֹ����ԣ����е�˵©�ˡ�
#��λ��Ʊʹ�ø���ֹ��ÿ���Ӽ�⣬����и��߼����¼֮���������߼ۻس�9.9%�����׵�������14��50��������ѡ�ɳֲ֡�
#8.ʶ����̡���ֻ��ѻ������̬��������֣��������֡�
################################################################################
#2016/8/13
#9.���ݲ�ͬ��ʱ������û�����������
#10.�޳���ҵ��
#11.ɾ���ˡ���ֻ��ѻ����̬ʶ��
#12.�޸�����С��ָ�������ҵ��ָ����Ϊ�����еİ˲���
#13.������bstd��Ϊ�����ڳֲ�3���ڣ��ܳ��ܵ��������ж�
#14.ÿ���Ӽ��ɼۣ�����и��߼����¼֮���������߼ۻس�9.9%�����׵�


import types
import json
from sqlalchemy import desc
import numpy as np
import pandas as pd
from scipy import stats
from autotraderintf import *
from mailintf import *

# ��ȡ����ֵ
def get_variables_updated(context, addstring):
    valueUpdated = False
    # ����ֵ�ļ�
    if g.real_market_simulate:
        configfilename = 'config/real_%s.conf' %(addstring)
    else:
        configfilename = 'config/loop_%s.conf' %(addstring)

    if True: #try:
        jsoncontent = read_file(configfilename)
        content = json.loads(jsoncontent)

        # ����µ���ֵд����
        if content.has_key('g.policy_name' ) and type(content["g.policy_name"]) == types.UnicodeType \
            and g.policy_name != content["g.policy_name"]:
            g.policy_name = content["g.policy_name"]
            valueUpdated = True
        if content.has_key('g.capitalValue') and type(content["g.capitalValue"]) == types.IntType \
            and g.capitalValue != content["g.capitalValue"]:
            # �ز��ģ�������ý׶����õĳ�ʼ�ܽ�� - �����ܽ�� = ����
            currentProfit = (context.portfolio.total_value - g.totalValueDifference) - g.capitalValue
            g.capitalValue = content["g.capitalValue"]
            valueUpdated = True
            # ����ܲ�ֵ = ��ǰ��ֵ - �±����ܽ�� - ֮ǰ������
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
        if content.has_key('g.index_pool') and type(content["g.index_pool"]) == types.ListType \
            and g.index_pool != content["g.index_pool"]:
            g.index_pool = content["g.index_pool"]
            valueUpdated = True

    #except:
    #    log.error("�����ļ�%s��ȡ����" %(configfilename))

    return valueUpdated

def initialize(context):# �����汾��
    # additional string in variable configuration file name
    g.addstring = "IndexETF"

    g.policy_name = 'ָ��ѡ�ɻ�ETF����'

    # ��ʼ�ܽ���������ܽ��
    g.capitalValue = 50000
    # ����ܲ�ֵ = ��ǰ��ֵ - �±����ܽ�� - ֮ǰ������(0)
    g.totalValueDifference = context.portfolio.total_value - g.capitalValue

    # �Ƿ��ڵ���ģʽ��
    g.indebug = False
    # ����״̬��Ӧ��
    g.online_response_code = 0

    # run_params: ��ʾ�˴����еĲ���, ����������
    # start_date: �ز�/ģ�⿪ʼ����, datetime.date����
    # end_date: �ز�/ģ���������, datetime.date����
    # type: ���з�ʽ, ���������ַ���֮һ
    # 'simple_backtest': �ز�, ͨ��������������С�����
    # 'full_backtest': �ز�, ͨ����������лز⡯����
    # 'sim_trade': ģ�⽻��
    g.real_market_simulate = False
    if context.run_params.type == 'sim_trade':
        # ʹ����ʵ�۸�ز�(ģ�����Ƽ���ˣ��ز���ע��)
        set_option('use_real_price', True)
        g.real_market_simulate = True

    # ����ͳ��ģ��
    g.trade_stat = trade_stat()

    g.zs1 =  '000016.XSHG' #��֤50ָ��
    g.zs2 =  '000300.XSHG' #'000300.XSHG' #����300ָ��
    g.zs8 =  '399101.XSHE' #'159902.XSHE' #'399005.XSHE' #��С��ָ��

    g.lag = 20 # �ؿ�ǰ20��

    g.ret1 = 0
    g.ret2 = 0
    g.ret8 = 0
    g.ret_last5d = []
    g.gradient1 = 0
    g.gradient2 = 0
    g.gradient8 = 0

    # �Աȱ��
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
    # ��Ҫ���ֱ��
    g.todobuy = False
    g.maxrbstd = {}
    g.exceptions = []
    g.stockscrashed = []
    g.stopstocks = []
    #g.maxvalue = {} # ����֮�����߼��б�
    #g.minutesinlowprice = {} # �ɼ۵�����߼����½�����ֵ��ʱ�����ӣ�
    #g.minutesthreshold = 120 # �ɼۼ�ʱ��ֵ�����ӣ�
    #g.topdropthreshold = 0.05 # �ɼ۵�����߼����½�����ֵ
    g.stockrecommend = []
    g.recommend_freq = 5
    # ��Ʊ��ͷ���Ƽӷ������
    g.rank_stock_score_plus_allowed = True
    if g.rank_stock_score_plus_allowed:
        # ���Զ�ͷ���Ƶľ��߳���
        g.ma_lengths = [5,10,20,60,120]
        # ��������زȵľ��߳���
        g.test_ma_length = 10
        # ����ʱ�زȵ�����վס�ľ���
        g.stand_ma_length = 10
        # ��ͷ��������
        g.in_trend_days = 7

    # �����Ƿ���autotrader֪ͨ
    g.autotrader_inform_enabled = False

    # ָ����Ʊ�б�
    # "510050.XSHG" - ������֤50ETF
    # "160706.XSHE" - ��ʵ����300ETF����LOF
    # "159902.XSHE" - ������С��ETF
    g.stock_appointed = []
    # ��ѡ��Ʊ�أ��ձ�ʾ���й�Ʊ��ѡ
    g.stock_candidates = []
    # ָ����
    # '000016.XSHG' - ��֤50ָ��
    # '000300.XSHG' - ����300ָ��
    # '399005.XSHE' - ��С��ָ��
    g.index_pool = []

    # ��ӡ���Բ���
    log_param()

def log_param():
    log.info("---------------------------------------------")
    log.info("��������: %s" %(g.policy_name))
    log.info("�Ƿ��ǵ���ģʽ: %s" %(g.indebug))
    log.info("������Ƶ��: %d��" %(g.period))
    log.info("����ʱ��: %s:%s" %(g.adjust_position_hour, g.adjust_position_minute))
    log.info("��ʼ�ܽ���������ܽ��: %d" %(g.capitalValue))
    log.info("�����Ʊ��Ŀ: %d" %(g.stockCount))
    if g.maxPE != None and g.minPE != None and g.maxPE > g.minPE :
        log.info("ѡ��PEֵ��Χ: %d~%d" %(g.minPE, g.maxPE))
    if g.PEG != None :
        log.info("ѡ��PEGָ��(��ӯ�����ӯ����������)ֵ: %.02f%%" %(g.PEG*100))
    if g.minEPS != None :
        log.info("ѡ����СEPSֵ: %d" %(g.minEPS))
    if g.minIncNetProfit != None :
        log.info("ѡ����С������������ֵ: %.02f%%" %(g.minIncNetProfit*100))
    if g.incReturnInROE != None :
        log.info("ѡ�ɿ۳��Ǿ������澻�ʲ�������ռ��ֵ: %.02f%%" %(g.incReturnInROE*100))
    #log.info("�ɼ۵�����߼����½�����ֵ: %.02f%%" %(g.topdropthreshold*100))
    log.info("�Ƽ���ƱƵ��: %d����" %(g.recommend_freq))
    log.info("�Ƿ�����Ʊ��ͷ���Ƽӷ�: %s" %(g.rank_stock_score_plus_allowed))
    log.info("�Ƿ���autotrader֪ͨ: %s" %(g.autotrader_inform_enabled))

    if len(g.stock_appointed) > 0:
        log.info("ָ����Ʊ�б�: %s" %(str(g.stock_appointed)))
    else:
        if len(g.index_pool) > 0:
            log.info("ָ����: %s" %(str(g.index_pool)))
        elif len(g.stock_candidates) > 0:
            log.info("��ѡ��Ʊ��: %s" %(str(g.stock_candidates)))
    log.info("---------------------------------------------")

# ��ȡǰn����λʱ�䵱ʱ�����̼�
def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, ('close'), True)['close'][0]

def getStockPrice(stock, interval):
    h = attribute_history(stock, interval, unit='1d', fields=('close'), skip_paused=True)
    return h['close'].values[0]

def unpaused(stockspool):
    current_data=get_current_data()
    return [s for s in stockspool if not current_data[s].paused]    

#���˵���*����ST�༰��ҵ���Ʊ
def filterStarName(stock_list):
    curr_data = get_current_data()
    return  [stock for stock in stock_list if 'ST' not in curr_data[stock].name and
        '*' not in curr_data[stock].name and '��' not in curr_data[stock].name and 
        not stock.startswith('300')]

def sell_all_stocks(context):
    for stock in context.portfolio.positions.keys():
            position = context.portfolio.positions[stock]
            close_position(context, position)
            curr_data = get_current_data()
            log.info("Sell: %s(%s)" %(curr_data[stock].name, stock))
    #�ܹؼ�����һ��д�����ʱ��û����һ�䣬�����������޷����롣
    g.days = 0          

# ���������ź�
# �������ж�ͷ���ƹ�Ʊ
# ����һlist�����������������ڵ��ǲȵ��������ߵĹ�Ʊ
def buy_signal(available_stocks, context):
    in_trend_stocks = get_in_trends(available_stocks, context)

    # ������list 
    signal = []
    # �������ж�ͷ���ƹ�Ʊ
    for security in in_trend_stocks:
        # ��ȡ��ʷ���̼�
        past_prices = attribute_history(security,g.test_ma_length, '1d', 'close', skip_paused = True)
        # �������
        test_ma = sum(past_prices).iloc[0] / g.test_ma_length
        # ��ȡվס��������
        past_prices_2 = attribute_history(security, g.stand_ma_length, '1d', 'close', skip_paused= True) 
        # �������
        stand_ma = sum(past_prices_2).iloc[0] / g.stand_ma_length
        # ��ȡ������Ϣ
        previous_history = attribute_history(security, 1, '1d', ['close','low'])
        # �������̼�
        current_price = previous_history['close'].iloc[0]
        # ������ͼ�
        previous_low = previous_history['low'].iloc[0]
        # ����ù�Ʊû�гֲ֣�����ǰ���̼۵���Ŀ�����
        if current_price <= test_ma :
            # �����ź�list 
            signal.append(security)
    # ����ź�
    return(signal)

# ��ȡ���ж�ͷ���ƹ�Ʊ
# ����һlist��Ч��Ʊ
# ���һlist��Ϊ���з��ϴ�С�����������дӴ�С�Ĺ�Ʊ
def get_in_trends(available_stocks, context):
    # ������Ҫ��ѡ�Ĺ�Ʊlist��ֻҪ���ֹ�Ʊ���������߲����϶�ͷ���ƣ��ͼ���ɾ��������ֹͣ����
    stockselected = []
    # ����������Ч��Ʊ
    for security in available_stocks:
        # ��ȡ�ma����
        longest_ma = max(g.ma_lengths)
        # ��������
        date = context.current_dt
        # ��ȡ��ȥ�۸�
        all_past_prices = attribute_history(security,longest_ma + g.in_trend_days -1, '1d', 'close',  skip_paused = True)
        # �����϶����Ƶ�ÿһ��
        for day in range(g.in_trend_days):
            # ɸȥβ����-day������
            if day == 0:
                past_prices = all_past_prices
            else:
                past_prices = all_past_prices[:-day]
            # �����վ���ֵlist 
            mas = []
            # �������о��߳���
            for length in g.ma_lengths:
                # ��ȡ��Ӧ����
                ma_data = past_prices[-length:]
                # ���ֵ
                ma = sum(ma_data).iloc[0]/ length
                # ����list 
                mas.append(ma)
            # �Ӵ�С���о�ֵlist 
            sorted_mas = sorted(mas)
            sorted_mas.reverse()
            # �������֮���֮ǰ��
            if mas == sorted_mas:
                # ������ѡ��������
                stockselected.append(security)
                # ��������������
                break
    # �������ƹ�Ʊlist 
    return(stockselected)

def Multi_Select_Stocks(context, data):
    #�����ų�֮ǰ��ֹӯֹ��Ĺ�Ʊ�����������ɸѡ��ѡ�ɳ�
    for dstock in g.exceptions :
        # ��ǰ�۸������֮ǰֹӯ��ֹ��۸���ǵ�����
        if (dstock['stopvalue'] != 0.0) and ((data[dstock['stock']].close-dstock['stopvalue'])/dstock['stopvalue'] > 0.15):
            g.exceptions.remove(dstock)
        elif (dstock['targetvalue'] != 0.0) and ((data[dstock['stock']].close-dstock['targetvalue'])/dstock['targetvalue'] < -0.15):
            g.exceptions.remove(dstock)

    # ָ����Ʊ�б�ǿգ���ֱ�ӷ���ָ����Ʊ�б�
    if len(g.stock_appointed) > 0:
        return g.stock_appointed

    # ��ȡ��ѡ��Ʊ
    stocks = []
    # �Ƿ�ʹ��ָ����ѡ������
    if len(g.index_pool) > 0:
        #log.info("ָ����Ʊ�أ�%s" %(str(g.index_pool)))
        # ָ����
        for index in g.index_pool:
            stocks += get_index_stocks(index)
    else:
        # ��ѡ��Ʊ�أ��ձ�ʾ���й�Ʊ��ѡ
        if len(g.stock_candidates) == 0:
            #log.info("���й�Ʊ��")
            candidates = get_all_securities(['stock'])
            #�ų��¹�
            stocks = candidates[(context.current_dt.date() - candidates.start_date) > datetime.timedelta(60)].index
        else:
            #log.info("��ѡ��Ʊ��: %s" %(str(g.stock_candidates)))
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
    # �����趨��PEGָ��(��ӯ�����ӯ����������)
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
    # �۳��Ǿ��������ľ��ʲ�������/���ʲ�������ROE��Ҫ�ﵽһ������
    # ���Ǿ�������ռ���ʲ���������̫��
    if g.incReturnInROE != None :
        q = q.filter(
            indicator.inc_return > (indicator.roe*g.incReturnInROE),
            )
    # ����ֵ��������
    q = q.order_by(
        valuation.market_cap.asc()
    ).limit(
        # ��෵��20��
        20
    )
    df = get_fundamentals(q)
    stocks = df.code.values

    stock_select={}
    for s in stocks:
        #�ų�֮ǰ��ֹӯֹ��Ĺ�Ʊ
        skipit = False
        for dstock in g.exceptions :
            if dstock['stock'] == s :
                skipit = True
                break
        if skipit:
            log.info('�ų�֮ǰ��ֹӯֹ��Ĺ�Ʊ')
            log.info('%s' %(s))
            continue

        #�ų�����ֹӯֹ�������Ĺ�Ʊ
        if stock_monitor(context, data, s) != 'NormalProfit':
            continue
#        # �ų������µ����ȹ��󲢳����µ����ƵĹ�Ʊ
#        if isStockBearish(s , data, 15, 0.03, 0.02) :
#            continue

        #�ų��ּ���ͣ��δ����(�ѳ��е���ͣ�ɼ�������)����ͣ�Ĺ�Ʊ
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

    # ȷ���й�Ʊ��ѡ��
    if len(stock_select) > 0 :
        dfs = pd.DataFrame(stock_select.values(),index=stock_select.keys())
        dfs.columns=['score']
        dfs=dfs.sort(columns='score',ascending=True)
        return dfs.index[:g.stockCount].values.tolist()

    # ���ؿ��б�
    return []

def stock_monitor(context, data, stock):
    # maxd = ����250��������3�յ���
    # avgd = ����250����ƽ����3�յ���
    # bstd = (maxd+avgd)/2, ��bstd��Ϊ�����ڳֲ�3���ڣ��ܳ��ܵ�������
    # maxr = ����250��������3���Ƿ�������ӯ����������ʷֵmaxr��ʱ�����������ֹӯ
    h = attribute_history(stock, 250, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
    maxr = 0.00
    maxd = 0.00
    avgd = 0.00
    dcount = 0
    for i in range(1, len(h)-3):
        # ��������3���ǵ���
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

    # ��ǰ�۸񳬳�ֹӯֹ��ֵ���������ù�Ʊ
    dr3cur = (data[stock].close-h.close[-2])/h.close[-2]
    if dr3cur >= maxr:
        return 'TargetProfitArrived'
    if dr3cur <= bstd:
        return 'StopProfitArrived'
    return 'NormalProfit'

def isStockBearish(stock, data, interval, breakrate=0.03, lastbreakrate=0.02):
    h = attribute_history(stock, interval, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
    # ��ǰ�۸���ȵ�����߼ۻ�ǰһ�����̼��µ�3%����
    if (not isnan(h['close'].values[-1])) and (data[stock].close < (1-breakrate)*min(h['close'].values[-1], data[stock].high)) :
        breakout = True
        for i in range(1, interval) :
            # ��ǰ�۸����ǰ������ĳ������2%�����µ��գ����̼۵�����߼�2%���ϣ������ǰ�����̼�2%���ϣ�����ͼۣ��Ҹ���֮����δ��Чͻ�Ƹ�����߼�
            if (not isnan(h['close'].values[i])) and (not isnan(h['close'].values[i-1])) and (not isnan(h['low'].values[i])) and (not isnan(h['high'].values[i])) \
                and (h['close'].values[i] < (1-lastbreakrate)*min(h['close'].values[i-1], h['high'].values[i])) and (data[stock].close < h['low'].values[i]) :
                for l in range(i+1, interval) :
                    if (not isnan(h['close'].values[l])) and (not isnan(h['high'].values[i])) and (h['close'].values[l] > h['high'].values[i]) :
                        breakout = False
                        break
        if breakout :
            log.info('.............��Ʊ��������...............')
            return True
    return False

# ÿ����λʱ��(�������ز�,��ÿ�����һ��,���������,��ÿ���ӵ���һ��)����һ��
def handle_data(context, data):
    # �������Ƿ����ļ��и���
    if g.real_market_simulate and get_variables_updated(context, g.addstring):
        # ��ӡ���Բ���
        log_param()

    if (g.real_market_simulate or g.indebug) and g.autotrader_inform_enabled:
        # ������������״̬(����ز�ʱ����״̬����Ӱ��ز��ٶȣ�ÿ10���Ӽ��һ��)
        if g.real_market_simulate and (context.current_dt.minute % 10 == 0):
            # ͨ��״̬�仯�����ʼ�֪ͨ
            rspcode = autotrader_online_status(0)
            if rspcode != g.online_response_code:
                g.online_response_code = rspcode
                mail_to_report(rspcode)
        # ������߼�¼�ļ��Ƿ���δ��ɵ����߽��ף�������߽���
        if g.online_response_code == 0:
            do_record_offline()

    # ��õ�ǰʱ��
    hour = context.current_dt.hour
    minute = context.current_dt.minute

#    if isThreeBlackCrows(g.zs2, data) and isThreeBlackCrows(g.zs8, data):
#        for stock in g.stocks:
#            if context.portfolio.positions[stock].sellable_amount > 0:
#                #�в�λ�����
#    		    log.info('��ֻ��ѻ�����')
#    		    sell_all_stocks(context)
#    	#����Ϊ���ڵ�����2�죬���⵱���ٴ������Ʊ
#    	g.days = g.period-1
#        return

    # ���ֹӯֹ����������������Ʊ
    for stock in g.stocks:
        if context.portfolio.positions[stock].sellable_amount > 0:
            # ÿ���Ӽ�⣬����и��߼����¼֮���������߼ۻس�һ�����������׵�
            #try:
            #    if data[stock].close > g.maxvalue[stock] :
            #        g.maxvalue[stock] = data[stock].close
            #except KeyError:
            #    g.maxvalue[stock] = data[stock].close
            #if ((data[stock].close - g.maxvalue[stock]) / g.maxvalue[stock]) <= -g.topdropthreshold :
            #    if g.minutesinlowprice[stock] == 0:
            #        curr_data = get_current_data()
            #        log.info('��ǰ%s��%s���ɼۣ�%.02f��������߼ۣ�%.02f�����½�����ֵ' %(curr_data[stock].name, stock, data[stock].close, g.maxvalue[stock]))
            #    g.minutesinlowprice[stock] += 1
            #else:
            #    # ������״̬�����
            #    if g.minutesinlowprice[stock] < g.minutesthreshold:
            #        g.minutesinlowprice[stock] = 0
            # �ɼ۳���������߼����½�����ֵ��ֹ��
            #if g.minutesinlowprice[stock] >= g.minutesthreshold:
            #    position = context.portfolio.positions[stock]
            #    if close_position(context, position):
            #        g.todobuy = True
            #        log.info('����������߼����½�����ֵ��ֹ��: ')
            #        g.exceptions.append({'stock': stock, 'stopvalue': data[stock].close, 'targetvalue': 0.0})
            #        curr_data = get_current_data()
            #        log.info('Sell: %s(%s), %02f, %02f' %(curr_data[stock].name, stock,data[stock].close,g.maxvalue[stock]))

            # ��ȡ���1�����̼�
            h = attribute_history(stock, 1, unit='1d', fields=('close'), skip_paused=True)
            # �Ե����µ����ȹ���Ĺ�Ʊ���м���ͳ��
            if data[stock].close  < 0.955*h['close'].values[-1] :
                if g.stockscrashed.count(stock) == 0:
                    g.stockscrashed.append(stock)
            # ��ǰ�۸񳬳�ֹӯֹ��ֵ���������ù�Ʊ
            dr3cur = (data[stock].close-context.portfolio.positions[stock].avg_cost)/context.portfolio.positions[stock].avg_cost
            #dr3cur = (data[stock].close-h['close'].values[-2])/h['close'].values[-2]
            if dr3cur <= g.maxrbstd[stock]['bstd']:
                position = context.portfolio.positions[stock]
                if close_position(context, position):
                    g.todobuy = True
                    log.info('ֹ��: ')
                    g.exceptions.append({'stock': stock, 'stopvalue': data[stock].close, 'targetvalue': 0.0})
                    curr_data = get_current_data()
                    log.info('Sell: %s(%s)' %(curr_data[stock].name, stock))
                # ����ù�Ʊδ������ֹ���б��У�����ӽ�ȥ
                if g.stopstocks.count(stock) == 0:
                    g.stopstocks.append(stock)
            elif dr3cur >= g.maxrbstd[stock]['maxr']*1.100:
                position = context.portfolio.positions[stock]
                if close_position(context, position):
                    g.todobuy = True
                    log.info('ֹӯ: ')
                    g.exceptions.append({'stock': stock, 'stopvalue': 0.0, 'targetvalue': data[stock].close})
                    curr_data = get_current_data()
                    log.info('Sell: %s(%s)' %(curr_data[stock].name, stock))

    stopfactor = 1
    if g.stockCount > 2:
        stopfactor = 2
    # �����µ����ȹ���Ĺ�Ʊ����һ�����������߳���һ������ֹ�Ʊֹ����ֹ���
    if (len(g.stocks) > 0) and (len(g.stockscrashed)*4.0/3 >= len(g.stocks) or len(g.stopstocks)*stopfactor >= len(g.stocks)) :
        g.todobuy = False
        if context.portfolio.positions_value > 0:
            #�в�λ�����
            log.info('��ֻ��Ʊ�ﵽֹ���ߣ����')
            sell_all_stocks(context)
            # ����1�죬����Ϊ���ڵ�����2�죬���⵱���ٴ������Ʊ
            g.days = g.period-1

    pos_adjust_time = (hour == g.adjust_position_hour and minute== g.adjust_position_minute)
    # �в�λ������ʱ���ʵ��ʱ������ָ��
    if (context.portfolio.positions_value > 0) or pos_adjust_time or g.real_market_simulate:
        # ��ȡǰһ��ָ�����̼�
        hs1 = getStockPrice(g.zs1, g.lag)
        hs2 = getStockPrice(g.zs2, g.lag)
        hs8 = getStockPrice(g.zs8, g.lag)
        if isnan(data[g.zs1].close):
            cp1 = get_close_price(g.zs1, 1, '1m')
        else:
            cp1 = data[g.zs1].close
        if isnan(data[g.zs2].close):
            cp2 = get_close_price(g.zs2, 1, '1m')
        else:
            cp2 = data[g.zs2].close
        if isnan(data[g.zs8].close):
            cp8 = get_close_price(g.zs8, 1, '1m')
        else:
            cp8 = data[g.zs8].close

        #cmp1result = True
        cmp2result = True
        cmp8result = True

        if (not isnan(hs1)) and (not isnan(cp1)):
            g.ret1 = (cp1 - hs1) / hs1
        #    if g.ret1>-0.004 :
        #        cmp1result = False
        else:
            g.ret1 = 0
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
        record(index1=g.ret1, index2=g.ret2, index8=g.ret8)
        #record(index2=g.ret2, index8=g.ret8)

    # ������ָ���Ƿ�ﵽ�������ޣ���ﵽ����ֹ���
    if context.portfolio.positions_value > 0 :
        if (cmp2result and cmp8result) or (isStockBearish(g.zs2, data, 5, 0.04, 0.03) or isStockBearish(g.zs8, data, 5, 0.04, 0.03)) :
            #�в�λ�����
            log.info('����δ�������������')
            sell_all_stocks(context)
            # ����1�죬����Ϊ���ڵ�����2�죬���⵱���ٴ������Ʊ
            g.days = g.period-1

    # �Ƽ���Ʊ
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
                log.info('��ǰ�Ƽ���Ʊ��%s' %(output))

    # ÿ������14:50����
    if pos_adjust_time:
        #log.error("%s" % (str(g.ret_last5d)))
        #log.error("%f, %f, %f" %(g.ret1, g.ret2, g.ret8))
        #if context.current_dt >= datetime.datetime(2006, 10, 10) and len(g.ret_last5d) >= 5:
            #g.gradient1 = g.ret1 - g.ret_last5d[0][0]
            #g.gradient2 = g.ret2 - g.ret_last5d[0][1]
            #g.gradient8 = g.ret8 - g.ret_last5d[0][2]

            #if g.gradient1 <= -0.01 and g.gradient2 <= -0.01 and g.gradient8 <= -0.01:
            #    log.error("����ָ���������ƣ�����")

        #��֣�����101%ʱ��֣��ز�Ч������úá�
        #������ָ��ֻ����5������б�����ϵ�����£�����101%�Ƿ�ʱ��������
        #if (g.ret1>0.01 and g.gradient1>0.01) or g.ret2>0.01 or g.ret8>0.01 :
        if g.ret2>0.01 or g.ret8>0.01 :
            g.days += 1
            if g.todobuy or (g.days % g.period == 1):            
                log.info('���У�ÿ%d����е���' %(g.period))
                buy_stocks(context, data)
                update_maxr_bstd(context)
        else :
            log.info('���')
            sell_all_stocks(context)

# ���֣�����ָ����ֵ��֤ȯ
# �����ɹ����ɽ�������ȫ���ɽ��򲿷ֳɽ�����ʱ�ɽ�������0��������True
# ����ʧ�ܻ��߱����ɹ�����ȡ������ʱ�ɽ�������0��������False
def open_position(context, security, value):
    order = order_target_value_(context, security, value)
    if order != None and order.filled > 0:
        return True
    return False

# ƽ�֣�����ָ���ֲ�
# ƽ�ֳɹ���ȫ���ɽ�������True
# ����ʧ�ܻ��߱����ɹ�����ȡ������ʱ�ɽ�������0�������߱�����ȫ���ɽ�������False
def close_position(context, position):
    security = position.security
    order = order_target_value_(context, security, 0) # ���ܻ���ͣ��ʧ��
    if order != None:
        if order.filled > 0:
            # ֻҪ�гɽ�������ȫ���ɽ����ǲ��ֳɽ�����ͳ��ӯ��
            g.trade_stat.watch(security, order.filled, position.avg_cost, position.price)

        if order.status == OrderStatus.held and order.filled == order.amount:
            return True

    return False

# �Զ����µ�
# ����Joinquant�ĵ�����ǰ����������������ִ�У�������������order_target_value�����ؼ���ʾ�������
# �����ɹ����ر�����������һ����ɽ��������򷵻�None
def order_target_value_(context, security, value):
    if value == 0:
        log.debug("Selling out %s" % (security))
    else:
        log.debug("Order %s to value %f" % (security, value))
        
    # �����Ʊͣ�ƣ�����������ʧ�ܣ�order_target_value ����None
    # �����Ʊ�ǵ�ͣ������������ɹ���order_target_value ����Order�����Ǳ�����ȡ��
    # ���ɲ����ı������ۿ�״̬���ѳ�����ʱ�ɽ���>0����ͨ���ɽ����ж��Ƿ��гɽ�
    order = order_target_value(security, value)
    # ģ��ʽ������£������ǿ�
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
        #ȷ����Ʊ������0���Ҹù�Ʊ������ѡ�еĹ�Ʊ����
        if (context.portfolio.positions[stock].total_amount > 0) and (stock not in g.stocks):
            position = context.portfolio.positions[stock]
            if not close_position(context, position) :
                #�۳���Ʊʧ�ܣ���ͣ�ƹ�Ʊ�����������Ҫɾ�����漸������ı�ѡ��Ʊ��ʹ��Ʊ������4��
                g.stocks.pop()
                g.stocks.insert(0, stock)
            curr_data = get_current_data()
            log.info('Rank Outof 10, Sell: %s(%s)' %(curr_data[stock].name, stock))

    #��ʼ����ѡ�еĹ�Ʊ����߼�
    #for stock in g.stocks :
    #    if stock not in context.portfolio.positions.keys():
    #        g.maxvalue[stock] = data[stock].close
    #        #��ʼ���ɼ۵�����߼����½�����ֵ��ʱ
    #        g.minutesinlowprice[stock] = 0

    valid_count = 0
    for stock in context.portfolio.positions.keys():
        if context.portfolio.positions[stock].total_amount > 0:
            valid_count = valid_count + 1
    # place equally weighted orders
    #���й�Ʊ����>=4������ֱ�ӷ���
    if valid_count < len(g.stocks):
        value = (context.portfolio.total_value - g.totalValueDifference) / len(g.stocks)
        for stock in g.stocks:
            open_position(context, stock, value)
            curr_data = get_current_data()
            log.info('buy: %s(%s)' %(curr_data[stock].name, stock))

def update_maxr_bstd(context):
    g.maxrbstd = {}
    for stock in g.stocks:
        # maxd = ����250��������3�յ���
        # avgd = ����250����ƽ����3�յ���
        # bstd = (maxd+avgd)/2, ��bstd��Ϊ�����ڳֲ�3���ڣ��ܳ��ܵ�������
        # maxr = ����250��������3���Ƿ�������ӯ����������ʷֵmaxr��ʱ�����������ֹӯ
        h = attribute_history(stock, 250, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        maxr = 0.00
        maxd = 0.00
        avgd = 0.00
        dcount = 0
        for i in range(1, len(h)-3):
            # ��������3���ǵ���
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
#ÿ�쿪��ǰ
#================================================================================
def before_trading_start(context):
    # �������Ƿ����ļ��и���
    if get_variables_updated(context, g.addstring):
        # ��ӡ���Բ���
        log_param()

    # ����������Ϊ0
    set_slippage(FixedSlippage(0)) 
    # ���ݲ�ͬ��ʱ�������������
    dt=context.current_dt
    # ���������ѣ�ÿ�ʽ���ʱ����������, ����ʱȯ��Ӷ������ʱȯ��Ӷ���ǧ��֮һӡ��˰, ÿ�ʽ�����Ϳ�5��Ǯ
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.00027, sell_cost=0.00127, min_cost=5)) 
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))

    # ���㲢��¼���ո���250��������3���Ƿ����ܳ��ܵ�������
    update_maxr_bstd(context)

    #��ʼ������֮�����߼ۣ��޳����ڳֲַ�Χ�ڵĹ�Ʊ��߼�Ԫ��
    #maxvalue = {}
    #minutesinlowprice = {}
    #for stock in context.portfolio.positions.keys():
    #    if stock in g.stocks:
    #        try:
    #            maxvalue[stock] = g.maxvalue[stock]
    #        except KeyError:
    #            maxvalue[stock] = 0.01
    #        #��¼��һ�չɼ۵�����߼����½�����ֵ��ʱֵ
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
    #        #��ʼ���ɼ۵�����߼����½�����ֵ��ʱ
    #        minutesinlowprice[stock] = 0
    #g.minutesinlowprice = minutesinlowprice
    #g.maxvalue = maxvalue

#================================================================================
#ÿ�����̺�
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

    # ģ��ʵ�������ִ��
    if (g.real_market_simulate or g.indebug) and g.autotrader_inform_enabled:
        # ɾ������δ��ɵ����߽��׼�¼
        rm_all_records_offline()

    # �õ���ǰδ��ɶ���
    orders = get_open_orders()
    for _order in orders.values():
        log.info("canceled uncompleted order: %s" %(_order.order_id))
    pass

# ����ͳ����
class trade_stat():
    def __init__(self):
        self.trade_total_count = 0
        self.trade_success_count = 0
        self.statis = {'win': [], 'loss': []}
        
    def reset(self):
        self.trade_total_count = 0
        self.trade_success_count = 0
        self.statis = {'win': [], 'loss': []}
    
    # ��¼���״�������ͳ��ʤ��
    # �����ɹ������������������ӯ��ͳ��
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
        log.info("���̺�ֲָſ�:%s" % str(list(context.portfolio.positions)))
        log.info("��λ�ſ�:%.2f" % position)
        self.print_win_rate(context.current_dt.strftime("%Y-%m-%d"), context.current_dt.strftime("%Y-%m-%d"), context)

    # ��ӡʤ��
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
            print '------------��Ч����------------'
            print '���״���: {0}, ӯ������: {1}, ʤ��: {2}'.format(self.trade_total_count, self.trade_success_count, str(win_rate * 100) + str('%'))
            print '����ӯ�����: {0}, ӯ������: {1}%'.format(most_win['stock'], most_win['value'])
            print '���ο������: {0}, �������: {1}%'.format(most_loss['stock'], most_loss['value'])
            print '���ʲ�: {0}, ����: {1}, ӯ��: {2}, ӯ�����ʣ�{3}%'.format(starting_cash + total_profit, starting_cash, total_profit, total_profit / starting_cash * 100)
            print '--------------------------------'
            print "-"

    # ͳ�Ƶ���ӯ����ߵĹ�Ʊ
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

    # ͳ�Ƶ��ο�����ߵĹ�Ʊ
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

    # ͳ����ӯ�����    
    def statis_total_profit(self, context):
        return (context.portfolio.total_value - g.totalValueDifference) - g.capitalValue

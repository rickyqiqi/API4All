'''
二八小市值择时买卖

配置指定频率的调仓日，在调仓日每日指定时间，计算沪深300指数和中证500指数当前的20日涨
幅，如果2个指数的20日涨幅有一个为正，则进行选股调仓，之后如此循环往复。

止损策略：

    大盘止损：(可选)
        1. 每分钟取大盘前160日的最低价和最高价，如果最高大于最低的两倍则清仓，停止交易。
        2. 每分钟判断大盘是否呈现三只黑鸦止损，如果是则当天清仓并停止交易，第二天停止交
           易一天。

    个股止损：(可选)
        每分钟判断个股是否从持仓后的最高价回撤幅度，如果超过个股回撤阈值，则平掉该股持仓

    二八止损：(必需)
        每日指定时间，计算沪深300指数和中证500指数当前的20日涨幅，如果2个指数涨幅都为负，
        则清仓，重置调仓计数，待下次调仓条件满足再操作

版本：v2.0.7
日期：2016.11.15
作者：Morningstar
'''

import tradestat
from config import *
from autotraderintf import *
from mailintf import *

def before_trading_start(context):
    # 检查变量是否在文件中更新
    if get_variables_updated(g.addstring):
        # 打印策略参数
        log_param()

    log.info("---------------------------------------------")
    #log.info("==> before trading start @ %s", str(context.current_dt))

    # 盘前显示当日有效黑名单
    if g.filter_blacklist:
        log.info("当日股票有效黑名单：%s" %str(get_blacklist(context)))

    # 是否根据账户总金额下跌率止损
    if g.is_stop_loss_by_portfolio_loss_rate:
        # 初始化当日总资金金额
        init_portfolio_value_high()

    # 盘前就判断三黑鸦状态，因为判断的数据为前4日
    g.is_last_day_3_black_crows = is_3_black_crows(g.index_4_stop_loss_by_3_black_crows)
    if g.is_last_day_3_black_crows:
        log.info("==> 前4日已经构成三黑鸦形态")
    pass

def after_trading_end(context):
    #log.info("==> after trading end @ %s", str(context.current_dt))
    g.trade_stat.report(context)

    # 模拟实盘情况下执行
    if (g.real_market_simulate or g.indebug) and g.is_autotrader_inform_enabled:
        # 删除当天未完成的离线交易记录
        rm_all_records_offline()

    reset_day_param()
    
    # 得到当前未完成订单
    orders = get_open_orders()
    for _order in orders.values():
        log.info("canceled uncompleted order: %s" %(_order.order_id))
    pass

def initialize(context):
    log.info("==> initialize @ %s", str(context.current_dt))

    # install opener
    urllib2.install_opener(urllib2.build_opener(HTTPSHandlerV3()))

    # 设置手续费率
    set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))
    # 设置基准指数：沪深300指数 '000300.XSHG'
    set_benchmark('000300.XSHG')
    # 设定滑点为百分比
    # 没有调用set_slippage函数, 系统默认的滑点是PriceRelatedSlippage(0.00246)
    #set_slippage(PriceRelatedSlippage(0.004))

    # 参数版本号
    g.version = 0.0

    # additional string in variable configuration file name
    g.addstring = "7stocks"
    
    # 是否在调试模式下
    g.indebug = False
    
    # 在线状态响应码
    g.online_response_code = 0

    # 当前是否是模拟实盘，回测盘的context.current_dt日期和time.time()日期不同
    g.real_market_simulate = False
    runningdatetime = datetime.datetime.fromtimestamp(time.time())
    if context.current_dt.date() == runningdatetime.date():
        # 使用真实价格回测(模拟盘推荐如此，回测请注释)
        set_option('use_real_price', True)
        g.real_market_simulate = True

    # 加载统计模块
    g.trade_stat = tradestat.trade_stat()

    # 配置策略参数
    # 此配置主要为之前的小市值策略，保证之前的收益回撤
    # 如果想要更改，最好新建个函数，调整参数测试其他策略
    # 10日调仓
    # 关闭大盘三乌鸦及高低价止损
    # 关闭个股止盈止损
    # 关闭选股评分
    set_param()
    
    # 调仓日计数器，单位：日
    g.day_count = 0

    # 缓存股票持仓后的最高价
    g.last_high = {}
    
    # 是否根据账户总金额下跌率止损
    if g.is_stop_loss_by_portfolio_loss_rate:
        # 缓存近n天最高市值
        g.last_ndays_portfolio_value_high = [0 for i in range(g.last_portfolio_value_high_days)]
        g.cur_portfolio_drop_minute_count = 0

    # 如下参数不能更改
    if g.is_market_stop_loss_by_price:
        # 记录当日是否满足大盘价格止损条件，每日盘后重置
        g.is_day_stop_loss_by_price = False

    # 缓存三黑鸦判断状态
    g.is_last_day_3_black_crows = False
    if g.is_market_stop_loss_by_3_black_crows:
        g.cur_drop_minute_count = 0

    if g.is_rank_stock:
        if g.rank_stock_count > g.pick_stock_count:
            g.rank_stock_count = g.pick_stock_count

    if g.is_stock_stop_loss or g.is_stock_stop_profit:
        # 缓存当日个股250天内最大的3日涨幅，避免当日反复获取，每日盘后清空
        g.pct_change = {}

    if g.is_market_stop_loss_by_28_index:
        g.minute_count_28index_drop = 0

    # 调仓完成标志
    g.position_change_finished = False
    # 当日涨幅超出过设定调仓的二八指数20日增幅标志
    g.index_growth_rate_over_uplimit = False

    # 打印策略参数
    log_param()

def set_param():
    # 调仓频率，单位：日
    g.period = 3
    # 配置调仓时间（24小时分钟制）
    g.adjust_position_hour = 14
    g.adjust_position_minute = 50

    # 配置选股参数

    # 备选股票数目
    g.pick_stock_count = 100
    
    # 配置选股参数
    # 是否根据PE选股
    g.pick_by_pe = False
    # 如果根据PE选股，则配置最大和最小PE值
    if g.pick_by_pe:
        g.max_pe = 200
        g.min_pe = 0

    # 是否根据EPS选股
    g.pick_by_eps = True
    # 配置选股最小EPS值
    if g.pick_by_eps:
        g.min_eps = 0
    
    # 配置是否过滤创业板股票
    g.filter_gem = True
    # 配置是否过滤黑名单股票，回测建议关闭，模拟运行时开启
    g.filter_blacklist = True
    if g.filter_blacklist:
        g.blacklist = []

    # 是否对股票评分
    g.is_rank_stock = True
    if g.is_rank_stock:
        # 参与评分的股票数目
        g.rank_stock_count = 20

        # 股票多头趋势加分项参数
        g.is_rank_stock_score_plus_allowed = False
        if g.is_rank_stock_score_plus_allowed:
            # 加分因子（倍率）
            g.rank_stock_score_plus_factor = 0.08
            # 测试多头趋势的均线长度
            g.ma_lengths = [5,10,20,60,120]
            # 多头趋势天数
            g.in_trend_days = 7

    # 买入股票数目
    g.buy_stock_count = 2
    
    # 配置二八指数
    #g.index2 = '000300.XSHG'  # 沪深300指数，表示二，大盘股
    #g.index8 = '000905.XSHG'  # 中证500指数，表示八，小盘股
    g.index2 = '000016.XSHG'  # 上证50指数
    g.index8 = '399333.XSHE'  # 中小板R指数
    #g.index8 = '399006.XSHE'  # 创业板指数
    
    # 判定调仓的二八指数20日增幅
    #g.index_growth_rate = 0.00
    g.index_growth_rate = 0.01

    # 配置是否检查全天买入机会
    # 全天中有超过二八指数20日增幅的情况，但到达调仓时间点时又回撤回去了
    g.check_buy_in_chance_all_day = True
    if g.check_buy_in_chance_all_day:
        # 调仓时间点二八指数20日增幅允许为标准二八指数20日增幅的百分比
        g.ajust_rate_4_index_growth_rate = 0.85

    # 配置是否根据大盘历史价格止损
    # 大盘指数前160日内最高价超过最低价2倍，则清仓止损
    # 注：关闭此止损，收益增加，但回撤会增加
    g.is_market_stop_loss_by_price = True
    if g.is_market_stop_loss_by_price:
        # 配置价格止损判定指数，默认为上证指数，可修改为其他指数
        g.index_4_stop_loss_by_price = '000001.XSHG'
        # 调整倍数
        g.ajust_rate_4_stop_loss_by_price = 1.10

    # 配置三黑鸦判定指数，默认为上证指数，可修改为其他指数
    g.index_4_stop_loss_by_3_black_crows = '000001.XSHG'

    # 配置是否开启大盘三黑鸦止损
    # 个人认为针对大盘判断三黑鸦效果并不好，首先有效三只乌鸦难以判断，准确率实际来看也不好，
    # 其次，分析历史行情看一般大盘出现三只乌鸦的时候，已经严重滞后了，使用其他止损方式可能会更好
    g.is_market_stop_loss_by_3_black_crows = False
    if g.is_market_stop_loss_by_3_black_crows:
        g.dst_drop_minute_count = 60

    # 是否根据28指数值实时进行止损
    g.is_market_stop_loss_by_28_index = False
    if g.is_market_stop_loss_by_28_index:
        # 配置当日28指数连续为跌的分钟计数达到指定值则止损
        g.dst_minute_count_28index_drop = 120

    # 配置是否个股止损
    g.is_stock_stop_loss = True
    if g.is_stock_stop_loss:
        g.ajust_rate_4_stock_stop_loss = 1.00
    # 配置是否个股止盈
    g.is_stock_stop_profit = True
    if g.is_stock_stop_profit:
        g.ajust_rate_4_stock_stop_profit = 1.10

    # 配置是否根据账户总金额下跌率止损
    g.is_stop_loss_by_portfolio_loss_rate = True
    if g.is_stop_loss_by_portfolio_loss_rate:
        # 统计账户总金额的连续交易日数量
        g.last_portfolio_value_high_days = 5
        # 触发账户止损的总金额下跌率
        g.stop_portfolio_loss_rate = 0.82
        g.dst_portfolio_drop_minute_count = 60

    # 配置是否开启邮件通知
    g.is_mail_inform_enabled = False
    # 配置是否开启autotrader通知
    g.is_autotrader_inform_enabled = True

    # 备选股票池，空表示所有股票备选
    g.stock_candidates = []
    # 是否使用指数池选股配置
    g.index_stock_2_select = False
    if g.index_stock_2_select:
        # 指数池，默认沪深300指数
        g.index_pool = ["000300.XSHG", "000905.XSHG"]

    # 出现二八分化时是否采纳大盘指数股票池
    g.large_market_share_index_pool_used = True
    if g.large_market_share_index_pool_used:
        # 大盘指数股票池
        g.large_market_share_index = '000016.XSHG'
        # 二八分化判断参数
        g.large_market_share_trend_judge_param = 0.065

def log_param():
    log.info("---------------------------------------------")
    log.info("是否是调试模式: %s" %(g.indebug))
    log.info("参数版本号: %.02f" %(g.version))
    log.info("调仓日频率: %d日" %(g.period))
    log.info("调仓时间: %s:%s" %(g.adjust_position_hour, g.adjust_position_minute))

    log.info("备选股票数目: %d" %(g.pick_stock_count))

    log.info("是否根据PE选股: %s" %(g.pick_by_pe))
    if g.pick_by_pe:
        log.info("选股最大PE: %s" %(g.max_pe))
        log.info("选股最小PE: %s" %(g.min_pe))

    log.info("是否根据EPS选股: %s" %(g.pick_by_eps))
    if g.pick_by_eps:
        log.info("选股最小EPS: %s" %(g.min_eps))
    
    log.info("是否过滤创业板股票: %s" %(g.filter_gem))
    log.info("是否过滤黑名单股票: %s" %(g.filter_blacklist))

    log.info("是否对股票评分选股: %s" %(g.is_rank_stock))
    if g.is_rank_stock:
        log.info("评分备选股票数目: %d" %(g.rank_stock_count))

    log.info("买入股票数目: %d" %(g.buy_stock_count))

    log.info("二八指数之二: %s - %s" %(g.index2, get_security_info(g.index2).display_name))
    log.info("二八指数之八: %s - %s" %(g.index8, get_security_info(g.index8).display_name))
    log.info("判定调仓的二八指数20日增幅: %.1f%%" %(g.index_growth_rate*100))

    log.info("是否开启大盘历史高低价格止损: %s" %(g.is_market_stop_loss_by_price))
    if g.is_market_stop_loss_by_price:
        log.info("大盘价格止损判定指数: %s - %s" %(g.index_4_stop_loss_by_price, get_security_info(g.index_4_stop_loss_by_price).display_name))
        log.info("大盘价格止损调整倍率: %s" %(g.ajust_rate_4_stop_loss_by_price))

    log.info("大盘三黑鸦止损判定指数: %s - %s" %(g.index_4_stop_loss_by_3_black_crows, get_security_info(g.index_4_stop_loss_by_3_black_crows).display_name))
    log.info("是否开启大盘三黑鸦止损: %s" %(g.is_market_stop_loss_by_3_black_crows))
    if g.is_market_stop_loss_by_3_black_crows:
        log.info("三黑鸦止损开启需要当日大盘为跌的分钟计数达到: %d" %(g.dst_drop_minute_count))

    log.info("是否根据28指数值实时进行止损: %s" %(g.is_market_stop_loss_by_28_index))
    if g.is_market_stop_loss_by_28_index:
        log.info("根据28指数止损需要当日28指数连续为跌的分钟计数达到: %d" %(g.dst_minute_count_28index_drop))        

    log.info("是否开启个股止损: %s" %(g.is_stock_stop_loss))
    if g.is_stock_stop_loss:
        log.info("个股止损调整倍率: %s" %(g.ajust_rate_4_stock_stop_loss))
    log.info("是否开启个股止盈: %s" %(g.is_stock_stop_profit))
    if g.is_stock_stop_profit:
        log.info("个股止盈调整倍率: %s" %(g.ajust_rate_4_stock_stop_profit))

    log.info("是否开启根据账户总金额下跌率止损: %s" %(g.is_stop_loss_by_portfolio_loss_rate))
    if g.is_stop_loss_by_portfolio_loss_rate:
        log.info("账户总金额下跌至连续%02d日最高总金额的下跌止损率: %2.2f%%, 持续分钟数: %d" %(g.last_portfolio_value_high_days, (1-g.stop_portfolio_loss_rate)*100, g.dst_portfolio_drop_minute_count))

    log.info("是否开启邮件通知: %s" %(g.is_mail_inform_enabled))
    log.info("是否开启autotrader通知: %s" %(g.is_autotrader_inform_enabled))

    log.info("备选股票池: %s" %(str(g.stock_candidates)))
    log.info("是否使用指数池选股配置: %s" %(g.index_stock_2_select))
    if g.index_stock_2_select:
        log.info("指数池: %s" %(str(g.index_pool)))

    log.info("出现二八分化时，是否采纳大盘指数股票池: %s" %(g.large_market_share_index_pool_used))
    if g.large_market_share_index_pool_used:
        log.info("大盘指数股票池: %s" %(g.large_market_share_index))
        log.info("二八分化判断参数: %.03f" %(g.large_market_share_trend_judge_param))

# 重置当日参数，仅针对需要当日需要重置的参数
def reset_day_param():
    # 是否根据账户总金额下跌率止损
    if g.is_stop_loss_by_portfolio_loss_rate:
        g.cur_portfolio_drop_minute_count = 0

    if g.is_market_stop_loss_by_price:
        # 重置当日大盘价格止损状态
        g.is_day_stop_loss_by_price = False

    # 重置三黑鸦状态
    g.is_last_day_3_black_crows = False
    if g.is_market_stop_loss_by_3_black_crows:
        g.cur_drop_minute_count = 0

    if g.is_market_stop_loss_by_28_index:
        g.minute_count_28index_drop = 0

    if g.is_stock_stop_loss or g.is_stock_stop_profit:
        # 清空当日个股250天内最大的3日涨幅的缓存
        g.pct_change.clear()

    # 复位调仓完成标志
    g.position_change_finished = False
    # 复位当日涨幅超出过设定调仓的二八指数20日增幅标志
    g.index_growth_rate_over_uplimit = False

# 初始化近n日总资金金额
def init_portfolio_value_high():
    for i in range(g.last_portfolio_value_high_days-1):
        g.last_ndays_portfolio_value_high[i] = g.last_ndays_portfolio_value_high[i+1]
    g.last_ndays_portfolio_value_high[g.last_portfolio_value_high_days-1] = 0

# 设置近n日中当日总资金金额最高值
def set_portfolio_value_high(current_portfolio_value):
    if g.last_ndays_portfolio_value_high[g.last_portfolio_value_high_days-1] < current_portfolio_value:
        g.last_ndays_portfolio_value_high[g.last_portfolio_value_high_days-1] = current_portfolio_value

# 判断是否执行根据资金总额下跌率止损
def stop_loss_by_portfolio_loss_rate(context):
    max_portfolio_value_high = max(g.last_ndays_portfolio_value_high)
    if context.portfolio.total_value < max_portfolio_value_high * g.stop_portfolio_loss_rate:
        g.cur_portfolio_drop_minute_count += 1

    if g.cur_portfolio_drop_minute_count >= g.dst_portfolio_drop_minute_count:
        if g.cur_portfolio_drop_minute_count == g.dst_portfolio_drop_minute_count:
            log.info("==> 当前资金总额下跌已低于数日内最高资金总额的止损倍数超过%d分钟, 当前资金总额: %f, 最高资金总额: %f" %(g.dst_portfolio_drop_minute_count, context.portfolio.total_value, max_portfolio_value_high))

        clear_position(context)
        g.day_count = 0
        return True
    return False

# 按分钟回测
def handle_data(context, data):
    if (g.real_market_simulate or g.indebug) and g.is_autotrader_inform_enabled:
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

    # 是否根据账户总金额下跌率止损
    if g.is_stop_loss_by_portfolio_loss_rate:
        # 设置近n日中当日总资金金额最高值
        set_portfolio_value_high(context.portfolio.total_value)
        # 当前总资金金额低于近n日中最高值的止损倍数，止损
        if stop_loss_by_portfolio_loss_rate(context):
            return

    if g.is_market_stop_loss_by_price:
        if market_stop_loss_by_price(context, g.index_4_stop_loss_by_price):
            return

    if g.is_market_stop_loss_by_28_index:
        if market_stop_loss_by_28_index(context, g.dst_minute_count_28index_drop):
            return

    if g.is_market_stop_loss_by_3_black_crows:
        if market_stop_loss_by_3_black_crows(context, g.index_4_stop_loss_by_3_black_crows, g.dst_drop_minute_count):
            return

    if g.is_stock_stop_loss:
        stock_stop_loss(context, data)

    if g.is_stock_stop_profit:
        stock_stop_profit(context, data)

    do_handle_data(context, data)

def do_handle_data(context, data):
    # 获得当前时间
    hour = context.current_dt.hour
    minute = context.current_dt.minute

    # 回看指数前20天的涨幅
    gr_index2 = 0
    if context.current_dt.date() > datetime.datetime(2005, 1, 31).date():
        gr_index2 = get_growth_rate(g.index2)
    gr_index8 = 0
    if context.current_dt.date() > datetime.datetime(2007, 1, 26).date():
        gr_index8 = get_growth_rate(g.index8)
    
    record(index2=gr_index2, index8=gr_index8)

    # 是否设置了检查全天买入机会的选项
    if g.check_buy_in_chance_all_day:
        # 超过标准二八指数20日增幅则记录下来
        if gr_index2 > g.index_growth_rate or gr_index8 > g.index_growth_rate:
            g.index_growth_rate_over_uplimit = True

    # 是否当日调仓已经完成
    if not g.position_change_finished:
        # 是否是调仓时点及其之后的时点
        # 每天指定时间检查是否调仓并处理
        if hour == g.adjust_position_hour and minute >= g.adjust_position_minute:
            if minute == g.adjust_position_minute:
                log.info("调仓日计数 [%d]" %(g.day_count))
                log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index2).display_name, gr_index2*100))
                log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index8).display_name, gr_index8*100))

            buy_in_condition = (gr_index2 > g.index_growth_rate) or (gr_index8 > g.index_growth_rate)

            # 是否设置了检查全天买入机会的选项
            if g.check_buy_in_chance_all_day:
                # 仓位是否为空仓
                # 是否全天中有超过标准二八指数20日增幅
                # 当前调仓时间点指数涨幅超过了标准二八指数20日增幅的一定调整比例
                if context.portfolio.positions_value <= 0 and g.index_growth_rate_over_uplimit \
                    and (gr_index2 > g.index_growth_rate*g.ajust_rate_4_index_growth_rate \
                        or gr_index8 > g.index_growth_rate*g.ajust_rate_4_index_growth_rate):
                    buy_in_condition = True

            if buy_in_condition:
                if g.day_count % g.period == 0:
                    log.info("==> 满足条件进行调仓")
                    buy_stocks = pick_stocks(context, data)
                    log.info("选股后可买股票: %s" %(buy_stocks))
                    adjust_position(context, buy_stocks)
                g.day_count += 1
                g.position_change_finished = True
            elif context.portfolio.positions_value > 0:
                clear_position(context)
                g.day_count = 0
                g.position_change_finished = True

def market_stop_loss_by_price(context, index):
    # 大盘指数前160日内最高价超过最低价2倍，则清仓止损
    # 基于历史数据判定，因此若状态满足，则当天都不会变化
    # 增加此止损，回撤降低，收益降低

    if not g.is_day_stop_loss_by_price:
        h = attribute_history(index, 160, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        low_price = h.low.min()
        high_price = h.high.max()
        if high_price > 2 * g.ajust_rate_4_stock_stop_profit * low_price \
            and h['close'][-1] < h['close'][-4] \
            and h['close'][-1] > h['close'][-100]:
            # 当日第一次输出日志
            log.info("==> 大盘止损，%s指数前160日内最高价超过最低价2倍, 最高价: %f, 最低价: %f" %(get_security_info(index).display_name, high_price, low_price))
            g.is_day_stop_loss_by_price = True

    if g.is_day_stop_loss_by_price:
        clear_position(context)
        g.day_count = 0

    return g.is_day_stop_loss_by_price

def market_stop_loss_by_3_black_crows(context, index, n):
    # 前日三黑鸦，累计当日大盘指数涨幅<0的分钟计数
    # 如果分钟计数超过值n，则开始进行三黑鸦止损
    # 避免无效三黑鸦乱止损
    if g.is_last_day_3_black_crows:
        if get_growth_rate(index, 1) < 0:
            g.cur_drop_minute_count += 1

        if g.cur_drop_minute_count >= n:
            if g.cur_drop_minute_count == n:
                log.info("==> 当日%s增幅 < 0 已超过%d分钟，执行三黑鸦止损" %(get_security_info(index).display_name, n))

            clear_position(context)
            g.day_count = 0
            return True

    return False

def is_3_black_crows(stock):
    # talib.CDL3BLACKCROWS

    # 三只乌鸦说明来自百度百科
    # 1. 连续出现三根阴线，每天的收盘价均低于上一日的收盘
    # 2. 三根阴线前一天的市场趋势应该为上涨
    # 3. 三根阴线必须为长的黑色实体，且长度应该大致相等
    # 4. 收盘价接近每日的最低价位
    # 5. 每日的开盘价都在上根K线的实体部分之内；
    # 6. 第一根阴线的实体部分，最好低于上日的最高价位
    #
    # 算法
    # 有效三只乌鸦描述众说纷纭，这里放宽条件，只考虑1和2
    # 根据前4日数据判断
    # 3根阴线跌幅超过4.5%

    h = attribute_history(stock, 4, '1d', ('close','open'), skip_paused=True, df=False)
    h_close = list(h['close'])
    h_open = list(h['open'])

    if len(h_close) < 4 or len(h_open) < 4:
        return False
    
    # 一阳三阴
    if h_close[-4] > h_open[-4] \
        and (h_close[-1] < h_open[-1] and h_close[-2]< h_open[-2] and h_close[-3] < h_open[-3]):
        #and (h_close[-1] < h_close[-2] and h_close[-2] < h_close[-3]) \
        #and h_close[-1] / h_close[-4] - 1 < -0.045:
        return True
    return False
    
'''
def is_3_black_crows(stock, data):
    # talib.CDL3BLACKCROWS
    his =  attribute_history(stock, 2, '1d', ('close','open'), skip_paused=True, df=False)
    closeArray = list(his['close'])
    closeArray.append(data[stock].close)
    openArray = list(his['open'])
    openArray.append(get_current_data()[stock].day_open)

    if closeArray[0]<openArray[0] and closeArray[1]<openArray[1] and closeArray[2]<openArray[2]:
        if closeArray[-1]/closeArray[0]-1>-0.045:
            his2 =  attribute_history(stock, 4, '1d', ('close','open'), skip_paused=True, df=False)
            closeArray1 = his2['close']
            if closeArray[0]/closeArray1[0]-1>0:
                return True
    return False
'''

def market_stop_loss_by_28_index(context, count):
    # 回看指数前20天的涨幅
    gr_index2 = get_growth_rate(g.index2)
    gr_index8 = get_growth_rate(g.index8)

    if gr_index2 <= g.index_growth_rate and gr_index8 <= g.index_growth_rate:
        if (g.minute_count_28index_drop == 0):
            log.info("当前二八指数的20日涨幅同时低于[%.2f%%], %s指数: [%.2f%%], %s指数: [%.2f%%]" \
                %(g.index_growth_rate*100, get_security_info(g.index2).display_name, gr_index2*100, get_security_info(g.index8).display_name, gr_index8*100))

            #log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index2).display_name, gr_index2*100))
            #log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index8).display_name, gr_index8*100))
        g.minute_count_28index_drop += 1
    else:
        # 不连续状态归零
        if g.minute_count_28index_drop < count:
            g.minute_count_28index_drop = 0

    if g.minute_count_28index_drop >= count:
        if g.minute_count_28index_drop == count:
            log.info("==> 当日%s指数和%s指数的20日增幅低于[%.2f%%]已超过%d分钟，执行28指数止损" \
                %(get_security_info(g.index2).display_name, get_security_info(g.index8).display_name, g.index_growth_rate*100, count))

        clear_position(context)
        g.day_count = 0
        return True
        
    return False

# 个股止损
def stock_stop_loss(context, data):
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    show_log = False
    if ((hour >= 9 and hour <= 11) and (minute == 30)) or ((hour >= 13 and hour <= 15) and (minute == 0)):
        show_log = True
    for stock in context.portfolio.positions.keys():
        cur_price = data[stock].close
        xi = attribute_history(stock, 2, '1d', 'high', skip_paused=True)
        ma = xi.max()
        try:
            if g.last_high[stock] < cur_price:
                g.last_high[stock] = cur_price
        except KeyError:
            g.last_high[stock] = 0
            
        threshold = get_stop_loss_threshold(stock, g.period)
        # 每天指定时间输出
        if show_log:
            log.debug("个股止损阈值, stock: %s, threshold: %f" %(stock, threshold))
        if cur_price < g.last_high[stock] * (1 - threshold) * g.ajust_rate_4_stock_stop_loss:
            log.info("==> 个股止损, stock: %s, cur_price: %f, last_high: %f, threshold: %f" 
                %(stock, cur_price, g.last_high[stock], threshold))

            position = context.portfolio.positions[stock]
            if close_position(context, position):
                g.day_count = 0

# 个股止盈
def stock_stop_profit(context, data):
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    show_log = False
    if ((hour >= 9 and hour <= 11) and (minute == 30)) or ((hour >= 13 and hour <= 15) and (minute == 0)):
        show_log = True
    for stock in context.portfolio.positions.keys():
        position = context.portfolio.positions[stock]
        cur_price = data[stock].close
        threshold = get_stop_profit_threshold(stock, g.period)
        # 每天指定时间输出
        if show_log:
            log.debug("个股止盈阈值, stock: %s, threshold: %f" %(stock, threshold))
        if cur_price > position.avg_cost * (1 + threshold) * g.ajust_rate_4_stock_stop_profit:
            log.info("==> 个股止盈, stock: %s, cur_price: %f, avg_cost: %f, threshold: %f" 
                %(stock, cur_price, g.last_high[stock], threshold))

            position = context.portfolio.positions[stock]
            if close_position(context, position):
                g.day_count = 0

# 获取个股前n天的m日增幅值序列
# 增加缓存避免当日多次获取数据
def get_pct_change(security, n, m):
    pct_change = None
    if security in g.pct_change.keys():
        pct_change = g.pct_change[security]
    else:
        h = attribute_history(security, n, unit='1d', fields=('close'), skip_paused=True)
        pct_change = h['close'].pct_change(m) # 3日的百分比变比（即3日涨跌幅）
        g.pct_change[security] = pct_change
    return pct_change
        
# 计算个股回撤止损阈值
# 即个股在持仓n天内能承受的最大跌幅
# 算法：(个股250天内最大的n日跌幅 + 个股250天内平均的n日跌幅)/2
# 返回正值
def get_stop_loss_threshold(security, n = 3):
    pct_change = get_pct_change(security, 250, n)
    #log.debug("pct of security [%s]: %s", pct)
    maxd = pct_change.min()
    #maxd = pct[pct<0].min()
    avgd = pct_change.mean()
    #avgd = pct[pct<0].mean()
    # maxd和avgd可能为正，表示这段时间内一直在增长，比如新股
    bstd = (maxd + avgd) / 2

    # 数据不足时，计算的bstd为nan
    if not isnan(bstd):
        if bstd != 0:
            return abs(bstd)
        else:
            # bstd = 0，则 maxd <= 0
            if maxd < 0:
                # 此时取最大跌幅
                return abs(maxd)

    return 0.099 # 默认配置回测止损阈值最大跌幅为-9.9%，阈值高貌似回撤降低

# 计算个股止盈阈值
# 算法：个股250天内最大的n日涨幅
# 返回正值
def get_stop_profit_threshold(security, n = 3):
    pct_change = get_pct_change(security, 250, n)
    maxr = pct_change.max()
    
    # 数据不足时，计算的maxr为nan
    # 理论上maxr可能为负
    if (not isnan(maxr)) and maxr != 0:
        return abs(maxr)
    return 0.30 # 默认配置止盈阈值最大涨幅为30%

# 获取股票n日以来涨幅，根据当前价计算
# n 默认20日
# endday 结束日（0为当前报价，1为前第1日，2为前第2日...）
def get_growth_rate(security, n=20, endday=0):
    lc = get_close_price(security, n+endday)
    if endday == 0:
        c = get_close_price(security, 1, '1m')
    else:
        c = get_close_price(security, endday)
    
    if not isnan(lc) and not isnan(c) and lc != 0:
        return (c - lc) / lc
    else:
        log.error("数据非法, security: %s, %d日收盘价: %f, 当前价: %f" %(security, n, lc, c))
        return 0

# 获取前n个单位时间当时的收盘价
def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, ('close'), True)['close'][0]

# 开仓，买入指定价值的证券
# 报单成功并成交（包括全部成交或部分成交，此时成交量大于0），返回True
# 报单失败或者报单成功但被取消（此时成交量等于0），返回False
def open_position(context, security, value):
    order = order_target_value_(context, security, value)
    if order != None and order.filled > 0:
        # 报单成功并有成交则初始化最高价
        cur_price = get_close_price(security, 1, '1m')
        g.last_high[security] = cur_price
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
            # 全部成交则删除相关证券的最高价缓存
            if security in g.last_high:
                g.last_high.pop(security)
            else:
                log.warn("last high price of %s not found" %(security))
            return True

    return False

# 清空卖出所有持仓
def clear_position(context):
    if context.portfolio.positions:
        log.info("==> 清仓，卖出所有股票")
        for stock in context.portfolio.positions.keys():
            position = context.portfolio.positions[stock]
            close_position(context, position)

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
        posInPercent = value/context.portfolio.total_value
        curr_data = get_current_data()
        secname = curr_data[order.security].name
        if g.is_mail_inform_enabled:
            # mail to inform clients
            mail_to_clients(order.security, secname, posInPercent, order.price, tradedatetime, '小市值策略改进版')
        if g.is_autotrader_inform_enabled:
            # inform auto trader to do the trade
            autotrader_stock_trade('小市值策略改进版', order.security, secname, posInPercent, order.price, tradedatetime, order.order_id)
            if g.online_response_code == 0:
                rspcode = do_record_offline()
                if rspcode != g.online_response_code:
                    g.online_response_code = rspcode
                    rspcode = mail_to_report(rspcode)
    return order


# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]

# 过滤ST及其他具有退市标签的股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list 
        if not current_data[stock].is_st 
        and 'ST' not in current_data[stock].name 
        and '*' not in current_data[stock].name 
        and '退' not in current_data[stock].name]
        
# 过滤涨停的股票
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    
    # 已存在于持仓的股票即使涨停也不过滤，避免此股票再次可买，但因被过滤而导致选择别的股票
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
        or last_prices[stock][-1] < current_data[stock].high_limit]
    #return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
    #    or last_prices[stock][-1] < current_data[stock].high_limit * 0.995]

# 过滤跌停的股票
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
        or last_prices[stock][-1] > current_data[stock].low_limit]
    #return [stock for stock in stock_list if last_prices[stock][-1] > current_data[stock].low_limit]
    #return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
    #    or last_prices[stock][-1] > current_data[stock].low_limit * 1.005]
    
# 过滤黑名单股票
def filter_blacklist_stock(context, stock_list):
    blacklist = get_blacklist(context)
    return [stock for stock in stock_list if stock not in blacklist]

# 过滤创业版股票
def filter_gem_stock(context, stock_list):
    return [stock for stock in stock_list if stock[0:3] != '300']

# 过滤20日增长率为负的股票
def filter_by_growth_rate(stock_list, n):
    return [stock for stock in stock_list if get_growth_rate(stock, n) > 0]

# 股票评分
def rank_stocks(data, stock_list, score_plus_list):
    dst_stocks = {}
    for stock in stock_list:
        h = attribute_history(stock, 130, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        low_price_130 = h.low.min()
        high_price_130 = h.high.max()

        avg_15 = data[stock].mavg(15, field='close')
        cur_price = data[stock].close

        #avg_15 = h['close'][-15:].mean()
        #cur_price = get_close_price(stock, 1, '1m')

        #score = (cur_price-low_price_130) + (cur_price-high_price_130) + (cur_price-avg_15)
        score = ((cur_price-low_price_130) + (cur_price-high_price_130) + (cur_price-avg_15)) / cur_price
        if g.is_rank_stock_score_plus_allowed:
            if stock in score_plus_list:
                #log.info("股票%s上升形态，加分%f(股价*%f)" 
                #         %(stock, g.rank_stock_score_plus_factor * cur_price, g.rank_stock_score_plus_factor))
                #score -= g.rank_stock_score_plus_factor * cur_price
                log.info("股票%s上升形态，加分%f(股价*%f)" 
                         %(stock, g.rank_stock_score_plus_factor, g.rank_stock_score_plus_factor))
                score -= g.rank_stock_score_plus_factor
        dst_stocks[stock] = score

    df = pd.DataFrame(dst_stocks.values(), index=dst_stocks.keys())
    df.columns = ['score']
    df = df.sort(columns='score', ascending=True)
    return df.index

'''
# 过滤新股
def filter_new_stock(stock_list):
    stocks = get_all_securities(['stock'])
    stocks = stocks[(context.current_dt.date() - stocks.start_date) > datetime.timedelta(60)].index
'''

# 选股
# 选取指定数目的小市值股票，再进行过滤，最终挑选指定可买数目的股票
def pick_stocks(context, data):
    # 获取备选股票
    candidates = []
    # 是否使用指数池选股配置
    if g.index_stock_2_select:
        # 指数池
        for index in g.index_pool:
            candidates += get_index_stocks(index)
    else:
        # 备选股票池，空表示所有股票备选
        if len(g.stock_candidates) == 0:
            if g.large_market_share_index_pool_used:
                # 判断是否出现二八分化
                gr_index2_3d = get_growth_rate(g.index2, n=3, endday=2)
                gr_index2_5d = get_growth_rate(g.index2, 5)
                gr_index8_3d = get_growth_rate(g.index8, n=3, endday=2)
                gr_index8_5d = get_growth_rate(g.index8, 5)
                if (context.current_dt.date() > datetime.datetime(2007, 1, 26).date()) \
                   and (gr_index2_5d > gr_index2_3d) and ((gr_index2_5d - gr_index2_3d) - (gr_index8_5d - gr_index8_3d) > g.large_market_share_trend_judge_param):
                    candidates = get_index_stocks(g.large_market_share_index)
                    log.info("大盘股指数（%s）远超小盘股指数（%s），大盘股指数作为股票池", g.index2, g.index8)
                else:
                    candidates = list(get_all_securities(['stock']).index)
                    log.info("所有股票作为股票池")
            else:
                candidates = list(get_all_securities(['stock']).index)
                log.info("所有股票作为股票池")
        else:
            candidates = g.stock_candidates

    q = query(valuation.code).filter(
            valuation.code.in_(candidates)
        )
    if g.pick_by_pe:
        q = q.filter(
            valuation.pe_ratio > g.min_pe, 
            valuation.pe_ratio < g.max_pe
            )

    if g.pick_by_eps:
        q = q.filter(
            indicator.eps > g.min_eps,
            #valuation.turnover_ratio > 3
            )

    q = q.order_by(
                valuation.market_cap.asc()
            ).limit(
                g.pick_stock_count
            )
    
    df = get_fundamentals(q)
    stock_list = list(df['code'])

    if g.filter_gem:
        stock_list = filter_gem_stock(context, stock_list)
        
    if g.filter_blacklist:
        stock_list = filter_blacklist_stock(context, stock_list)
        
    stock_list = filter_paused_stock(stock_list)
    stock_list = filter_st_stock(stock_list)
    stock_list = filter_limitup_stock(context, stock_list)
    stock_list = filter_limitdown_stock(context, stock_list)

    # 根据20日股票涨幅过滤效果不好，故注释
    #stock_list = filter_by_growth_rate(stock_list, 20)
    
    if g.is_rank_stock:
        if len(stock_list) > g.rank_stock_count:
            stock_list = stock_list[:g.rank_stock_count]

        #log.debug("评分前备选股票: %s" %(stock_list))
        if len(stock_list) > 0:
            score_plus_list = []
            if g.is_rank_stock_score_plus_allowed:
                score_plus_list = get_in_trends(context, stock_list)
            stock_list = rank_stocks(data, stock_list, score_plus_list)
        #log.debug("评分后备选股票: %s" %(stock_list))
    
    # 选取指定可买数目的股票
    if len(stock_list) > g.buy_stock_count:
        stock_list = stock_list[:g.buy_stock_count]
    return stock_list

# 获取所有多头趋势股票
# 输入一list有效股票
# 输出一list，为所有符合从小到长均线排列从大到小的股票
def get_in_trends(context, available_stocks):
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

# 根据待买股票创建或调整仓位
# 对于因停牌等原因没有卖出的股票则继续持有
# 始终保持持仓数目为g.buy_stock_count
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions.keys():
        if stock not in buy_stocks:
            log.info("stock [%s] in position is not buyable" %(stock))
            position = context.portfolio.positions[stock]
            close_position(context, position)
        else:
            log.info("stock [%s] is already in position" %(stock))
    
    # 根据股票数量分仓
    # 此处只根据可用金额平均分配购买，不能保证每个仓位平均分配
    position_count = len(context.portfolio.positions)
    if g.buy_stock_count > position_count:
        value = context.portfolio.available_cash / (g.buy_stock_count - position_count)

        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(context, stock, value):
                    if len(context.portfolio.positions) == g.buy_stock_count:
                        break

'''
--------------------------------------------------------------------------------

更新：

2016.11.15

v2.0.7
增加根据28指数值实时止损，效果暂不理想，默认关闭
感谢@零零发 的分享，完善根据大盘价格止损，改为根据160日高低价格进行条件止损
优化日志，更易读
感谢@ordo，优化选股代码
调整默认参数，并非最优，最优我也不知道:-)
注：
1. 默认3日2股评分大盘价格及三黑鸦止损
2. 持股数量一般会影响策略波动性，数量太少，策略波动较大，建议股票数目 >= 3，然后调整
参数达到一个好的配置
3. 三黑鸦会降低回测，同时收益也会降低

2016.08.31

v2.0.6
完善三黑鸦判定算法，放宽判定条件，在前日三黑鸦形态下，当日为跌的分钟计数达到指定
值，则进行止损，此方法主要为了增加三黑鸦的有效性

2016.08.30

v2.0.5
根据百度百科描述修正三黑鸦算法，根据前4日数据判断，在三黑鸦形态下当日为跌的分钟计
数达到指定值后，进行止损，修正潜在bug

2016.08.19

v2.0.4
修改止盈止损阈值的计算为根据调仓间隔日期获取，比如5日调仓则获取历史3日的幅度

2016.08.17

v2.0.3
拆分三黑鸦和指数价格止损及配置，优化大盘三黑鸦及指数价格止损，避免每分钟反复获取
数据处理，提高回测效率

2016.08.16

v2.0.2
修复部分小bug，感谢 @michaeljrqiu @射手摩羯座的提醒

v2.0.1
完善了平仓的盈亏统计，主要针对部分成交，另外修正了部分平仓导致的最高价缓存被删除
的问题

需要更新tradestat.py

2016.08.15

v2.0.0
感谢@az大神的策略分享，增加EPS选股，选股评分，大盘三黑鸦及高低价止损，个股止盈止
损，全部可选配置

默认参数配置只为保留1.2.8版本的收益和回撤，如果想进行其他调整，请自行调配参数

v1.2.8
完善买卖接口，聚宽对于部成部撤的报单，返回的报单状态为已撤，故修改为根据报单成交
量来判断报单是否成功，同期收益回撤不变

2016.08.13

v1.2.7
优化买卖接口，解决涨跌停股票创建报单成功但被取消导致不必要的后处理，同期收益回撤
不变

2016.07.19

v1.2.6
感谢 @Special 的指正，修正了胜率统计的bug，避免在股票卖出失败的时候多进行了一次
统计，结果交易次数减少了，同期胜率降低了1%，收益回撤等其他不变

2016.07.14

v1.2.5
增加跌停股票过滤，多谢 @沙米 建议，同期提高了不少收益率，提高了胜率，降低了最大
单股亏损，回撤基本不变

v1.2.4
完善日志输出，打印策略配置参数，调整主要日志为中文

2016.07.13

v1.2.3
完善ST及停牌股票的过滤（来自 @菜菜午出头），优化日志

2016.07.12

v1.2.2
优化增幅计算代码

v1.2.1
改进黑名单配置，感谢@az的指正，修正了创业板股票判断的bug

v1.2.0
感谢 @zw @沙米 的完善，在其基础上增加了过滤控制，可选择配置市盈率选股、过滤创
业板及过滤黑名单，设置了pe参数，增加了注释，因为配置了pe选股及过滤了创业板，收
益有所降低，但是回撤也相应降低了

注：黑名单有时效性，回测已注释

2016.07.02

v1.1.2
修正调仓日因持仓股票涨停被过滤导致本该继续持有的股票被卖出的问题，收益回撤影响
不大，提高了单股盈利

说明：当前调仓因股票停牌不能卖出的时候会继续持有，始终保持指定数目的股票持仓

2016.07.01

v1.1.1
根据 @zx1967 的反馈，调整了选股数目大小（g.selected_stock_cnt = 100，其实可以更
大），尽量避免数目过小而恰巧全部过滤掉以致最终可买股票为空，结果收益更高了，回
撤差不多

2016.06.30

v1.1.0
感谢 @莫邪的救赎 的建议，修改为run_daily执行，主要是提高了回测速度，回测时间缩
短了近一半

-------------------------------------------------------------------------------
'''

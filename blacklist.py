#coding=utf-8

import datetime as dt
# blacklist.py
# 建议在研究里建立文件blacklist.py，然后将这段代码拷贝进blacklist.py
# 模拟运行的时候只需要更新研究里的数据即可，这样可在不修改模拟运行代码的情况下
# 修改黑名单

# 配置股票黑名单
# 列出当且极不适宜购买的股票
# 注：1. 黑名单有时效性，回测的时候最好不使用，模拟交易建议使用
#     2. 用一模块或者大数据分析收集这类股票，定时更新
def get_blacklist(context):

   # 黑名单一览表，更新时间 2016.7.10 by 沙米
    # 科恒股份、太空板业，一旦2016年继续亏损，直接面临暂停上市风险
    blacklist = [{'StartDate': dt.datetime(2016, 7, 10), 
                 'EndDate': dt.datetime(2021, 7, 10), 
                 'BlkList': ["600656.XSHG","300372.XSHE","600403.XSHG","600421.XSHG","600733.XSHG","300399.XSHE",
                 "600145.XSHG","002679.XSHE","000020.XSHE","002330.XSHE","300117.XSHE","300135.XSHE",
                 "002566.XSHE","002119.XSHE","300208.XSHE","002237.XSHE","002608.XSHE","000691.XSHE",
                 "002694.XSHE","002715.XSHE","002211.XSHE","000788.XSHE","300380.XSHE","300028.XSHE",
                 "000668.XSHE","300033.XSHE","300126.XSHE","300340.XSHE","300344.XSHE","002473.XSHE"]}]
    listInEffective = []
    for list in blacklist:
        if context.current_dt >= list['StartDate'] and context.current_dt < list['EndDate']:
            listInEffective += list['BlkList']
    return listInEffective


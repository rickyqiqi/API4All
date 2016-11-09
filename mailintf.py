#coding=utf-8

import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from kuanke.user_space_api import *

def mail_to_clients(security, secname, value, price, tradedatetime, policyname):
    # 第三方 SMTP 服务
    mail_host=""  #设置服务器
    mail_user=""    #用户名
    mail_pass=""   #口令
    sender = ""
    receivers = []  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

    if g.real_market_simulate:
        mailinfofile = 'config/mailreal.conf'
    else:
        mailinfofile = 'config/mailloop.conf'

    try:
        jsoncontent = read_file(mailinfofile)
        content = json.loads(jsoncontent)

        if 'smtphost' in content:
            mail_host = content["smtphost"]
        if 'account' in content:
            mail_user = content["account"]
        if 'password' in content:
            mail_pass = content["password"]
        if 'sender' in content:
            sender = content["sender"]
        if 'receivers' in content:
            receivers = content["receivers"]
    except:
        log.error("配置文件%s读取错误" %(mailinfofile))

    if mail_host == "":
        log.error("SMTP主机配置空")
        return
    elif mail_user == "":
        log.error("邮件发送账户空")
        return
    elif len(receivers) == 0:
        log.error("邮件接受列表空")
        return

    mail_msg = """<p>策略名称：%s</p><p>调仓日期：%s</p><p>股票名称：%s</p><p>股票代码：%s</p><p>目标仓位：%.4f%%</p><p>目标价格：%.2f</p>""" %(policyname, tradedatetime.strftime("%Y-%m-%d %H:%M:%S"), secname, security, value*100, price)
    message = MIMEText(mail_msg, 'html', 'utf-8')
    message['From'] = Header("量化交易策略", 'utf-8')
    message['To'] =  Header("用户", 'utf-8')

    subject = policyname + '买卖信号'
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP() 
        smtpObj.connect(mail_host, 25)    # 25 为 SMTP 端口号
        smtpObj.login(mail_user,mail_pass)  
        smtpObj.sendmail(sender, receivers, message.as_string())
        log.info("邮件发送成功")
    except smtplib.SMTPException:
        log.error("无法发送邮件")
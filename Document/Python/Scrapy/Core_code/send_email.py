#-*-coding:utf8-*-
import time
import MySQLdb
import datetime
import os
import shutil
import sys
import urllib2
# import chardet
from optparse import OptionParser
path1 = (os.getcwd())
if os.name != 'nt':
	path1 = path1.split('/Scrapy_crawlers')[0] + '/Scrapy_crawlers/Shop_site_crawler'
else:
	path1 = path1.split('\Scrapy_crawlers')[0] + '\Scrapy_crawlers\Shop_site_crawler'
sys.path.append(path1)
from settings import DBS,TO_EMAILS_LIST_4,TO_EMAILS_LIST_5,FROM_EMAIL_DICT
from settings import TO_EMAILS_LIST_1,TO_EMAILS_LIST_2,TO_EMAILS_LIST_3
from zsl_spider_lib import Html,ZYMail_z,zip_dir
from zsl_spider_lib import get_conn
from zsl_spider_lib import select_data
from zsl_spider_lib import select_description,send_email_att
from zsl_spider_lib import mysql_data_2_execl,ssh_2_remote_db_sel_data

today = time.strftime("%Y-%m-%d")
yestday = str(time.strftime("%Y-%m-%d",time.localtime((int(time.time())-3600*24))))
ysday = str(time.strftime("%Y%m%d",time.localtime((int(time.time())-3600*24))))
ys_3_day = str(time.strftime("%Y%m%d",time.localtime((int(time.time())-3600*72))))
ys_8_day = str(time.strftime("%Y-%m-%d",time.localtime((int(time.time())-3600*24*8))))
ys_9_day = str(time.strftime("%Y-%m-%d",time.localtime((int(time.time())-3600*24*9))))


def parse_opts():
	'''
	Function doc
	定义 文件接收参数的地方
	'''
	parser = OptionParser(usage="%prog [options] [ [target] | -l | -L <target> ]",
		description="Deploy Scrapy project to Scrapyd server")
	parser.add_option("-T", "--dt", help="the datetime like 2014-06-06")
	parser.add_option("-F", "--func", help="function")
	parser.add_option("-k", "--key_type", default="", help=" database type ")
	return parser.parse_args()
opts, args = parse_opts()


def getXtepPeerShopInfo(conn):
	'''
	Function doc
	获取特步关注店铺的店铺名称
	'''
	pass


def xtep_execl_email():
	'''
	Function doc
	1.查询特步官方旗舰店数据
	2.制作execl表格
	3.发送邮件
	'''
	ystday = time.strftime("%Y-%m-%d",time.localtime((int(time.time())-3600*24)))
	today = time.strftime("%Y-%m-%d")
	shop_info = ['鸿星尔克童装旗舰店','anta安踏童装旗舰店','骆驼户外官方旗舰店','rax户外旗舰店','迈途旗舰店','探路者官方旗舰店','乔丹官方旗舰店','361度户外旗舰店','361度童装旗舰店','361度官方旗舰店','鸿星尔克官方旗舰店','安踏官方网店','李宁官方网店','New Balance旗舰店','adidas官方旗舰店','NIKE官方旗舰店','特步官方旗舰店','匹克官方旗舰店','厦门特步淘麦专卖店','蓝瞳运动专营店','乔丹童装官方旗舰店','特步乐麦专卖店','liningkids童装旗舰店','特步童装旗舰店','Kappa官方旗舰店','UNDER ARMOUR官方旗舰店']
	dirname = 'sale%s'%(time.strftime("%Y%m%d"))
	zipfile = "%s.zip"%dirname

	if os.path.exists(dirname):
		pass
	else:
		os.makedirs(dirname)

	#制作execl
	for sk in shop_info:
		sql = " SELECT * FROM xtep_item_sale_stat WHERE `昨日日期` = '%s' AND `店铺名称` = '%s' " % (ystday,sk)
		print sql
		fname = '%s.csv'%(sk)
		#查询数据
		data,description = ssh_2_remote_db_sel_data('qqd_ydhy',sql) 
		mysql_data_2_execl(fname,data,description)
		#移动文件到文件夹
		shutil.move(fname,dirname+'/'+fname)

	#压缩文件
	zip_dir(dirname,zipfile)

	#发送邮件
	mail_to_title = '特步行业关注店铺销售额统计'
	mail_to_list = TO_EMAILS_LIST_5
	send_email_att(mail_to_title,mail_to_list,zipfile) 

	#删除生成的文件和压缩包
	if os.path.isfile(zipfile):  
		os.remove(zipfile)  
		print zipfile+" removed!"  
	if os.path.isdir(dirname):  
		shutil.rmtree(dirname,True)  
		print "dir "+dirname+" removed!" 


def ydhy_sql():
	'''
	Function doc
	统计 淘宝运动行业 商品抓取情况 
	'''
	sql = ''' 
		SELECT
		a.dt,
		a.num num1,
		b.num num2,
		c.num num3,
		CASE
			WHEN a.num is NULL THEN 'is OK!'
			WHEN c.num < 0.1*a.num THEN 'is OK!'
			ELSE '<font color="red"> <b>is not OK! </b></font>'
		END stauts
		FROM
		( SELECT count(1) num ,insertDate dt FROM shop_get_item_list_new WHERE insertDate = '%s' )a
		JOIN
		( SELECT count(DISTINCT nid) num FROM ods_tb_item_info WHERE adddate = '%s' AND fetch_api = 'ydhy_tb_item_id' ) b
		JOIN
		( select count(DISTINCT itemid) num from shop_get_item_list_new where insertDate ='%s' and (itemno='0' or stock='0') ) c
		 ''' % (yestday,today,yestday)
	return [sql]


def sdian_sql():
	'''
	Function doc
	统计 多店 7天每天的抓到的商品总数
	'''
	sql = '''
		SELECT 
		count(1) as 抓到货号和销量的商品总数 ,
		dt as 抓取日期
		FROM 
			tb_item_price
		WHERE dt > FROM_DAYS(TO_DAYS(NOW())-7) GROUP BY dt
		'''
	return [sql]


def xtep_shops_tb_sql():
	'''
	Function doc
	统计 淘宝多店 商品价格抓取情况
	'''
	# UPDATE
	# tb_ware_list_get a,
	# ods_tb_item_info b
	# SET a.sale_price = b.price
	# WHERE a.dt = '2017-02-25' AND a.num_iid = b.nid AND b.adddate = '2017-02-26'
	sql = '''
		SELECT
		a.dt,
		a.num1,
		b.num2,
		CASE
			WHEN a.num1 is null THEN 'is OK!'
			WHEN b.num2 < 0.05*a.num1 THEN 'is OK!'
			ELSE '<font color="red"> <b>is not OK! </b></font>'
		END stauts
		FROM
		( SELECT count(distinct num_iid) num1, dt FROM tb_ware_list_get WHERE dt = '%s' ) a
		INNER JOIN
		( SELECT count(distinct num_iid) num2 FROM tb_ware_list_get WHERE sale_price is NULL 
		AND dt = '%s' ) b ''' % (yestday,yestday)
	return [sql]


def scrapy_sql():
	'''
	Function doc
	行业爬虫任务执行信息统计
	'''
	sql = ''' SELECT  * FROM ind_sp_task_exec_info_st  WHERE up_date = '%s' ''' % (today)
	return [sql]


def qqd_sql(table):
	'''
	Function doc
	sql_2 统计 全渠道 商品表   数据抓取情况
	sql_3 统计 全渠道 店铺信息 授权店铺和未授权店铺销量抓取情况统计
	sql_5 统计 全渠道 商品表   分平台商品没有货号的数量统计
	Parameter doc
	@table : 表名
	'''
	sql_2 = '''
		SELECT 
		count(1) as keywords_search_info每个平台抓取到的数据量,
		IFNULL(fetch_api,'sum') as 抓取数据的爬虫,
		adddate as 抓取日期,
		min(addtime) as 开始抓取的时间,
		max(addtime) as 结束抓取的时间
		FROM %s WHERE  adddate = '%s' GROUP BY fetch_api  WITH ROLLUP ''' % (table,today)
	sql_3 = ''' SELECT * FROM shops_sale_info_stat WHERE up_date = '%s' ''' % (today)
	sql_5 = '''
		SELECT 
		count(itemno) as 货号为11111111的商品数量表示未抓到,
		itemno as 货号,
		isTmall as 平台类型,
		type as PC端或者无线,
		fetch_api as 抓取的爬虫名称,
		adddate as keywords_search_info表抓取日期
		FROM %s WHERE adddate='%s' AND ( itemno ='11111111' OR itemno = '' ) GROUP BY fetch_api 
		ORDER BY  isTmall ''' % (table,today)
		
	return [sql_2,sql_3,sql_5]


def xtep_shops_tb_text(conn):
	'''
	Function doc
	统计 淘宝多店 商品价格抓取情况 拼接成字符串
	@return text

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	sqls = xtep_shops_tb_sql() #list
	datas = select_data(conn,'tb_ware_list_get',sqls[0])
	s_pk = ''

	for data in datas:
		num1 	= str(data[1])
		num2 	= str(data[2])
		stauts 	= str(data[3])	
		s_pk 	= '''today 需要抓取价格的商品id数量: %s 价格为空商品id数量: %s ... %s<br> 
		''' % (num1,num2,stauts)

	return s_pk


def ydhy_text(conn):
	'''
	Function doc
	统计 淘宝运动行业 商品抓取情况 拼接成字符串
	@return text

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	sqls = ydhy_sql() #list
	datas = select_data(conn,'shop_get_item_list_new',sqls[0])
	s_pk = ''

	for data in datas:
		num1 	= str(data[1])
		num2 	= str(data[2])
		num3 	= str(data[3])
		stauts 	= str(data[4])	
		s_pk = '''today 需要抓取的商品数量: %s 实际抓取到的商品数量: %s 未抓取到货号的商品数量 %s ... %s<br> 
		''' % (num1,num2,num3,stauts)

	return s_pk


def keywords_search_info_text(conn,table):
	'''
	Function doc
	统计 全渠道 商品信息表 
		每个爬虫当天抓取的数据量 与 7天平均抓取的数据量进行对比
	@return text

	Parameter doc
	@conn : Mysql数据库 连接实例
	@table: 表名
	'''
	f_list = [
		'qqd_amazon_search',
		'qqd_dd_search',
		'qqd_jd_search',
		'qqd_sn_search',
		'qqd_tbwx_search',
		'qqd_tb_search',
		'qqd_t_itemno_search',
		'qqd_yhd_search'] # 爬虫列表
	sql_1 = '''
		SELECT
		c.adddate,
		c.fetch_api,
		c.num,
		b.b_num,
		CASE
		WHEN b.b_num is NULL THEN
			'is OK!'
		WHEN c.num > b.b_num * 0.7 THEN
			'is OK!'
		ELSE
			'<font color="red"> <b>is not OK! </b></font>'
		END stauts
		FROM 
			(SELECT adddate, fetch_api, count(1) num FROM %s WHERE adddate = '%s' GROUP BY adddate, fetch_api) c
		LEFT JOIN 
			(SELECT fetch_api,round(avg(num),2) b_num FROM ( SELECT adddate, fetch_api, count(1) num FROM %s WHERE adddate > '%s' AND adddate < '%s' GROUP BY adddate,fetch_api) a GROUP BY fetch_api ORDER BY 1) b 
		ON c.fetch_api = b.fetch_api ''' % (table,today,table,ys_8_day,today)
	datas = select_data(conn,table,sql_1)
	strs_pk = []
	f_list2 = []

	for data in datas:
		fetch_api 	= str(data[1])
		count 		= str(data[2])
		count_avg 	= str(data[3])
		stauts 	    = str(data[4])
		if fetch_api in f_list:
			s_pk = ''' %s : today: %s    avg: %s %s <br> ''' % (fetch_api,count,count_avg,stauts)
			strs_pk.append(s_pk)
		f_list2.append(fetch_api)
	
	strs_pk2 = []
	s_fs = ''

	if len(f_list2) < len(f_list):#当平台没数据的时候
		f_list3 = list(set(f_list).difference(set(f_list2))) #求list 差集
		for i in f_list3:
			s_f = ''' %s : today: <font color="red"> <b>0 </b></font>,<font color="red"> <b>is not OK! </b></font><br>''' % (i)
			strs_pk2.append(s_f)
		s_fs = '\n'.join(strs_pk2)

	return ('\n'.join(strs_pk)) + s_fs


def shops_sale_info_stat_text(conn,key_type):
	'''
	Function doc
	店铺销量统计 
	@return text

	Parameter doc
	@conn : Mysql数据库 连接实例
	@key_type: 全渠道类型(如:xtep,mg)
	'''
	sql = '''
		SELECT a.sale, a.sale_b0, a.sale_s0, a.sale0_pr, a.brand,b.avg7pr 
		FROM shops_sale_info_stat a
		LEFT JOIN
		( SELECT brand,round(avg(sale0_pr),0) avg7pr FROM shops_sale_info_stat WHERE up_date > '%s' ) b
		ON a.brand = b.brand
		WHERE up_date = '%s' ''' % (ys_8_day,today)
	datas = select_data(conn,'shops_sale_info_stat',sql)
	s_pk = ''

	for data in datas:
		sale 		= str(data[0])
		sale_b0 	= str(data[1])
		sale_s0 	= str(data[2])
		sale0_pr 	= str(data[3])
		brand 		= str(data[4])
		avg7pr		= 0 if str(data[5]) == 'None' else int(data[5])*0.8

		if sale0_pr != '0' :
			stauts = 'is OK!' if int(sale0_pr.strip('%')) > avg7pr else '<font color="red"><b>is not OK!</b></font>'
		else:
			stauts = '<font color="red"><b>is not OK!</b></font>'
				
		s_pk = '''<font color="Green"><b>店铺销量统计</b></font><br> 
		%s : shop sale today 总销量: %s 授权店铺销量: %s 未授权店铺销量: %s  授权店铺销量占比 %s  %s 授权店铺7天平均销量占比 %s <br> 
		''' % (brand,sale,sale_b0,sale_s0,sale0_pr,stauts,str(avg7pr*1.25)+'%')

	return s_pk


def lost_itemno_text(conn,table):
	'''
	Function doc
	统计 全渠道 商品信息表 没货号商品数量
	@return text

	Parameter doc
	@conn : Mysql数据库 连接实例
	@table: 表名
	'''
	f_list = [
		'qqd_amazon_search',
		'qqd_dd_search',
		'qqd_jd_search',
		'qqd_sn_search',
		'qqd_tbwx_search',
		'qqd_tb_search',
		'qqd_t_itemno_search',
		'qqd_yhd_search']

	sql = '''
		SELECT
		a.fetch_api,
		a.num,
		b.num num_avg7,
		CASE 
			WHEN b.num is NULL THEN 'is OK!'
			WHEN a.fetch_api in ('qqd_t_itemno_search','qqd_tb_search') AND a.num < b.num+1000 THEN 'is OK!'
			WHEN a.num < b.num+100 THEN 'is OK!'
			ELSE '<font color="red"> <b>is not OK! </b></font>'
		END stauts
		FROM
		( SELECT  count(itemno) num, fetch_api FROM %s WHERE adddate = '%s' AND (itemno ='' OR itemno = '11111111')  GROUP BY fetch_api ORDER BY 1 ) a
		LEFT JOIN
		( SELECT round(avg(a.num),2) num, a.fetch_api fetch_api 
			FROM ( SELECT  count(itemno) num, fetch_api FROM %s WHERE adddate > '%s' AND adddate < '%s' AND (itemno ='' OR itemno = '11111111')  GROUP BY adddate,fetch_api ORDER BY  isTmall) a 
			GROUP BY a.fetch_api ORDER BY 1 ) b
		ON a.fetch_api = b.fetch_api ''' % (table,today,table,ys_8_day,today)
	datas = select_data(conn,table,sql)
	strs_pk = []
	# f_list2 = []

	for data in datas:
		fetch_api 	= str(data[0])
		count 		= str(data[1])
		count_avg 	= str(data[2])
		stauts 	    = str(data[3])
		if fetch_api in f_list:
			s_pk = ''' %s : today: %s    avg: %s %s <br> ''' % (fetch_api,count,count_avg,stauts)
			strs_pk.append(s_pk)
		# f_list2.append(fetch_api)

	# strs_pk2 = []
	# s_fs = ''

	# if len(f_list2) < len(f_list):#当平台没数据的时候
	# 	f_list3 = list(set(f_list).difference(set(f_list2))) #求list 差集
	# 	for i in f_list3:
	# 		s_f = ''' %s : today: <font color="red"> <b>0 </b></font>,<font color="red"> <b>is not OK! </b></font><br>''' % (i)
	# 		strs_pk2.append(s_f)
	# 	s_fs = '\n'.join(strs_pk2)

	return '\n'.join(strs_pk) 


def sdian_text(conn):
	'''
	Function doc
	统计 多店 商品价格抓取情况
	@return text

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	sql = '''
		SELECT
		a.dt,
		a.num num1,
		b.num2 num2,
		CASE
			WHEN b.num2 is NULL THEN 'is OK!'
			WHEN a.num > b.num2*0.8 THEN 'is OK!'
			ELSE '<font color="red"> <b>is not OK! </b></font>'
		END stauts
		FROM
		( SELECT count(1) num,dt FROM tb_item_price WHERE dt = '%s' ) a
		INNER JOIN
		( SELECT count(DISTINCT num_iid) num2 FROM tb_ware_list_get where dt='%s' ) b
		''' % (today,yestday)
	datas = select_data(conn,'tb_ware_list_get',sql)
	s_pk = ''
	if datas:
		for data in datas:
			num1 	= str(data[1])
			num2 	= str(data[2])
			stauts 	= str(data[3])	
			s_pk = '''today 需要抓取的商品id数量: %s 实际抓取到的商品id数量: %s ... %s<br> 
			''' % (num2,num1,stauts)

	return s_pk


def scrapy_text(conn):
	'''
	Function doc
	统计 行业爬虫 每天抓取数据量 与 七天抓取的平均数量进行比较
	@return text

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	sql = '''
		SELECT 
		task_type,
		num,
		num7_avg,
		stauts 
		FROM ind_sp_task_exec_info_st WHERE up_date = '%s' ''' % (today) 
	datas = select_data(conn,'ind_sp_task_exec_info_st',sql)
	strs_pks = []

	for data in datas:
		task_type 	= str(data[0])
		num 		= str(data[1])
		num7_avg 	= str(data[2])
		stauts 	    = str(data[3])
		s_pk = ''' %s : yesterday: %s    avg: %s %s <br> ''' % (task_type,num,num7_avg,stauts)
		strs_pks.append(s_pk)

	return '\n'.join(strs_pks)


def send(conn,mail_to_title,mail_to_list,sqls,html_title,help_text=''):
	'''
	Function doc
	执行发送邮件
	@return None

	Parameter doc
	@conn 			: Mysql数据库 连接实例
	@mail_to_title 	: 邮件标题 (str)
	@mail_to_list 	: 邮件接收方账户列表 (list)
	@sqls 			: sql语句列表 (list)
	@html_title 	: html标题 (str)
	@help_text 		: 帮助理解的字符串 (str)
	'''
	get_html = Html()
	mail = ZYMail_z()
	mail.mail_to = mail_to_list
	mail.title = mail_to_title

	if not conn:
		return

	try:
		print 'task build start :',datetime.datetime.now()
		datas = []
		for i in range(len(sqls)):
			item = select_description(conn,sqls[i])#查询数据
			datas.append(item)
		html = get_html.html(datas,html_title,help_text)#对数据进行处理返回html数据
		# print html
		mail.send_email(html,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
		print time.strftime("%Y-%m-%d %H:%M:%S"), 'send email successful !'
	except:
		print time.strftime("%Y-%m-%d %H:%M:%S"), 'send email fail !'
		

def ydhy_email(conn):
	'''
	Function doc
	运动行业 发送邮件
	@return None

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	try:
		res = 'update xtep shops successful !'
		url = ''
		req = urllib2.Request(url)#执行PHP更新
		urllib2.urlopen(req)
	except:
		res = 'update xtep shops fail !'

	mail_to_title = '爬虫日志 %s 特步--运动行业' % (today)
	mail_to_list = TO_EMAILS_LIST_1
	sqls  = ydhy_sql()
	help_text = ydhy_text(conn)
	if 'not' in help_text:
		mail_to_title = '急!!!' + mail_to_title
	title = '''<font color="Green">特步--运动行业 抓取货号和销量的情况</font>'''

	send(conn,mail_to_title,mail_to_list,sqls,title,help_text)


def sdian_email(conn):
	'''
	Function doc
	多店 发送邮件
	@return None

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	mail_to_title = '爬虫日志 %s %s' % (today,opts.key_type)
	mail_to_list = TO_EMAILS_LIST_1
	sqls  		= sdian_sql()
	title 		= '''<font color="Green">%s--商品id抓取成功的数量</font>''' % opts.key_type
	help_text 	= sdian_text(conn)
	
	send(conn,mail_to_title,mail_to_list,sqls,title,help_text)


def xtep_shops_tb_email(conn):
	'''
	Function doc
	淘宝多店 发送邮件
	@return None

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	try:
		res = 'update xtep shops successful !'
		url = ""
		req = urllib2.Request(url)#php_url更新数据
		urllib2.urlopen(req)
	except:
		res = 'update xtep shops fail !'

	mail_to_title = '爬虫日志 %s 特步多店淘宝店' % (today)
	mail_to_list = TO_EMAILS_LIST_3
	sqls  = xtep_shops_tb_sql()
	title = '''<font color="Green">特步多店淘宝店--商品id爬虫的抓取情况</font>'''
	help_text = xtep_shops_tb_text(conn)

	send(conn,mail_to_title,mail_to_list,sqls,title,help_text)


def scrapy_mail(conn):
	'''
	Function doc
	行业爬虫 发送邮件
	@return None

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	mail_to_title = '爬虫日志 %s 行业' % (today)
	mail_to_list = TO_EMAILS_LIST_2
	sqls  = scrapy_sql()
	title = '''<font color="Green">行业--爬虫系统数据统计</font>'''
	help_text = scrapy_text(conn)

	send(conn,mail_to_title,mail_to_list,sqls,title,help_text)


def xtep_email(conn,key_type):
	'''
	Function doc
	全渠道 特步 发送邮件
	@return None

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	table = 'keywords_search_info'
	mail_to_title = '爬虫日志 %s 特步-全渠道爬虫' % (today)
	mail_to_list = TO_EMAILS_LIST_2
	sqls  = qqd_sql(table)
	title = '''<font color="Green">特步-全渠道爬虫系统数据统计</font>'''
	help_text = keywords_search_info_text(conn,table)
	help_text += '<br>'
	help_text += shops_sale_info_stat_text(conn,key_type)
	help_text += '<br><font color="Green"><b>商品货号抓取失败统计</b></font><br>'
	help_text += lost_itemno_text(conn,table)

	send(conn,mail_to_title,mail_to_list,sqls,title,help_text)


def mg_email(conn,key_type):
	'''
	Function doc
	全渠道 晨光 发送邮件
	@return None

	Parameter doc
	@conn : Mysql数据库 连接实例
	'''
	table = 'keywords_search_info'
	mail_to_title = '爬虫日志 %s 晨光-全渠道爬虫' % (today)
	mail_to_list = TO_EMAILS_LIST_2
	sqls  = qqd_sql(table)
	title = '''<font color="Green">晨光-全渠道爬虫系统数据统计</font>'''
	help_text = keywords_search_info_text(conn,table)
	help_text += '<br>'
	help_text += shops_sale_info_stat_text(conn,key_type)
	help_text += '<br><font color="Green"><b>商品货号抓取失败统计</b></font><br>'
	help_text += lost_itemno_text(conn,table)

	send(conn,mail_to_title,mail_to_list,sqls,title,help_text)


def main():
	'''
	Function doc
	执行发邮件
	'''

	print time.strftime("%Y-%m-%d %H:%M:%S"), '开始统计数据....'
	conn = get_conn(DBS,opts.key_type)

	if not conn:
		return
		
	if opts.key_type == 'ydhy' and opts.func == 'xtep_execl_email':
		xtep_execl_email()
	elif opts.key_type == 'ydhy':
		ydhy_email(conn)
	elif opts.key_type and opts.func == 'sdian_email':
		sdian_email(conn)
	elif opts.key_type == 'xtep_shops_tb':
		xtep_shops_tb_email(conn)
	elif opts.key_type == 'scrapy':
		scrapy_mail(conn)
	elif opts.key_type == 'xtep':
		xtep_email(conn,opts.key_type)
	elif opts.key_type == 'mg':
		mg_email(conn,opts.key_type)
	else:
		print 'Not find the email haha !!!'

	conn.close()
	

if __name__ == '__main__': 
	main()

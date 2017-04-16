#coding:utf8
import sys
import os
import time
import datetime
import MySQLdb
from optparse import OptionParser
path1 = (os.getcwd())
if os.name != 'nt':
	path1 = path1.split('/Scrapy_crawlers')[0] + '/Scrapy_crawlers/Shop_site_crawler'
else:
	path1 = path1.split('\Scrapy_crawlers')[0] + '\Scrapy_crawlers\Shop_site_crawler'
sys.path.append(path1)
from settings import DBS
from zsl_spider_lib import db_commit
from zsl_spider_lib import get_conn
from zsl_spider_lib import select_data
from zsl_spider_lib import insert_ignore_dicts
from zsl_spider_lib import get_partition_info
from zsl_spider_lib import del_partition
from zsl_spider_lib import get_to_days
from zsl_spider_lib import time_differ

today = time.strftime("%Y-%m-%d")
up_time = time.strftime("%Y-%m-%d %H:%M:%S")
yestday = time.strftime("%Y-%m-%d",time.localtime((int(time.time())-3600*24)))
ys_9_day = time.strftime("%Y-%m-%d",time.localtime((int(time.time())-3600*24*9)))


def parse_opts():
	'''
	Function doc
	定义文件接收参数
	'''
	parser = OptionParser(usage="%prog [options] [ [target] | -l | -L <target> ]",description="Deploy Scrapy project to Scrapyd server")
	parser.add_option("-T", "--dt", help="the elt datetime like 2014-06-06")
	parser.add_option("-k", "--key_type", default='xtep',  help=" keyword type")
	parser.add_option("-b", "--table", default='keywords_search_info',  help=" item_table")
	parser.add_option("-F", "--func", default = '',help=" functions")
	return parser.parse_args()


def insert_spider_job_stat(conn):
	'''
	Function doc
	统计10天内爬虫任务每轮用时,抓取的数据量,和每轮每次执行时间的平均值,最大值,最小值
	insert igore 插入数据库表 spider_job_stat
	Parameter doc
	@conn : Mysql 数据库连接实例
	'''
	start = time.time()
	pre_30day = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime((int(time.time())-3600*24*10)))
	job_list = [
		'shop',
		'search',
		'bitem',
		'citem'
		]

	for job in job_list:
		sql = '''
			SELECT 
			task_type,
			count(1),
			min(update_time),
			max(end_time),
			add_time
			FROM spider_jobs WHERE task_type = '%s' AND add_time > '%s' GROUP BY add_time
			''' % (job,pre_30day)
		print sql
		data = select_data(conn,'spider_jobs',sql)
		items = []

		if len(data) > 1:
			for d in data[:-1]:
				item = {}
				item['task_type'] 		= str(d[0])
				item['task_count']	 	= str(d[1])
				item['start_time'] 		= str(d[2])
				item['end_time'] 		= str(d[3])
				item['start_date'] 		= str(d[2]).split(' ')[0]
				item['end_date'] 		= str(d[3]).split(' ')[0]
				item['add_time'] 		= str(d[4])
				job_time = time_differ(item['end_time'],item['start_time'])
				item['job_time'] = round(job_time.total_seconds()/60,2)
				if int(item['task_count']) > 50:
					sql = get_spider_1_job_time_sql(item['start_time'],item['end_time'],item['task_type'])
					data1 = select_data(conn,'spider_jobs',sql)

					item['avg_1_job_time'] 		= str(data1[0][0])
					item['max_1_job_time']	 	= str(data1[0][1])
					item['min_1_job_time'] 		= str(data1[0][2])
					sql = get_spider_grab_num_sql(item['start_time'],item['end_time'],item['start_date'],item['end_date'],item['task_type'])
					data = select_data(conn,item['task_type'],sql)
					item['num'] 		= str(data[0][0])
				elif int(item['task_count']) < 50:#bitem有几个特殊任务运行时间很短
					item['avg_1_job_time'] 		= 0
					item['max_1_job_time']	 	= 0
					item['min_1_job_time'] 		= 0
					sql = get_spider_grab_num_sql(item['start_time'],item['end_time'],item['start_date'],item['end_date'],item['task_type'])
					data = select_data(conn,item['task_type'],sql)
					item['num'] 		= str(data[0][0])

				items.append(item)
			insert_ignore_dicts(items,'spider_job_stat',conn)


def get_spider_1_job_time_sql(start_time,end_time,spider):
	'''
	Function doc
	根据每轮任务时间统计出每轮任务中每次任务运行的
	1.平均用时,2.最大用时,3.最小用时 
	Parameter doc
	@start_time : 每轮每次任务开始时间
	@end_time : 每轮每次任务结束时间
	@spider : 爬虫类型
	'''
	sql = '''
		SELECT 
		round(avg(job_time),2) avg_1_job_time,
		max(job_time) max_1_job_time, 
		min(job_time) min_1_job_time
		FROM `spider_jobs` 
		WHERE update_time >='%s' and end_time <= '%s' and task_type = '%s' ;
		''' % (start_time,end_time,spider)
	return sql


def get_spider_grab_num_sql(start_time, end_time, start_dt, end_dt, spider):
	'''
	Function doc
	btiem,citem根据每轮任务时间统计出每轮任务抓取的数据量
	Parameter doc
	@start_time : 每轮每次任务开始时间
	@end_time : 每轮每次任务结束时间
	@start_dt : 开始日期
	@end_dt : 结束日期
	@spider : 爬虫类型
	'''
	d = datetime.datetime.strptime(end_dt,'%Y-%m-%d')
	diff =datetime.timedelta(days=1)
	end_dt = (d + diff).strftime("%Y-%m-%d")
	if spider in ['bitem','citem']:
		spider_type = " t.type = 'tmall' " if spider == 'bitem' else " t.type != 'tmall' "
		sql = '''
			SELECT
				count(1) num
			FROM
				item i
			JOIN task_info t ON i.shopid = t.shop_id AND %s
			WHERE
				i.dt >= '%s' and i.dt < '%s'  AND i.updated >= '%s' AND i.updated <= '%s'
		''' % (spider_type,start_dt,end_dt,start_time,end_time)
	elif spider == 'shop':
		sql = '''
			SELECT count(1) num FROM shop 
			WHERE dt >= '%s' and dt < '%s'  AND updated >= '%s' AND updated <= '%s'
		'''% (start_dt,end_dt,start_time,end_time)
	elif spider == 'search':
		sql = '''
			SELECT count(1) num FROM search 
			WHERE dt >= '%s' and dt < '%s'  AND updated >= '%s' AND updated <= '%s'
		'''% (start_dt,end_dt,start_time,end_time)
	
	return sql


def truncate_ods_shop_tmp(conn):
	'''
	Function doc
	清空中间表 ods_shop_tmp
	Parameter doc
	@conn Mysql 数据库连接实例
	'''
	sql = " TRUNCATE TABLE ods_shop_tmp " 
	print sql
	db_commit(conn,'ods_shop_tmp',sql,1)


def get_dis_shop_time(conn):
	'''
	Function doc
	获取需要去重的时间
	Parameter doc
	@conn Mysql 数据库连接实例
	return list
	'''
	sql = '''
	SELECT
		start_time,
		end_time,
		start_date,
		end_date,
		task_type,
		add_time
		FROM spider_job_stat WHERE stauts = 0 AND task_type = 'shop'
		'''
	data = select_data(conn,'spider_job_stat',sql)
	items = []
	
	for d in data:
		item = {}
		item['start_time'] 		= str(d[0])
		item['end_time']	 	= str(d[1])
		item['start_date'] 		= str(d[2])
		item['end_date'] 		= str(d[3])
		item['task_type'] 		= str(d[4])
		item['add_time'] 		= str(d[5])
		items.append(item)
	return items


def insert_ods_shop_tmp(conn,times):
	'''
	Function doc
	把shop表不重复数据插入临时表
	Parameter doc
	@conn Mysql 数据库连接实例
	@times dict 条件字典
	'''
	sql = 	'''
		INSERT IGNORE INTO ods_shop_tmp 
		SELECT *  FROM  shop WHERE updated >= '%s' AND updated <='%s' 
		AND dt >= '%s' AND dt <= '%s' 
		''' % (times['start_time'],times['end_time'],times['start_date'],times['end_date'])
	print sql
	db_commit(conn,'ods_shop_tmp',sql,1) #将每轮不重复的插入临时表,设置shop_id为主键了


def insert_dis_shop(conn):
	'''
	Function doc
	把临时表的数据插入 dis_shop表
	Parameter doc
	@conn Mysql 数据库连接实例
	'''
	sql = ''' INSERT IGNORE INTO dis_shop
				SELECT * FROM dis_shop_tmp '''
	print sql
	db_commit(conn,'dis_shop',sql,1) 


def update_spider_job_stat(conn,times):
	'''
	Function doc
	更新任务表 spider_job_stat 任务的状态
	Parameter doc
	@conn Mysql 数据库连接实例
	@times dict 更新的条件
	'''
	up_time = time.strftime("%Y-%m-%d %H:%M:%S")
	sql = '''
	UPDATE spider_job_stat SET stauts = 4,up_date = '%s',up_time = '%s'
	WHERE add_time = '%s' AND task_type = '%s'
	''' % (today,up_time,times['add_time'],times['task_type'])
	db_commit(conn,'spider_job_stat',sql,1) 


def del_shop_partition(conn,table,dt):
	'''
	Function doc
	删除shop表小于指定日期2天的分区
	Parameter doc
	@conn Mysql 数据库连接实例
	@table 表名
	@dt dict 日期字典
	'''
	datas 			= get_partition_info(conn,table)#获取分区信息
	start_to_days 	= get_to_days(dt['start_date'])#获取日期的to_days
	print dt['start_date']
	print start_to_days
	end_to_days 	= get_to_days(dt['end_date'])#获取日期的to_days
	print dt['end_date']
	print end_to_days
	for pn,pd in datas:
		#传进来的日期获得的to_days是当天,而分区的值是用明天的值LESS THEN (明天),所以to_days需要+1
		#才能锁定当天的分区
		if str(pd) != 'MAXVALUE' and (int(pd) >= start_to_days+1 and int(pd) < end_to_days+1):
			del_partition(conn,table,pn)#删除分区


def sql_citem_statistics():
	'''
	Function doc
	sql 含义:查询昨天citem爬虫抓取的数据量,使用的关键词数量,和
	七天抓取的平均数量并判断数据是否正常
	'''
	sql_citem = ''' 
	SELECT
	b.num_dis key_word,
	b.num,
	round(c.num7_avg,2) num7_avg,
	CASE 
		WHEN c.num7_avg is NULL THEN 'is OK!'
		WHEN b.num > 0.8*c.num7_avg THEN 'is OK!'
		ELSE '<font color="red"> <b>is not OK! </b></font>'
	END stauts
	FROM
	( SELECT  count(1) num, count(DISTINCT i.shopid) num_dis from item i  JOIN task_info t on  i.shopid=t.shop_id and t.type!='tmall' where  i.dt = '%s' ) b
	INNER JOIN
	(SELECT avg(a.num7) num7_avg FROM ( SELECT  count(1) num7 from item i  LEFT JOIN task_info t on i.shopid=t.shop_id  where t.type!='tmall' and i.dt < '%s' and i.dt > '%s'  GROUP BY i.dt ) a ) c ''' %(yestday,yestday,ys_9_day)
	return sql_citem


def sql_bitem_statistics():
	'''
	Function doc
	sql 含义:查询昨天bitem爬虫抓取的数据量,使用的关键词数量,和
	七天抓取的平均数量并判断数据是否正常
	'''
	sql_bitem = ''' 
	SELECT
	b.num_dis key_word,
	b.num,
	round(c.num7_avg,2) num7_avg,
	CASE 
		WHEN c.num7_avg is NULL THEN 'is OK!'
		WHEN b.num > 0.8*c.num7_avg THEN 'is OK!'
		ELSE '<font color="red"> <b>is not OK! </b></font>'
	END stauts
	FROM
	( SELECT  count(1) num, count(DISTINCT i.shopid) num_dis from item i  JOIN task_info t on  i.shopid=t.shop_id AND t.type='tmall' where i.dt = '%s'  ) b
	INNER JOIN
	( SELECT avg(a.num7) num7_avg FROM ( SELECT  count(1) num7 from item i  LEFT JOIN task_info t on i.shopid=t.shop_id  where t.type='tmall' and i.dt < '%s' and i.dt > '%s'  GROUP BY i.dt ) a ) c ''' %(yestday,yestday,ys_9_day)
	return sql_bitem


def sql_search_statistics():
	'''
	Function doc
	sql 含义:查询昨天search爬虫抓取的数据量,使用的关键词数量,和
	七天抓取的平均数量并判断数据是否正常
	'''
	sql_search = '''
	SELECT
	b.key_word,
	b.num,
	round(c.num7_avg,2) num7_avg,
	CASE	
		WHEN c.num7_avg is NULL THEN 'is OK!'
		WHEN b.num > 0.8*c.num7_avg THEN 'is OK!'
		ELSE '<font color="red"> <b>is not OK! </b></font>'
	END stauts
	FROM
	( SELECT count(distinct keyword) key_word, count(1) num FROM search WHERE dt = '%s' ) b
	INNER JOIN
	( SELECT avg(a.num) num7_avg FROM (SELECT count(1) num,dt FROM search WHERE dt > '%s' AND dt < '%s' GROUP BY dt) a ) c 
	''' % (yestday,ys_9_day,yestday)
	return sql_search


def sql_shop_statistics():
	'''
	Function doc
	sql 含义:查询昨天shop爬虫抓到不重复的店铺数量,抓取的数据量,使用的关键词数量,和
	七天抓取的平均数量并判断数据是否正常
	'''
	sql_shop = '''
	SELECT
	b.shop_id,
	b.key_word,
	b.num,
	round(c.num7_avg,2) num7_avg,
	CASE	
		WHEN c.num7_avg is NULL THEN 'is OK!'
		WHEN b.num > 0.8*c.num7_avg THEN 'is OK!'
		ELSE '<font color="red"> <b>is not OK! </b></font>'
	END stauts
	FROM
	( SELECT count(distinct shop_id) shop_id, count(distinct keyword) key_word, count(1) num FROM shop WHERE dt = '%s' ) b
	INNER JOIN
	( SELECT avg(a.num) num7_avg FROM (SELECT count(1) num,dt FROM shop WHERE dt > '%s' AND dt < '%s' GROUP BY dt) a ) c 
	''' % (yestday,ys_9_day,yestday)
	return sql_shop


def sql_sp_jobs_statistics():
	'''
	Function doc
	统计行业爬虫的运行时间
	'''
	sql = '''
		SELECT
		c.task_type,
		b.num task_success,
		d.num task_fail,
		count(c.task_type) task_total,
		sum(CASE WHEN round(TIMESTAMPDIFF(SECOND,c.update_time,c.end_time) / 60,2) > 2*b.avg_time THEN 1 ELSE 0 END) task_long,
		sum(CASE WHEN round(TIMESTAMPDIFF(SECOND,c.update_time,c.end_time) / 60,2) < 0.25*b.avg_time THEN 1 ELSE 0 END) task_short,
		b.avg_time,
		b.max_time,
		b.min_time
		FROM spider_jobs c 
		LEFT JOIN 
		( SELECT  count(a.task_type) num,a.dt, a.task_type, max(a.job_time) max_time, min(a.job_time) min_time, round(avg(a.job_time),2) avg_time FROM ( SELECT dt, task_type, round(TIMESTAMPDIFF(SECOND,update_time,end_time) / 60,2) as job_time FROM spider_jobs WHERE `stauts` = '2'  AND update_time >= '%s 00:00:00' AND end_time <= '%s 23:59:59' ) a GROUP BY a.task_type ) b
		ON c.task_type = b.task_type
		LEFT JOIN 
		( SELECT count(1) num,task_type FROM spider_jobs WHERE `stauts` = '3'  AND update_time >= '%s 00:00:00' AND end_time <= '%s 23:59:59' GROUP BY task_type ) d
		ON c.task_type = d.task_type
		WHERE c.`stauts` in ('2','3')  AND c.update_time >= '%s 00:00:00' AND c.end_time <= '%s 23:59:59' GROUP BY c.task_type
		''' % (yestday,yestday,yestday,yestday,yestday,yestday)
	return sql


def ind_sp_task_exec_info_st(conn):
	'''
	Function doc
	统计爬虫任务执行的所有情况插入ind_sp_task_exec_info_st表
	Parameter doc
	@conn Mysql 数据库连接实例
	'''
	sql_citem 	= sql_citem_statistics()
	sql_bitem 	= sql_bitem_statistics()
	sql_search 	= sql_search_statistics()
	sql_shop 	= sql_shop_statistics()
	sql_sp_jobs = sql_sp_jobs_statistics()
	up_time = time.strftime('%Y-%m-%d %H:%M:%S')
	up_date = time.strftime('%Y-%m-%d')

	datas = select_data(conn,'spider_jobs',sql_sp_jobs) #统计行业爬虫任务执行情况
	print sql_sp_jobs
	items = []
	for data in datas:#将每只爬虫的结果保存到items
		item = {}
		item['up_time'] 		= up_time
		item['up_date'] 		= up_date
		item['task_type'] 		= str(data[0])
		item['task_success'] 	= str(data[1])
		item['task_fail'] 		= str(data[2])
		item['task_total'] 		= str(data[3])
		item['task_long'] 		= str(data[4])
		item['task_short'] 		= str(data[5])
		item['avg_time'] 		= str(data[6])
		item['max_time'] 		= str(data[7])
		item['min_time'] 		= str(data[8])
		items.append(item)
	for item in items:#遍历结果
		if item['task_type'] == 'citem': #查询的结果整合到爬虫任务信息中
			datas = select_data(conn,'citem',sql_citem)
			print sql_citem
			if datas:
				item['shop_id']     = 0
				item['key_word'] 	= str(datas[0][0])
				item['num'] 		= str(datas[0][1])
				item['num7_avg'] 	= str(datas[0][2])
				item['stauts'] 		= str(datas[0][3])
		elif item['task_type'] == 'bitem':#查询的结果整合到爬虫任务信息中
			datas = select_data(conn,'bitem',sql_bitem)
			print sql_bitem
			if datas:
				item['shop_id']     = 0
				item['key_word'] 	= str(datas[0][0])
				item['num'] 		= str(datas[0][1])
				item['num7_avg'] 	= str(datas[0][2])
				item['stauts'] 		= str(datas[0][3])
		elif item['task_type'] == 'shop':#查询的结果整合到爬虫任务信息中
			datas = select_data(conn,'shop',sql_shop)
			print sql_shop
			if datas:
				item['shop_id'] 	= str(datas[0][0])
				item['key_word'] 	= str(datas[0][1])
				item['num'] 		= str(datas[0][2])
				item['num7_avg'] 	= str(datas[0][3])
				item['stauts'] 		= str(datas[0][4])
		elif item['task_type'] == 'search':#查询的结果整合到爬虫任务信息中
			datas = select_data(conn,'search',sql_search)
			print sql_search
			if datas:
				item['shop_id']     = 0
				item['key_word'] 	= str(datas[0][0])
				item['num'] 		= str(datas[0][1])
				item['num7_avg'] 	= str(datas[0][2])
				item['stauts'] 		= str(datas[0][3]) 

	if items:
		insert_ignore_dicts(items,'ind_sp_task_exec_info_st',conn)
	else:
		print 'not items!'


def shop_dis_data_del(conn):
	'''
	Function doc
	shop 表数据去重
	1.insert_spider_job_stat(conn) 获取shop爬虫每轮的任务时间(也是用于去重的依据)存入表中
	2.get_dis_shop_time(conn) 读取shop表需要去重的时间
	3.insert_ods_shop_tmp(conn,ti),insert_dis_shop(conn)转移shop表不重复的数据
	4.update_spider_job_stat(conn,ti)任务统计表状态
	5.del_shop_partition(conn,'shop',ti) 删除shop表的分区
	Parameter doc
	@conn Mysql 数据库连接实例
	'''
	print 'start insert_spider_job_stat ...\n'
	insert_spider_job_stat(conn) #spider_job_stat 表中插入shop爬虫10天需要去重的执行时间
	print 'end insert_spider_job_stat ...\n'
	time.sleep(3)
	print 'start truncate_ods_shop_tmp ...\n'
	truncate_ods_shop_tmp(conn)#清空shop表数据的临时中间表
	print 'end truncate_ods_shop_tmp ...\n'
	time.sleep(3)
	print 'start get_dis_shop_time ...\n'
	times = get_dis_shop_time(conn) #获取需要去重的时间
	print 'end get_dis_shop_time ...\n'

	if not times:
		print 'not shop data need delete distinct!'
		return

	print 'start insert_ods_shop_tmp,insert_dis_shop,truncate_ods_shop_tmp ...\n'
	for ti in times:
		insert_ods_shop_tmp(conn,ti) #把shop表不重复数据插入临时表
		time.sleep(3)
		
		insert_dis_shop(conn)#把临时表的数据插入 dis_shop表
		time.sleep(3)
		try:
			truncate_ods_shop_tmp(conn)#清空中间表
			time.sleep(3)
		except:
			print 'truncate_ods_shop_tmp fail return!'
			return
		print 'start update_spider_job_stat...\n'
		update_spider_job_stat(conn,ti)#更新任务表 spider_job_stat 任务的状态
		print 'end update_spider_job_stat...\n'
		print 'start del_shop_partition...\n'
		del_shop_partition(conn,'shop',ti)#删除shop表小于指定日期一天的分区
		print 'end del_shop_partition...\n'
	print 'end insert_ods_shop_tmp,insert_dis_shop,truncate_ods_shop_tmp ...\n'


def replace_into_shopids(conn):
	'''
	Function doc
	更新shopids表
	Parameter doc
	@conn Mysql数据库连接实例
	'''
	sql = ''' 
		REPLACE into shopids(shop_id,shop_name,sellerid,avg_totalsold,avg_procnt,type,dt) 
		SELECT shop_id, shop_name, sellerid,
		avg(totalsold) as avg_totalsold, avg(procnt) as avg_procnt,level as type , dt
		FROM ods_shop where dt>='%s' GROUP BY shop_id
		''' % (yestday)
	print sql
	db_commit(conn,'shopids',sql,1) 


def main():
	'''
	Function doc
	执行etl脚本
	'''
	opts, args = parse_opts()
	conn = get_conn(DBS,'scrapy')
	if not conn:
		return
	if opts.func == 'shop_dis_data_del':
		print 'start shop dis data delete...\n'
		shop_dis_data_del(conn)
		print 'end shop dis data delete...\n'
	elif opts.func == 'replace_into_shopids':
		replace_into_shopids(conn)#更新shopids表
	elif opts.func == 'ind_sp_task_exec_info_st':
		ind_sp_task_exec_info_st(conn)#统计爬虫任务执行情况插入ind_sp_task_exec_info_st表
	conn.close()
	

if __name__ == '__main__':
	main()

#coding:utf8 
import time
import os,sys
import datetime
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf-8')
path1 = (os.getcwd())
if os.name != 'nt':
    path1 = path1.split('/Scrapy_crawlers')[0] + '/Scrapy_crawlers/Shop_site_crawler'
else:
    path1 = path1.split('\Scrapy_crawlers')[0] + '\Scrapy_crawlers\Shop_site_crawler'
sys.path.append(path1)
from settings import DBS
from zsl_spider_lib import get_conn
from zsl_spider_lib import db_commit
from zsl_spider_lib import get_select_partition_sql
from zsl_spider_lib import get_next_mon_partition_sql
from zsl_spider_lib import get_to_days
from zsl_spider_lib import select_data
from zsl_spider_lib import get_partition_info
from zsl_spider_lib import del_partition
from optparse import OptionParser


def parse_opts():
	'''
    Function doc
    定义文件接收参数的方法
    '''
	parser = OptionParser(usage="%prog [options] [ [target] | -l | -L <target> ]",description="Deploy Scrapy project to Scrapyd server")
	parser.add_option("-T", "--dt", help="the elt datetime like 2014-06")#-T生成下一个月的分区
	parser.add_option("-D", "--diff_days", help=" days difference")
	#-D 10 删除当前日期前10天的分区
	#-D 2017-02-11 删除2017-02-11的分区
	#-D all 删除所有分区(未启用)
	parser.add_option("-k", "--key_type", default='',  help=" sever type")
	parser.add_option("-b", "--table", default='',  help=" item_table")
	parser.add_option("-e", "--execute", default = '',help=" execute_partition")
	parser.add_option("-m", "--max_pn", default = '',help=" max_partition_name")
	parser.add_option("-v", "--max_pv", default = 'MAXVALUE',help=" max_partition_value")
	return parser.parse_args()

def get_next_mon_partition(conn,table,max_pn,max_pv,the_mon):
	'''
    Function doc
    操作数据库生成下个月分区
    Parameter doc
    @conn Mysql数据库连接实例
    @table 表名
    @max_pn 将要被分区的大分区
    @max_pv 大分区的依据值
    @the_mon 年月如:2016-05 (将生成2016年6月份的分区)
    '''
	sql = get_next_mon_partition_sql(table,max_pn,max_pv,the_mon) 
	print sql
	db_commit(conn,table,sql,1)

def main():
	'''
    Function doc
    对数据库表进行操作
    支持 add,delete,select
    '''
	opts,args = parse_opts()
	if not opts.key_type:
		raise ValueError(" not 'db_name' return! like ==> -k db_name ")
	if not opts.table:
		raise ValueError(" not 'table_name' return! like ==> -b table_name ")
	if not opts.execute:
		raise ValueError(" If you want execute db! like ==> -e select,-e delete,-e add ")

	db 		= opts.key_type #数据库
	table 	= opts.table #表名
	execute = opts.execute #操作类型
	conn 	= get_conn(DBS,db)

	if not conn:
		return
	print 'task build start :',datetime.datetime.now()

	if execute == 'add':#生成下个月分区 或者生存指定月份的下月分区
		if not opts.max_pn:
			raise ValueError(" not the max partition name return! like ==> -m p_max ")
		the_mon = opts.dt if opts.dt else time.strftime("%Y-%m")
		get_next_mon_partition(conn,table,opts.max_pn,opts.max_pv,the_mon)#生成下个月分区
		time.sleep(3)
	
	if execute in ['select','delete']:
		datas = get_partition_info(conn,table)#查询分区情况

	if execute == 'delete':
		to_days 	= get_to_days(time.strftime("%Y-%m-%d"))
		diff_days 	= 20

		if opts.diff_days and opts.diff_days != 'all' and '-' not in opts.diff_days :
			diff_days = int(opts.diff_days)

		if not datas and len(datas) <= 0:
			print '--get partition fail!'
			return
		
		if opts.diff_days == 'all': #删除所有分区
			for pn,pd in datas:
				if str(pd) != 'MAXVALUE':
					print pn
					# sql = " ALTER TABLE %s DROP PARTITION %s " % (table,str(pn))
					# print sql
					# db_commit(conn,table,sql,1)#要删除所有分区开启即可
					# time.sleep(3)
		elif '-' in opts.diff_days:#删除指定日期的分区
			to_days = get_to_days(opts.diff_days)
			for pn,pd in datas:
				if str(pd) != 'MAXVALUE' and int(pd) == to_days+1:
					#传进来的日期获得的to_days是当天,而分区的值是用明天的值LESS THEN (明天),所以to_days需要+1
					#才能锁定当天的分区
					del_partition(conn,table,pn)#删除分区
					time.sleep(3)
		else:#默认删除当天的20天前的分区,也可以根据传入的参数来指定
			for pn,pd in datas:
				if str(pd) != 'MAXVALUE' and int(pd)+diff_days <= to_days+1:
					del_partition(conn,table,pn)#删除分区
					time.sleep(3)
	conn.close()
	print datetime.datetime.now()
	print 'OK'
if __name__ == '__main__':
	main()

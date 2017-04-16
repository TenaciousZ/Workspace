#coding:utf8
import sys
import os
import time
import datetime
import urllib2
import MySQLdb
import subprocess
from optparse import OptionParser
from twisted.python import log
import socket
reload(sys)
sys.setdefaultencoding('utf-8')
path1 = (os.getcwd())
if os.name != 'nt':
    path1 = path1.split('/Scrapy_crawlers')[0] + '/Scrapy_crawlers/Shop_site_crawler'
else:
    path1 = path1.split('\Scrapy_crawlers')[0] + '\Scrapy_crawlers\Shop_site_crawler'
sys.path.append(path1)
from settings import DBS
from zsl_spider_lib import _Insert_Dicts_to_Table,get_conn

yesterday=time.strftime("%Y-%m-%d",time.localtime(time.time()-24*60*60))
today=time.strftime("%Y-%m-%d",time.localtime(time.time()-1*60))

def parse_opts():
    '''
    Function doc
    定义文件接收参数的方法
    '''
    parser = OptionParser(usage="%prog [options] [ [target] | -l | -L <target> ]",
        description="Deploy Scrapy project to Scrapyd server")
    parser.add_option("-t", "--type", default="search", help="the project name in the target")
    parser.add_option("-T", "--dt", help="the datetime like 2014-06-06")
    parser.add_option("-P", "--proportion", default="0-100",help="kw_list proportion")
    parser.add_option("-u", "--update", default=0, type="int", help="the project name in the target")
    parser.add_option("-n", "--num", default=100, type="int", help="list keyword num")
    parser.add_option("-s", "--stauts", default=0, type="int", help="enabled stauts")
    return parser.parse_args()


def keyword(conn, sql, opts, stauts):
    '''
    Function doc
    1.判断任务表中是否还有未完成的任务 getJobCount(conn,opts.type,stauts)
    2.从数据库中读取爬虫的关键词,拼接成关键词组
    3.将关键词组存入任务表中 insertJob(opts.type, paras,conn,stauts)
    Parameter doc
    @conn Mysql数据库连接实例
    @sql sql语句
    @opts 文件接收到的参数
    @stauts 任务的类型 如:我把特步的关键词 定为 stauts = 9
    return 0 或 1
    '''
    print '%s stauts: %s' % (opts.type,stauts)
    if getJobCount(conn,opts.type,stauts) > 0:#判断任务表中是否还有未完成的任务
        print 'There is also the task is not done !'
        return

    kw = []
    try:
        cur=conn.cursor()
        count=cur.execute(sql)
        log.msg(sql)
        log.msg('there has %s rows record' % count)
        results=cur.fetchall()

        for r in results:
            try:
                s = [urllib2.quote(str(i).encode('GBK')) for i in r]
            except:
                print "error", r
                s = [urllib2.quote(str(i).encode('UTF-8')) for i in r]
            kw.append(':'.join(s))

        conn.commit()
        cur.close()
    except MySQLdb.Error,e:
        log.err("Mysql Error %d: %s" % (e.args[0], e.args[1]))
 
    print '---------total_kw',len(kw)
    if (len(kw) == 0):
        return 0

    j = 0
    avg = len(kw) / opts.num
    paras = []

    for i in range(avg+1):
        para = ",".join(kw[i*opts.num:(i+1)*opts.num])#按opts.num为一组
        if (len(para) != 0 ):
            j = j + 1
            paras.append(para)#关键词列表

    insertJob(opts.type, paras,conn,stauts)
    print j
    print 'task builded :', datetime.datetime.now()
    return 1


def getJobCount(conn, spider, stauts):
    '''
    Function doc
    判断任务表中是否还有未完成的任务 
    Parameter doc
    @conn Mysql数据库连接实例
    @spider 爬虫类型 如:bitem
    @stauts 任务的类型 如:我把特步的关键词 定为 stauts = 9
    return int
    '''
    sql = '''
        SELECT count(1) FROM spider_jobs WHERE stauts=%s AND task_type='%s';
        ''' % (stauts,spider)
    print sql
    cur = conn.cursor()
    cur.execute(sql)
    res = cur.fetchone()
    cur.close()
    return int(res[0])


def insertJob(spider,paras,conn,stauts):
    '''
    Function doc
    将关键词组存入任务表中 insertJob(opts.type, paras,conn,stauts)
    Parameter doc
    @conn Mysql数据库连接实例
    @paras 关键词组列表
    @spider 爬虫类型 如:bitem
    @stauts 任务的类型 如:我把特步的关键词 定为 stauts = 9
    '''
    tasks = []
    dt = time.strftime("%Y-%m-%d")
    #add_time 在循环外面定义,保证了任务生成的时间是一致的,防止一天生成多个任务
    add_time = time.strftime("%Y-%m-%d %H:%M:%S") 
    if os.name != 'nt':
        for i in range(len(paras)):
            para = paras[i].replace('%CD','"%CD"')
            task_info = {}#任务
            cmd = "scrapy crawl %s -a para=\"%s\" " % (spider, para)
            task_info['task_type'] = spider
            task_info['keyword'] = cmd
            task_info['ip'] = socket.gethostbyname(socket.gethostname())
            task_info['add_time'] = add_time
            task_info['dt'] = dt
            task_info['stauts'] = stauts
            tasks.append(task_info)   
    else:
        for i in range(len(paras)):
            para = paras[i].replace('%CD','"%CD"')
            task_info = {}
            cmd = "scrapy crawl %s -a para=\"%s\" " % (spider, para)
            task_info['task_type'] = spider
            task_info['keyword'] = cmd
            task_info['ip'] = socket.gethostbyname(socket.gethostname())
            task_info['add_time'] = add_time
            task_info['dt'] = dt
            task_info['stauts'] = stauts
            tasks.append(task_info)   
            # cmd = "scrapy crawl %s -a para=\"%s\" -o %s.csv >%s.log 2>&1" % (spider, para, spider, spider)
    try:
        _Insert_Dicts_to_Table(tasks,'spider_jobs',spider,conn)
    except:
        print 'insert task to spider_jobs fail'


def main():
    '''
    Function doc
    从关键词表中读取行业爬虫的关键词 拼接成关键词组 将关键词组存入任务表中 
    '''
    opts, args = parse_opts()
    stauts = 0
    print opts.type
    conn = get_conn(DBS,'scrapy')
    print 'task build start :',datetime.datetime.now()
    
    if opts.type == "shop":#读取shop爬虫的关键词
        sql = "SELECT keyword FROM keyword_info where type !='brand' and enabled=1 "
        return keyword(conn, sql, opts,stauts)
    elif opts.type == "search":#读取search爬虫的关键词
        sql = "select keyword from keyword_info WHERE (cate_num in(9,2,5,7,25,16,30) and enabled=1 and type='brand') or (type !='brand' and enabled=1)"
        return keyword(conn, sql, opts,stauts)
    elif opts.type == "bitem":#读取bitem爬虫的关键词
        enabled = 1

        if opts.stauts == 9:#全渠道运动行业
            enabled = 9
            stauts = 9

        sql = '''
            SELECT
            c.shop_id,
            c.sellerid,
            c.avg_procnt_new avg_procnt
            FROM
            ( SELECT a.*, s.avg_procnt avg_procnt_new 
                FROM task_info a 
                JOIN shopids s ON a.shop_id = s.shop_id ) c
            WHERE c.type='tmall' AND c.sellerid is not null AND c.sellerid!=0 and c.enabled='%s' AND c.avg_procnt < 6000
            ''' % (enabled)
        return keyword(conn, sql, opts,stauts)
    elif opts.type == "citem":#读取citem爬虫的关键词
        enabled = 1

        if opts.stauts == 9:#全渠道运动行业
            enabled = 9
            stauts = 9

        sql = '''
            SELECT
            c.shop_id,
            c.sellerid,
            c.avg_procnt_new avg_procnt
            FROM
            ( SELECT a.*, s.avg_procnt avg_procnt_new 
                FROM task_info a 
                JOIN shopids s ON a.shop_id = s.shop_id ) c
            WHERE c.type!='tmall' AND c.sellerid is not null AND c.sellerid!=0 and c.enabled='%s' AND c.avg_procnt < 6000
            ''' % (enabled)
        return keyword(conn, sql, opts,stauts)
    conn.close()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import codecs
from Shop_site_crawler.zsl_spider_lib import unicode_2_utf8
from Shop_site_crawler.zsl_spider_lib import get_i_sql
from Shop_site_crawler.zsl_spider_lib import insert_ignore_dicts_sql
from Shop_site_crawler.zsl_spider_lib import get_conn,db_commit,get_dbpool,mysql_dbpool_exec
from Shop_site_crawler.settings import DBS,SSH_INFO
try:
    from Shop_site_crawler.zsl_spider_lib import SSH_2_remote_db
except:
    print 'import SSH_2_remote_db fail ....'
import time
import sys
import logging
import os,MySQLdb
from twisted.enterprise import adbapi



class JsonWithEncodingJdPipeline(object):
    def __init__(self):
        self.file = codecs.open('data.json', 'a', encoding='utf-8')
        print 'open data.json...............'
    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item
    def spider_closed(self, spider):
        self.file.close()




class MySQLASync_ShopPipeline(object):
    '''
    Class doc
    行业shop爬虫数据存储管道类
    '''
    def __init__(self):
        '''
        Function doc
        类的初始化方法
        '''
        self.dbpool = get_dbpool(DBS,'scrapy')
        self.items = []

    def process_item(self, item, spider):
        '''
        Function doc
        管道类初始化结束后,会调用这个方法
        Parameter doc
        @item 爬虫抓取的数据
        @spider 爬虫的一些信息
        '''
        self.items.append(safeitem(item))

        if len(self.items) > 30:
            sql = insert_ignore_dicts_sql(self.items,'shop')
            if sql:
                self.dbpool.runInteraction(mysql_dbpool_exec,sql)
                self.items = []
        return item

    def close_spider(self, spider):
        '''
        Fucntion doc
        当爬虫关闭的时候执行这个方法
        Parameter doc
        @spider 爬虫的一些信息
        '''
        if len(self.items) > 0:
            sql = insert_ignore_dicts_sql(self.items,'shop')
            if sql:
                self.dbpool.runInteraction(mysql_dbpool_exec,sql)                
        print >>sys.stdout, "OK!"

    # end MySQLASync_ShopPipeline



class MySQLSync_SearchPipeline(object):
    '''
    Class doc
    行业search爬虫数据存储管道类
    '''
    def __init__(self):
        '''
        Function doc
        类的初始化方法
        '''
        self.dbpool = get_dbpool(DBS,'scrapy')
        self.p4p_items = []
        self.items = []

    def process_item(self, item, spider):
        '''
        Function doc
        管道类初始化结束后,会调用这个方法
        Parameter doc
        @item 爬虫抓取的数据
        @spider 爬虫的一些信息
        '''
        try:
            if 'shop_name' in item.keys() and 'p4p' not in item.keys():       
                self.items.append(safeitem(item))
            elif 'p4p' in item.keys() and 'shop_name' not in item.keys():
                self.p4p_items.append(safeitem(item))

            if len(self.items) > 59:
                sql = insert_ignore_dicts_sql(self.items,'search')
                if sql:
                    self.dbpool.runInteraction(mysql_dbpool_exec,sql)
                    self.items = []#还原初始值
            if len(self.p4p_items) > 59:
                sql = insert_ignore_dicts_sql(self.p4p_items,'search_p4p')
                if sql:
                    self.dbpool.runInteraction(mysql_dbpool_exec,sql)
                    self.p4p_items = []#还原初始值
        except MySQLdb.Error,e:
            logging.log(logging.INFO, "MySQL error:" + str(e))

        return item

    def close_spider(self, spider):
        '''
        Fucntion doc
        当爬虫关闭的时候执行这个方法
        Parameter doc
        @spider 爬虫的一些信息
        '''
        if (len(self.items) > 0):
            sql = insert_ignore_dicts_sql(self.items,'search')
            if sql:
                self.dbpool.runInteraction(mysql_dbpool_exec,sql)
        if (len(self.p4p_items) > 0):
            sql = insert_ignore_dicts_sql(self.p4p_items,'search_p4p')
            if sql:
                self.dbpool.runInteraction(mysql_dbpool_exec,sql)
        print >>sys.stdout, "OK!"
        
    # end MySQLSync_SearchPipeline



class MySQLASync_ItemPipeline(object):
    '''
    Class doc
    行业bitem,citem爬虫数据存储管道类
    '''
    def __init__(self):
        '''
        Function doc
        类的初始化方法
        '''
        self.dbpool = get_dbpool(DBS,'scrapy')
        self.items = []

    def process_item(self, item, spider):
        '''
        Function doc
        管道类初始化结束后,会调用这个方法
        Parameter doc
        @item 爬虫抓取的数据
        @spider 爬虫的一些信息
        '''
        self.items.append(safeitem(item))

        if len(self.items) > 30:
            sql = insert_ignore_dicts_sql(self.items,'item')
            if sql:
                self.dbpool.runInteraction(mysql_dbpool_exec,sql)
            self.items = []
        return item

    def close_spider(self, spider):
        '''
        Fucntion doc
        当爬虫关闭的时候执行这个方法
        Parameter doc
        @spider 爬虫的一些信息
        '''
        if len(self.items) > 0:
            sql = insert_ignore_dicts_sql(self.items,'item')
            if sql:
                self.dbpool.runInteraction(mysql_dbpool_exec,sql)
        self.dbpool.close()
        print >>sys.stdout, "OK!"


    # end MySQLASync_ItemPipeline



class MySQLASync_JDItemPipeline(object):
    '''
    Class doc
    行业jditem,jd_cate_item_details,爬虫数据存储数据管道类
    '''
    def __init__(self):
        '''
        Function doc
        类的初始化方法
        '''
        self.conn = get_conn(DBS,'scrapy')

    def process_item(self, item, spider):
        '''
        Function doc
        管道类初始化结束后,会调用这个方法
        Parameter doc
        @item 爬虫抓取的数据
        @spider 爬虫的一些信息
        '''
        self._InsertJDItem(self.conn,item,spider)
        return item

    def close_spider(self, spider):
        '''
        Fucntion doc
        当爬虫关闭的时候执行这个方法
        Parameter doc
        @spider 爬虫的一些信息
        '''
        self.conn.close()
        print >>sys.stdout, "OK!"

    def _InsertJDItem(self,conn, item,spider):
        '''
        Function doc
        将item存入数据库
        Parameter doc
        @conn Mysql数据库连接实例
        @item 数据
        @spider 爬虫的一下相关信息
        '''
        if 'keyword' in item.keys():
            table = 'item_details_info'
            try:
                item = safeitem(item)#将unicode编码的字符转成utf8
            except:
                logging.info("get safeitem is fialed....")
            try:
                insert_sql = get_i_sql(table,item,1)#返回一条插入的sql
                db_commit(conn,table,insert_sql)#插入数据库
            except:
                print 'insert data fail !'
        else:   
            table = 'cate_item_info'
            try:
                item = safeitem(item)#将unicode编码的字符转成utf8
            except:
                logging.info("get safeitem is fialed....")
            try:
                insert_sql = get_i_sql(table,item,1)#返回一条插入的sql
                db_commit(conn,table,insert_sql)#插入数据库
            except:
                print 'insert data fail !'

    # end MySQLASync_JDItemPipeline


'''返回一个可以安全的item'''
def safeitem(item):
    item['updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
    item['dt']  = time.strftime("%Y-%m-%d")
    #将unicode编码字段,转成utf8
    for key in item.keys():
        if isinstance(item[key],(unicode)):
            item[key] = item[key].encode('utf-8', "ignore")
    return item



class Mysql_test_pipelines(object):
    '''
    class doc
    the test
    '''
    def __init__(self):
        try:
            ssh = SSH_2_remote_db()
            ssh.ssh_username = SSH_INFO['ssh_username']
            ssh.ssh_passwd = SSH_INFO['ssh_passwd']
            ssh.ip = SSH_INFO['ip']
            ssh.ssh_port = SSH_INFO['ssh_port']
            ssh.remote_db_address = DBS['scrapy']['MYSQL_HOST']
            ssh.db_user = DBS['scrapy']['MYSQL_USER']
            ssh.db_passwd = DBS['scrapy']['MYSQL_PASSWD']
            ssh.db_name = DBS['scrapy']['MYSQL_DBNAME']
            self.server = ssh.ssh_2_remote_server() #ssh连接服务器实例
            self.server.start()
            self.conn = ssh.ssh_2_db_conn(self.server) #远程数据连接实例
        except:
            self.conn = get_conn(DBS,'scrapy')

    def process_item(self, item, spider):
        self._insert_test_items(self.conn,item,spider)
        return item

    def close_spider(self,spider):
        try:
            self.server.stop()
            self.conn.close()
        except:
            self.conn.close()

    def _insert_test_items(self,conn,item,spider):
        '''
        Function doc
        将item存入数据库
        '''
        table = spider.name
        try:
            item = unicode_2_utf8(item)#将unicode编码的字符转成utf8
        except:
            logging.info("get safeitem is fialed....")
        try:
            insert_sql = get_i_sql(table,item,1)#返回一条插入的sql
            db_commit(conn,table,insert_sql)#插入数据库
        except:
            print 'insert data fail !'

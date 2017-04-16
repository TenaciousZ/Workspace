#-*-coding:utf-8-*-
'''
    @by zsl
    @help for spider
'''
import MySQLdb
import urllib2
import logging
import datetime
import time,random
import os
import re
import chardet
from settings import DBS,SSH_INFO,FROM_EMAIL_DICT,TO_EMAILS_LIST_6
from twisted.enterprise import adbapi
try:
    from xlwt import Workbook 
except:
    pass
try:
    from sshtunnel import SSHTunnelForwarder
except:
    pass
import zipfile


class Mysqldbpool(object):
    '''
    Class doc
    scrapy 框架管道返回mysql连接池实例改变父类dbpool属性
    '''
    def __init__(self, dbpool):
        '''
        Function doc
        管道类父类的初始化属性方法
        '''
        self.dbpool = dbpool
        # self.count = 0#一次插入字段总数
        # self.batch = 60#最大插入字段总数
        # self.items = []#所有字段存入list

    @classmethod
    def from_settings(cls, settings):
        '''
        Function doc
        scrapy框架的一个类方法,当调用管道类的时候会调用这个方法
        并把连接池的实例返回给管道类,管道类接受这个实例参数,
        把实例参数传给父类改变父类的属性
        '''
        settings = settings['DBS']['scrapy'] if (os.getcwd()).find('/home') !=-1 else settings['DBS']['defult_scrapy']  #选择数据库地址
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            # port=3306,
            charset='utf8',
            # cursorclass = MySQLdb.cursors.DictCursor,
            # use_unicode= True,
        )

        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
        return cls(dbpool)

    def _handle_error(self, failure, item, spider):
        """Handle occurred on db interaction."""
        # do nothing, just log
        log.err(failure)

 
def zip_dir(dirname,zipfilename):
    '''
    Function doc
    解压文件或者文件夹
    Parameter doc
    @dirname 需要解压的文件名和路径
    @zipfilename 解压后的文件名和路径
    '''
    filelist = []
    if os.path.isfile(dirname):#file
        filelist.append(dirname)
    else :#dir
        for root, dirs, files in os.walk(dirname):
            for name in files:
                print name
                filelist.append(os.path.join(root, name))
         
    zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
    for tar in filelist:
        arcname = tar[len(dirname):]
        zf.write(tar,arcname)
    zf.close()


def mysql_data_2_execl(fname,data,description,table_name='file'):
    '''
    Function doc
    将mysql 查询出来的数据保存 execl表格
    Parameter doc
    @fname str 文件名
    @data  tuple or list 结果集
    @description tuple or list 字段描述
    '''

    file = Workbook(encoding = 'utf-8')
    table = file.add_sheet(table_name)
    try:
        for i,p in enumerate(description):
            if isinstance(p[0],(unicode)):
                p[0] = p[0].encode('utf-8', "ignore")       
            table.write(0,i,p[0]) #第一行写字段名

        for j in range(len(data)):
            for i,p in enumerate(data[j]):
                if isinstance(p,(unicode)):
                    p = p.encode('utf-8', "ignore")
                table.write(j+1,i,str(p))
        file.save(fname)
    except:
        print 'save execl fail...'


def ssh_2_remote_db_sel_data(db_type,sql):
    '''
    Function doc
    通过ssh连接数据库获取字段和结果集
    Parameter doc
    @db_type 数据库类型
    @sql sql语句
    return 字段描述(description),结果集(data)
    '''
    try:
        ssh = SSH_2_remote_db()
        ssh.ssh_username = SSH_INFO['ssh_username']
        ssh.ssh_passwd = SSH_INFO['ssh_passwd']
        ssh.ip = SSH_INFO['ip']
        ssh.ssh_port = SSH_INFO['ssh_port']
        ssh.remote_db_address = DBS[db_type]['MYSQL_HOST']
        ssh.db_user = DBS[db_type]['MYSQL_USER']
        ssh.db_passwd = DBS[db_type]['MYSQL_PASSWD']
        ssh.db_name = DBS[db_type]['MYSQL_DBNAME']
        server = ssh.ssh_2_remote_server() #ssh连接服务器实例
        server.start()
        conn = ssh.ssh_2_db_conn(server) #远程数据连接实例
    except:
        conn = get_conn(DBS,db_type)
    
    try:
        datas = select_description(conn,sql)
        data = datas['data']
        description = datas['description']
    except:
        print 'ssh get data fail'
    
    try:
        server.stop() #关闭ssh连接
        conn.close()
    except:
        conn.close()
        
    return data,description


def fmt_text(str, level=2):
    '''
    Function doc
    替换str中的特殊字符
    return str
    '''
    if not str:
        return ''

    str = str.strip().replace(',', '%2C').replace('\n', ' ')
    if level == 2:
        str = re.sub(r'/$', '', re.sub(r'&#\d+;?', '', str.replace('&amp;', '&').replace('&amp;', '&')).strip())
    return str


def pick_str(str, bs, es='"'):
    '''
    Function doc
    切割字符串
    Parameter doc
    @str : 字符串
    @bs : 从bs开始切割
    @es : 切割到es结束
    return str
    '''
    bs_len = len(bs)    # bs 的字符串长度
    a = str.find(bs)    # str 找到 bs 的位置
    
    if a != -1:
        b = str.find(es, a+bs_len)  #从 str 的 bs 之后开始查找 es
        if b != -1: #b 是找到es 的位置
            return str[a+bs_len:b].strip()  #str切片取 bs之后 到es 之间的字符串
    return ''


def send_email2(mail_to_title,mail_to_list,html_text=''):
    '''
    Function doc
    发送邮件方法
    Parameter doc
    @mail_to_title 发送的标题
    @mail_to_list  发送接收者的邮件列表
    @html_text  html文本信息
    '''
    mail = ZYMail_z()
    mail.mail_to = mail_to_list
    mail.title = mail_to_title
    # mail.conent_type = 'plain'
    try:
        print 'task build start :',datetime.datetime.now()
        mail.send_email(html_text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
        print time.strftime("%Y-%m-%d %H:%M:%S"), 'send email successful !'
    except:
        print time.strftime("%Y-%m-%d %H:%M:%S"), 'send email fail !'


def send_email_att(mail_to_title,mail_to_list,fname=''):
    '''
    Function doc
    发送带附件邮件方法
    Parameter doc
    @mail_to_title 发送的标题
    @mail_to_list  发送接收者的邮件列表
    @html_text  html文本信息
    '''
    mail = ZYMail_z()
    mail.mail_to = mail_to_list
    mail.title = mail_to_title
    mail.attachment(fname)#构造附件
    mail.conent_type = 'plain'
    help_text = '请查收!'
    try:
        print 'task build start :',datetime.datetime.now()
        mail.send_email(help_text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
        print time.strftime("%Y-%m-%d %H:%M:%S"), 'send email successful !'
    except:
        print time.strftime("%Y-%m-%d %H:%M:%S"), 'send email fail !'


def unicode_2_utf8(item):
    '''
    Function doc
    将unicode编码字段,转成utf8编码
    Parameter doc
    @item : 字典(dict)
    return dict 返回utf8编码的字典
    '''
    for key in item.keys():
        if isinstance(item[key],(unicode)):
            item[key] = item[key].encode('utf-8', "ignore")
    return item


def div_list(ls,n):#等分切割list
    '''
    Function doc
    等分切割list
    Parameter doc
    @ls : 列表(list)
    @n : int 切割次数
    return list 返回切割后的list
    '''
    if not isinstance(ls,list) or not isinstance(n,int):  
        return []  
    ls_len = len(ls)  
    if n<=0 or 0==ls_len:  
        return [ls]  
    if n > ls_len:  
        return [ls]  
    elif n == ls_len:  
        return [[i] for i in ls]
    else:  
        j = ls_len/n  
        k = ls_len%n  
        ### j,j,j,...(前面有n-1个j),j+k  
        #步长j,次数n-1  
        ls_return = []  
        for i in xrange(0,(n-1)*j,j):  
            ls_return.append(ls[i:i+j])  
        #算上末尾的j+k  
        ls_return.append(ls[(n-1)*j:])  
        return ls_return  


def del_partition(conn,table,pn):#删除分区
    '''
    Function doc
    删除分区
    Parameter doc
    @conn : Mysql 数据库连接实例
    @table : 表名
    @pn : 分区名字
    '''
    sql = " ALTER TABLE %s DROP PARTITION %s " % (table,str(pn))
    print sql
    db_commit(conn,table,sql,1)


def get_partition_info(conn,table):
    '''
    Function doc
    获取分区信息
    Parameter doc
    @conn : Mysql 数据库连接实例
    @table : 表名
    return tuple 返回分区名称,分区依据等信息
    '''
    sql = '''  
        SELECT 
        PARTITION_NAME as pn,
        PARTITION_DESCRIPTION as pd
        FROM INFORMATION_SCHEMA.PARTITIONS WHERE TABLE_NAME='%s';
        '''%(table)
    print sql
    datas = select_data(conn,table,sql)
    print 'partitions = ',datas
    return datas


def get_select_partition_sql(table_name):
    '''
    Function doc
    获取查询分区情况信息的sql语句
    Parameter doc
    @table_name : 表名
    return sql
    '''
    select_partition = '''  
        SELECT 
        TABLE_NAME as tbl
        ,PARTITION_NAME as pn
        ,PARTITION_ORDINAL_POSITION as pop
        ,PARTITION_METHOD as pm
        ,PARTITION_EXPRESSION as pe
        ,PARTITION_DESCRIPTION as pd
        ,TABLE_ROWS as t_rows
        ,AVG_ROW_LENGTH as avgrl
        ,DATA_LENGTH as dl
        ,MAX_DATA_LENGTH as mdl
        ,INDEX_LENGTH as il
        ,DATA_FREE as df
        ,CREATE_TIME as ct
        ,UPDATE_TIME as ut
        ,CHECK_TIME as cht
        ,CHECKSUM as ch
        ,PARTITION_COMMENT as pc
        ,NODEGROUP as ng
        ,TABLESPACE_NAME as tsn
        FROM INFORMATION_SCHEMA.PARTITIONS WHERE TABLE_NAME='%s';
    '''%(table_name)
    return select_partition

def get_next_mon_info(year_and_mon = ''):
    '''
    Function doc
    获取下个月的信息
    1.获取年份 : year 如:2017
    2.获取下个月月份 : next_mon 如 01
    3.获取下个月天数 : mon_days 如 31
    4.获取年月信息 : year_and_mon 如 201701
    Parameter doc
    @year_and_mon : 如 2016-12
    return ...
    '''
    import calendar

    if year_and_mon:#有传值的时候'2016-12'
        year = year_and_mon.split('-')[0]
        current_mon = year_and_mon.split('-')[1]
        year = int(year)
        current_mon = int(current_mon)
    elif not year_and_mon:
        year = int(time.strftime('%Y')) #当前年如: 2016
        current_mon = int(time.strftime('%m')) #当前月如: 12
    
    if current_mon == 12:#如果当前月是12那么下个月就是1
        next_mon = 1
        year = year +1
        year_and_mon = str(year) +'0'+ str(next_mon) #获取当年的下个月
    else:
        next_mon = current_mon +1
        if next_mon < 10:#
            year_and_mon = str(year) +'0'+ str(next_mon) #获取当年的下个月
        else:
            year_and_mon = str(year) + str(next_mon) #获取当年的下个月
    week_num,mon_days = calendar.monthrange(year,next_mon)
    return year,next_mon,mon_days,year_and_mon


def get_to_01days(year,mon):
    '''
    Function doc
    计算公元0年到这个月一号的天数是多少
    Parameter doc
    @year : int (example : 2016)
    @mon : int (example : 12)
    return like 736634 返回一串数字
    '''
    to_days_20161101 = 736634
    d1 = datetime.datetime(2016, 11, 01)
    d2 = datetime.datetime(int(year),int(mon),1)
    days = (d2-d1).days#计算出这个月一号与20161101所差的天数
    to_days = to_days_20161101 + days #计算公元0年到这个月一号的天数是多少
    return to_days


def get_to_days(from_days='2015-12-06'):
    '''
    Function doc
    计算公元0年到这个月一号的天数是多少
    Parameter doc
    @from_days str (example : '2016-11-06')
    return like 736639 返回一串数字
    '''
    year,mon,day = from_days.split('-')
    to_days_20161101 = 736634
    d1 = datetime.datetime(2016, 11, 01)
    d2 = datetime.datetime(int(year),int(mon),int(day))
    days = (d2-d1).days#计算出from_days与20161101所差的天数
    to_days = to_days_20161101 + days #计算公元0年到from_days的天数是多少
    return to_days


def get_from_days(to_days = 736639):
    '''
    Function doc
    根据天数计算日期
    Parameter doc
    @to_days int (example : 736639)
    return 日期
    '''
    to_days_20161101 = 736634
    diff_days = to_days - to_days_20161101
    delta_diff_days = datetime.timedelta(days=diff_days)#timedelta 类型的时间差
    d=datetime.datetime.strptime('2016-11-01','%Y-%m-%d')#将字符串转换为日期 string => datetime
    from_day = d + delta_diff_days
    return from_day.strftime('%Y-%m-%d')


def get_one_partition_sql(table_name, old_max_pn='p_max', date=''):
    '''
    Function doc
    获取增加一天分区的sql
    Parameter doc
    @table_name : 表名
    @old_max_pn : 最大分区的名字(old max partition name)
    @date : 日期 默认当天(example : '2016-12-23')
    return sql
    '''
    if not date:
        date = time.strftime("%Y-%m-%d")
    p_num = date.replace('-','')
    partitions = 'PARTITION p%s VALUES LESS THAN (TO_DAYS("%s")+1),'%(p_num,date)
    new_max_partition = 'PARTITION p_max VALUES LESS THAN (MAXVALUE)'

    add_partition_sql = '''ALTER TABLE %s REORGANIZE PARTITION %s INTO (%s %s);
                    '''%(table_name,old_max_pn,partitions,new_max_partition)
    return add_partition_sql


def get_next_mon_partition_sql(table_name, max_pn='p_max',max_pv='MAXVALUE', year_and_mon = ''):
    '''
    Function doc
    获取增加下个月整月的分区的sql
    Parameter doc
    @table_name : 表名
    @max_pn : 最大分区的名字(max partition name)
    @max_pv : 最大分区的时间值(max partition name)
    @year_and_mon : 年份月份 默认为空就是当月(example : '2016-12')
    return sql
    '''
    partitions = ''
    next_mon_info = get_next_mon_info(year_and_mon) #默认参数为空,参数格式 '2016-12'
    year = next_mon_info[0] #下个月的年份
    next_mon = next_mon_info[1] #下个月月份
    mon_days = next_mon_info[2] #下个月天数
    year_and_mon = next_mon_info[3] # 年月的组合字符串
    to_days = get_to_01days(year,next_mon) #获取这个月1号的to_days

    for i in range(1,mon_days+1):
        if i < 10:
            p_num = year_and_mon +'0'+ str(i)
        else:
            p_num = year_and_mon + str(i)
        to_day = to_days + i
        partitions += 'PARTITION p%s VALUES LESS THAN (%s),'%(str(p_num),str(to_day))

    for_max_partition = 'PARTITION %s VALUES LESS THAN (%s)' % (max_pn,max_pv)#从这里分区
    add_partition_sql = '''ALTER TABLE %s REORGANIZE PARTITION %s INTO (%s %s);
                    '''%(table_name,max_pn,partitions,for_max_partition)
    return add_partition_sql


def get_conn(dbs,db_type):
    '''
    Function doc
    创建Mysql 数据库连接实例
    Parameter doc
    @dbs 数据库地址库集合
    @db_type 选择数据库类型
    return conn 数据库连接实例
    '''
    conn = ''
    if not db_type:
        raise KeyError(" not db return ! ")
    if not isinstance(dbs,dict):
        raise TypeError(" '%s' must be 'dict' ! " % (dbs))
    if not isinstance(db_type,str):
        raise TypeError(" '%s' must be 'str' ! " % (db_type))
    if db_type not in dbs.keys() and 'qqd_%s'%db_type not in dbs.keys() and 'defult_%s'%db_type not in dbs.keys():
        raise KeyError(" '%s' not in dbs.keys ! " % (db_type))
    
    if 'qqd_' in db_type or 'defult_' in db_type:
        db_type = db_type.strip('qqd_').strip('defult_')

    if db_type == 'scrapy':
        db = dbs['scrapy'] if os.name != 'nt' else dbs['defult_scrapy']
    else:
        db = dbs['qqd_%s'%db_type] if os.name != 'nt' else dbs['defult_%s'%db_type]
    try:
        conn=MySQLdb.connect(host=db['MYSQL_HOST'],user=db['MYSQL_USER'],passwd=db['MYSQL_PASSWD'],charset='utf8')
        conn.select_db(db['MYSQL_DBNAME'])
    except:
        print "conn mysql fail..."
        return None
    return conn


def get_dbpool(dbs,db_type):
    '''
    Function doc
    创建Mysql 数据库连接池实例
    Parameter doc
    @dbs 数据库地址库集合
    @db_type 选择数据库类型
    return dbpool 数据库连接池实例
    '''
    dbpool = ''
    if not db_type:
        raise KeyError(" not db return ! ")
    if not isinstance(dbs,dict):
        raise TypeError(" '%s' must be 'dict' ! " % (dbs))
    if not isinstance(db_type,str):
        raise TypeError(" '%s' must be 'str' ! " % (db_type))
    if db_type not in dbs.keys() and 'qqd_%s'%db_type not in dbs.keys() and 'defult_%s'%db_type not in dbs.keys():
        raise KeyError(" '%s' not in dbs.keys ! " % (db_type))
    
    if 'qqd_' in db_type or 'defult_' in db_type:
        db_type = db_type.strip('qqd_').strip('defult_')

    if db_type == 'scrapy':
        db = dbs['scrapy'] if os.name != 'nt' else dbs['defult_scrapy']
    else:
        db = dbs['qqd_%s'%db_type] if os.name != 'nt' else dbs['defult_%s'%db_type]
        
    try:
        dbargs = dict(
            host=db['MYSQL_HOST'],
            db=db['MYSQL_DBNAME'],
            user=db['MYSQL_USER'],
            passwd=db['MYSQL_PASSWD'],
            # port=3306,
            charset='utf8',
            # cursorclass = MySQLdb.cursors.DictCursor,
            # use_unicode= True,
        )

        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
    except:
        print " mysql dbpool fail..."
        return None
    return dbpool


def mysql_dbpool_exec(conn,sql):
        '''
        Function doc
        连接池调用方法
        @conn 数据库连接
        @sql 
        '''
        logging.log(logging.INFO, "---sql len---:" + str(len(sql)))
        try:
            conn.execute(sql)
        except MySQLdb.Error,e:
            logging.log(logging.INFO, "MySQL error:" + str(e))


def db_commit(conn, table='', sql='', stauts=''):#提交事务
    '''
    Function doc
    执行Mysql提交sql事务
    Parameter doc
    @conn : Mysql数据库连接实例
    @table : 表名
    @sql : sql 语句
    @stauts : 状态 这是一个可选参数
    '''
    if not table or not sql:
        raise TypeError('help:table(str) and sql(str) not none like ==> db_commit(conn,table,sql)')
    if not isinstance(table,str) or not isinstance(sql,str):
        raise TypeError('help:table and sql must be str')

    try:
        logging.log(logging.INFO, "---sql len---:" + str(len(sql)))
        cur = conn.cursor()#创建一个游标实例
        count = cur.execute(sql)#执行sql
        conn.commit()#提交事务
        cur.close()#关闭游标实例

        if stauts:
            logging.log(logging.INFO, 'table "%s" exec sql success %s-tiao' % (table,count))
    except MySQLdb.Error,e:
        print 'MysqlError %s :%s %s' % (e[0],table,e[1])
        logging.log(logging.INFO, table + "  MySQL error:" + str(e))#打印日志
        # with open(table+'.txt','w') as f:#打开或创建以表名命名的txt文件,w 参数意义:每次写入覆盖原来的内容
        #     f.write(sql + '\n')#写入插入失败的sql


def get_list_proportion(kw_list,Proportion='0-100'):
    '''
    Function doc
    按百分比取列表的数据 
    Parameter doc
    @kw_list : list 是数据库读取的关键字列表
    @Proportion : 占比 如 '20-40' 代表取列表 '20%~40%'的数据
    return list
    '''
    if '-' not in Proportion:
        print 'para like 0-20'
        return

    P_1 = int(Proportion.split('-')[0])/100.0
    P_2 = int(Proportion.split('-')[1])/100.0
    P_1 = int(len(kw_list)*P_1)
    P_2 = int(len(kw_list)*P_2)
    print 'list = kw_list[%s:%s]'%(P_1,P_2)
    return kw_list[P_1:P_2]


def ua_request(request,headers=''):
    '''
    Function doc
    更改 request 实例 的请求头 主要是加 User-Agent
    Parameter doc
    @request : url请求实例
    @headers : dict  请求头
    return request url请求实例
    '''
    if headers and isinstance(headers, dict):
        for k,v in headers.items():
            request.headers[k] = v
    request.headers['User-Agent'] = random.choice(USER_AGENT_LIST)
    return request


def safe(s):
    return MySQLdb.escape_string(s)#对字段不转义


def select_data(conn,table,sql):
    '''
    Function doc
    返回数据库查询结果
    Parameter doc
    @conn : Mysql连接实例
    @table : 表名  
    @sql : sql语句 
    return data
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql)
        data = cur.fetchall()
        cur.close()
        print 'table "%s" exec sql success ' % (table)
    except MySQLdb.Error,e:
        print 'MysqlError %s :%s %s' % (e[0],table,e[1])
        return None
    return data


def get_i_sql(table, dict,type=0):
    '''
    Function doc
    生成一句插入sql语句
    Parameter doc
    @table : 表名
    @dict 字典
    return sql
    '''
    if type==1 and 'key_type' in dict.keys():
        dict.pop('key_type')#删除关键字类型字段

    if type==1 and 'table' in dict.keys():
        dict.pop('table')#删除表名字段

    sql = 'insert into %s set ' % table
    sql += dict_2_str(dict)
    return sql


def get_s_sql(table, keys, conditions, isdistinct=0):
    '''
    Function doc
    生成select的sql语句
    Parameter doc
    @table : 表名
    @keys : list 需要查询的字段 
    @conditions : 字典 作为条件的字段
    @isdistinct,查询的数据是否不重复
    return sql
    '''
    if isdistinct:
        sql = 'select distinct %s ' % ",".join(keys)
    else:
        sql = 'select  %s ' % ",".join(keys)
    sql += ' from %s ' % table
    if conditions:
        sql += ' where %s ' % dict_2_str_and(conditions)
    return sql


def get_u_sql(table, value, conditions,type=0):
    '''
    Function doc
    生成update的sql语句
    Parameter doc
    @table : 表名
    @value : dict 数据
    @conditions : 字典 作为条件的字段
    return sql
    '''
    if type==1 and 'key_type' in value.keys():
        value.pop('key_type') #删除关键字类型字段
    if type==1 and 'table' in value.keys():
        value.pop('table')#删除表名字段
    sql = 'update %s set ' % table
    sql += dict_2_str(value)
    if conditions:
        sql += ' where %s ' % dict_2_str_and(conditions)
    return sql


def get_d_sql(table, conditions):
    '''
    生成detele的sql语句
    @table，查询记录的表名
    @conditions,插入的数据，字典
    '''
    sql = 'delete from  %s  ' % table
    if conditions:
        sql += ' where %s ' % dict_2_str_and(conditions)
    return sql


def dict_2_str(dictin):
    '''
    Function doc
    和 dict_2_str_and 方法类似
    将字典转化 " key='value',key='value' " 的字符串形式
    Parameter doc
    @dictin : 字典 数据
    return str
    '''
    tmplist = []

    for k, v in dictin.items():
        tmp = "%s='%s'" % (str(k), safe(str(v)))
        tmplist.append(' ' + tmp + ' ')
    return ','.join(tmplist)


def dict_2_str_and(dictin):
    '''
    Function doc
    和 dict_2_str 方法类似
    将字典转化 " key='value' and key='value' " 的字符串形式
    Parameter doc
    @dictin : 字典 数据
    return str
    '''
    if isinstance(dictin,(str)):
        return dictin
    else:
        tmplist = []
        for k, v in dictin.items():
            tmp = "%s='%s'" % (str(k), safe(str(v)))
            tmplist.append(' ' + tmp + ' ')
        return ' and '.join(tmplist)


def get_page_and_rank(page):
    '''@获取page,rank'''
    page1 = (int(page)/2.0)
    if int(page1)<page1:
        page2 = int(page1) + 1
        rank = 1
    elif page1 == int(page1):
        page2 = int(page1)
        rank = 31
    return page2,rank


def _Insert_Dicts_to_Table(dicts,table,help_text,conn):
    '''
    Function doc
    将一组 dict 插入数据库表
    Parameter doc
    @dicts : 一个list包含多个dict 如: [{'a':1},{'a':2}]
    @table : 表名
    @conn : Mysql 连接数据库实例
    '''
    cur = conn.cursor()#创建实例
    vals = []
    sql = ''
    for i in range(len(dicts)):
        sql = get_i2_sql(table,dicts[i])#生成sql
        val = dict_2_value(dicts[i])#生成结果
        vals.append(val)
    sql = sql + ','.join(vals)
    try:
        count = cur.execute(sql)#操作数据库
        conn.commit()#提交事件
        print 'insert '+table+' '+str(help_text)+' '+str(count)+u'-tiao'+' success...'
        cur.close()#关闭实例
        # conn.close()#断开连接数据库
    except:
        with open(table+'.txt','a') as f:
            f.write(sql+'\n\n')
        print 'insert '+table+' '+str(help_text)+' fail...'


def insert_ignore_dicts(dicts,table,conn):
    '''
    Function doc
    将一组 dict 插入数据库表 忽略报错
    Parameter doc
    @dicts : 一个list包含多个dict 如: [{'a':1},{'a':2}]
    @table : 表名
    @conn : Mysql 连接数据库实例
    '''
    sql = insert_ignore_dicts_sql(dicts,table)
    db_commit(conn,table,sql,1)


def insert_ignore_dicts_sql(dicts,table):
    '''
    Function doc
    将一组 dict 转换成sql
    Parameter doc
    @dicts : 一个list包含多个dict 如: [{'a':1},{'a':2}]
    @table : 表名
    '''
    vals = []
    sql = ''

    try:
        for i in range(len(dicts)):
            sql = get_i2_sql(table,dicts[i])#生成sql
            val = dict_2_value(dicts[i])#生成结果
            vals.append(val)

        sql = sql + ','.join(vals)
    except:
        print 'dicts to sql fail'
        with open('sql.txt','a') as f:
            f.write(str(dicts))
    
    return sql


def dict_2_value(dict):
    '''
    Function doc
    python dict 
    默认是根据key值 排序的, 只要key值一致 
    那么结果排序也是一致的
    将字典变成，('value','value') 的形式
    Parameter doc
    @dict : 字典
    return ('value','value')
    '''
    tmplist = []
    for k, v in dict.items():
        if isinstance(v,(unicode)):
            v = v.encode('utf-8', "ignore")
        try:        
            tmp = "%s" %safe(str(v))
        except Exception,e:
            logging.log(logging.INFO, "dict_2_value Fail...")
            return
        tmp = "'"+tmp+"'"
        tmplist.append(tmp)
    val = '('+','.join(tmplist)+')'
    return val


def dict_2_field(dict):
    '''
    Function doc
    将字典变成，('key','key')
    Parameter doc
    @dict : 字典
    return ('key','key')
    '''
    fieldlist = []
    for k, v in dict.items():
        fields = "`%s`" %str(k)
        fieldlist.append(fields)

    field = '('+','.join(fieldlist)+')'
    return field


def get_i2_sql(table,dict):
    '''
    Function doc
    生成sql 类似 : INSERT INTO table (key,key,key)  VALUES
    Parameter doc
    @table : 表名
    @dict : 字典数据
    return sql
    '''
    field = dict_2_field(dict) #返回字段(key,key,key)
    sql = 'INSERT IGNORE INTO %s %s  VALUES ' % (table,field)
    return sql


def get_page(url,p1,p2='@zsl@',num=1):#获取页数
    '''
    @url,url地址
    @p1,页数字前面的字符
    @p2,页数字后面的字符
    @num,每页数字改变大小
    '''
    if url.find(p1) == -1:
        page = 0
    else:
        page = (url.split(p1)[1]).split(p2)[0]
        if num == 1:
            return page
        else:
            page = (int(page) + num)/num
            return page

    
def get_max_page(count,num,diy_page=100):
    '''
    根据商品总数,每页商品数量,和用户自定义的页数,比较获取正确的页数
    @count,网页商品总数
    @num,每页商数数量
    @diy_page,自定义最大的页码
    '''
    max_page = float(count)/num
    if max_page >diy_page:
        max_page = diy_page
    elif max_page > int(max_page):
        max_page = int(max_page) + 1
    else:
        max_page = int(max_page)
    return max_page


def Get_end_and_start_Time(tmroday=1,h_start=0,h_end=9,m_start=0,m_end=0):
    '''
    @获取具体时间,开始和结束时间戳
    @tmroday默认等于1 如果是今天等于0
    @h_end 结束 小时
    @h_start 开始小时
    @m_start 开始分钟
    @m_end 开始分钟
    '''
    tmroday = int(tmroday)
    today = datetime.datetime.today()
    
    time_end = datetime.datetime(today.year, today.month, today.day + tmroday, h_end, m_end, 0)
    time_start = datetime.datetime(today.year, today.month, today.day + tmroday, h_start, m_start, 0)
    
    time_start = time.mktime(time_start.timetuple())
    time_end = time.mktime(time_end.timetuple())
    return time_start,time_end


def time_do_sleep(sleep_time=0,start=0,end=0):
    '''
    函数意义:在规定时间段内,每个小时30-35分钟内会执行睡眠
    如果睡眠时间小于5分钟,连续调用函数,可能会连续执行多次
    
    @sleep_time 是睡眠时间
    @start 是开始睡眠的时间范围
    @end 睡眠结束的时间范围
    '''
    now = time.time()
    sleep_time = sleep_time

    for i in range(start,end):#每跑1个小时睡眠21分钟
        start_time,end_time = Get_end_and_start_Time(0,i,i,30,35)
        if int(now) > int(start_time) and int(now) < int(end_time):
            print 'sleep-start:'+time.strftime("%Y-%m-%d %H:%M:%S")
            time.sleep(sleep_time)
            print 'sleep-end:'+time.strftime("%Y-%m-%d %H:%M:%S")


def send_email(fname):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.header import Header
    #创建一个带附件的实例
    to_addr = TO_EMAILS_LIST_6
    message = MIMEMultipart()
    # message['From'] = Header(u"虫子")
    message['To'] =  ','.join(to_addr)
    subject = '爬虫日志'
    message['Subject'] = Header(subject, 'utf-8')

    #邮件正文内容
    message.attach(MIMEText('爬虫日志文件请查收', 'plain', 'utf-8'))

    # 构造附件1，传送当前目录下的 test.txt 文件
    att1 = MIMEText(open(fname, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'
    # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
    att1["Content-Disposition"] = 'attachment; filename='+fname
    message.attach(att1)
    # 输入Email地址和口令:
    from_addr = FROM_EMAIL_DICT['user_name']
    password = FROM_EMAIL_DICT['passwd']
    # 输入SMTP服务器地址:
    smtp_server = 'smtp.exmail.qq.com'
    # 输入收件人地址:

    import smtplib
    server = smtplib.SMTP(smtp_server, 25) # SMTP协议默认端口是25
    server.set_debuglevel(1)
    try:
        server.login(from_addr, password)
    except:
        print 'fail'
    server.sendmail(from_addr, to_addr, message.as_string())
    server.quit()


#代理ip验证
def proxyVF(proxy):
    '''@proxy 代理ip,exp:123.123.123.132:8080'''
    try:
        proxy_handler = urllib2.ProxyHandler({'http':proxy})
        opener = urllib2.build_opener(proxy_handler)#创建代理ip对象
        urllib2.install_opener(opener)#使用代理ip
        res = urllib2.urlopen('http://www.oschina.net/',timeout=3).read()
        if len(res) > 1000:
            print '--- proxy --- pass ---'
            return proxy
    except:
        print '---proxy---Not---pass---'


#计算时间差
def time_differ(date1='12:55:05',date2='13:15:05'):
    '''
    @传入是时间格式如'12:55:05'
    '''
    if '-' in date1:
        date1=datetime.datetime.strptime(date1,"%Y-%m-%d %H:%M:%S")
        date2=datetime.datetime.strptime(date2,"%Y-%m-%d %H:%M:%S")
    else:
        date1=datetime.datetime.strptime(date1,"%H:%M:%S")
        date2=datetime.datetime.strptime(date2,"%H:%M:%S")

    if date1 < date2:        
        return date2-date1
    else:
        return date1-date2


from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import parseaddr, formataddr
import smtplib
class ZYMail_z(object):
    '''
    @classdoc
    '''
    def __init__(self):
        self.mail_to = ['576879814@qq.com']
        self.title = '爬虫日志'
        self.conent_type = 'html' #正文数据类型
        self.smtp_server = 'smtp.exmail.qq.com' #服务器地址
        # self.mail_from = 'zsl@chinaclouddata.cn'
        self.mail_from = FROM_EMAIL_DICT['user_name']
        self.att = ''#附件

    def _format_addr(self,s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    def attachment(self,fname):#附件
        # 构造附件1
        self.att = MIMEText(open(fname, 'rb').read(), 'base64', 'utf-8')
        self.att["Content-Type"] = 'application/octet-stream'
        self.att["Content-Disposition"] = 'attachment; filename=%s' % (fname)  # 这里的filename可以任意写，写什么名字，邮件中显示什么名字

    def send_email(self,text_content,user=None, passwd=None):
        #创建一个带附件的实例
        message = MIMEMultipart()
        message['From'] = self._format_addr('zsl<%s>'%self.mail_from)
        message['To'] =  ','.join(self.mail_to)
        message['Subject'] = Header(self.title, 'utf-8')
        #邮件正文内容
        message.attach(MIMEText(text_content, self.conent_type,'utf-8'))
        
        if self.att:#附件
            message.attach(self.att)
            
        # 输入Email地址和口令:
        # from_addr = FROM_EMAIL_DICT['user_name']
        # password = FROM_EMAIL_DICT['passwd']

        server = smtplib.SMTP(self.smtp_server, 25) # SMTP协议默认端口是25
        # server.set_debuglevel(1)
        try:
            server.login(user, passwd)
        except:
            print time.strftime("%Y-%m-%d %H:%M:%S"), 'fail'

        mail_from = user
        server.sendmail(mail_from, self.mail_to, message.as_string())

        server.quit()


def select_description(conn,sql):
        '''
        @@@return dict
        ''' 
        cur = conn.cursor()#创建实例
        try:
            item = {}
            try:
                cur.execute(sql)
            except :
                print 1
                return ''

            data = cur.fetchall()
            # data = list(data)
            # for d in range(len(data)):
            #     data[d] = list(data[d])
            #     for i in range(len(data[d])):
            #         if isinstance(data[d][i],(unicode)):
            #             data[d][i] = data[d][i].encode('utf-8', "ignore")
            description = cur.description #字段描述
            # description = list(description)
            # for d in range(len(description)):
            #     description[d] = list(description[d])
            #     for i in range(len(description[d])):
            #         if isinstance(description[d][i],(unicode)):
            #             description[d][i] = description[d][i].encode('utf-8', "ignore")
            item['data'] = data
            item['description'] = description
        
        except MySQLdb.Error,e:
            print 'MysqlError %s : %s' % (e[0],e[1])
            return
        cur.close()#关闭实例
        return item


class Html(object):
    '''
    Class doc
    html格式的数据内容,供邮件预览
    '''

    def html(self,datas,title,help_text = '',table_name = ''):#返回html数据
        html_table = self.get_html_table(datas,table_name)
        html = self.get_html(title,html_table,help_text)
        return html

    def get_html_table(self,datas,table_name = ''):
        '''
        @datas  is  list
        @return html table
        '''
        html_table = ''
        for iii in range(len(datas)):#tables
            data = datas[iii]['data']
            description = datas[iii]['description']
            th_s = ''   
            for i in range(len(description)):#字段名称
                th = description[i][0].encode('utf-8', "ignore") if isinstance(description[i][0],unicode) else description[i][0]
                th_s += '<td width="100px" bgcolor="Aquamarine">%s</td>' % (th)
            tr_s = ''
            for i in range(len(data)): #字段内容
                td_s = ''
                for ii in range(len(data[i])):
                    td = data[i][ii].encode('utf-8', "ignore") if isinstance(data[i][ii],unicode) else data[i][ii]
                    td_s += '<td width="100px" bgcolor="PowderBlue" >%s</td>' % (td)
                tr_s += '<tr>' +td_s+ '</tr>'
            
            html_table += '''
                            <table border="1">
                                <tr><th>%s</th></tr>
                                <tr>%s</tr>
                                %s
                            </table>
                        '''%(table_name,th_s,tr_s)
        return html_table

    def get_html(self,title,html_table,help_text = ''):
        '''
        Function doc
        返回一个html页面代码
        @title html中的一个小标题
        @html_table html表格
        @help_text 帮助文档
        '''
        html  = '''
                    <html>
                        <head></head>
                        <body>
                        <h3>%s</h3>
                            %s
                            %s

                        </body>
                    </html>
                '''%(title,help_text,html_table)
        return html


USER_AGENT_LIST =[
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)",
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; InfoPath.1)",
            "Mozilla/4.0 (compatible; GoogleToolbar 5.0.2124.2070; Windows 6.0; MSIE 8.0.6001.18241)",
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; EasyBits GO v1.0; InfoPath.1; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; Sleipnir/2.9.8)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; WOW64; Trident/6.0)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; ARM; Trident/6.0)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; .NET4.0C; .NET4.0E)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; BIDUBrowser 2.x)",
            'Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) BaiduHD/4.1.0.0 Mobile/10A406 Safari/8536.25',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.7.3000 Chrome/30.0.1599.101 Safari/537.36',
            'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/10.04 Chromium/12.0.742.112 Safari/534.30',
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:35.0) Gecko/20100101 Firefox/35.0',]


class SSH_2_remote_db(object):
    '''
    Class doc
    通过ssh 连接远程数据库
    '''
    def __init__(self):
        '''
        Function doc
        初始化类,定义一些参数
        @ssh_username : ssh登录的服务器用户名
        @ssh_passwd : ssh登录的服务器密码
        @ip : ssh登录的服务器ip
        @ssh_port : ssh登录的服务器 ssh 端口
        @remote_db_address : Mysql远程数据库远程地址
        @db_user : Mysql登录用户名'
        @db_passwd : Mysql登录密码
        @db_name : Mysql 数据库
        '''
        self.ssh_username = 'ssh_username'
        self.ssh_passwd = 'ssh_passwd!'
        self.ip = 'ip'
        self.ssh_port = 22
        self.remote_db_address = 'remote_db_address'
        self.db_user = 'db_user'
        self.db_passwd = 'db_passwd'
        self.db_name = 'db_name'

    def ssh_2_remote_server(self):
        '''
        Fucntion doc
        获取ssh连接远程服务器实例
        return ssh连接远程服务器实例
        '''
        return SSHTunnelForwarder(
            (self.ip, int(self.ssh_port)),
            ssh_password=self.ssh_passwd,
            ssh_username=self.ssh_username,
            remote_bind_address=(self.remote_db_address, 3306))

    def ssh_2_db_conn(self,server):
        '''
        Function doc
        获取远程数据库连接实例
        Parameter doc
        @server : ssh连接远程服务器实例
        return 远程数据库连接实例
        '''
        return MySQLdb.connect(host='localhost',
            port=server.local_bind_port,
            user=self.db_user,
            passwd=self.db_passwd,
            db=self.db_name,
            charset='utf8')

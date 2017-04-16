#coding:utf8
import sys
import os
import time
import datetime
import MySQLdb
import subprocess
from optparse import OptionParser
from twisted.python import log
import socket
import urllib2
reload(sys)
sys.setdefaultencoding('utf-8')
path1 = (os.getcwd())
if os.name != 'nt':
    path1 = path1.split('/Scrapy_crawlers')[0] + '/Scrapy_crawlers/Shop_site_crawler'
else:
    path1 = path1.split('\Scrapy_crawlers')[0] + '\Scrapy_crawlers\Shop_site_crawler'
sys.path.append(path1)
from settings import DBS,FROM_EMAIL_DICT,TO_EMAILS_LIST_2
from zsl_spider_lib import get_list_proportion
from zsl_spider_lib import time_differ
from zsl_spider_lib import ZYMail_z
from zsl_spider_lib import _Insert_Dicts_to_Table,select_data
from zsl_spider_lib import get_conn

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
    return parser.parse_args()


def judgeProcess(spider):
    '''
    Function doc
    调用命令行,判断爬虫是否在运行
    Parameter doc
    @spider 爬虫名称 如: bitem
    return 0 或 1
    '''
    try:
        cmd = '''
            ps uxf | grep 'scrapy_%s.sh' | grep -v grep | awk '{print $9,$10}' 
            ''' % (spider)

        print 'judgeProcess command:', cmd
        P = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
        out = P.communicate()

        print 'this is out[0]:',out[0],type(out[0]),len(out[0])

        if len(out[0]) >22:#字符串长度超过22 说明进程存在
            print '---Exist process!'
            return 1
        else:
            print '---Not exist process!'
            return 0
    except:
        print 'judgeProcess fail!'
        return 1


def judge_ydhy_job(conn, spider):
    '''
    Fuction doc
    判断任务列表还有有运动行业的未执行任务
    Parameter doc
    @conn Mysql数据库连接实例
    @spider 爬虫的名字
    ruturn 返回查询出来的条数
    '''
    sql = "SELECT count(1) FROM spider_jobs WHERE stauts = 9 AND task_type = '%s' " % (spider)
    print sql
    data = select_data(conn,'spider_jobs',sql)
    return int(data[0][0])


def getJob(conn, spider, stauts=0):
    '''
    Function doc
    1.获取任务id
    2.更新任务状态为1 (
        1.如果更新成功则retrun 返回 id,keyword,uptime等信息
        2.如果更新失败说明被其他机子更新走了,则,return 0)
    Parameter doc
    @conn Mysql数据库连接实例
    @spider 爬虫名字 如: bitem
    @stauts 初始状态如果 stauts = 9 可能是特步运动行业的任务
    '''
    #获取任务id
    sql = "SELECT id,keyword FROM spider_jobs WHERE stauts = %s AND task_type = '%s' LIMIT 1 " % (stauts,spider)
    print sql
    cur = conn.cursor()
    cur.execute(sql)
    r = cur.fetchone()
    id = ''

    if r and r[0]:
        id = int(r[0])
        keyword = str(r[1])
    if not id:
        return 'not_id'

    #更新任务id状态
    ip = socket.gethostbyname(socket.gethostname())
    update_time = time.strftime("%Y-%m-%d %H:%M:%S")
    sql = ''' UPDATE spider_jobs SET stauts = 1,ip = '%s',update_time = '%s' 
            WHERE id = %s AND stauts = %s ''' % (ip,update_time,id,stauts)#stauts = 0 要加上这个条件是因为如果被其他机器更新了状态就不是0了
    print sql
    count = cur.execute(sql)
    conn.commit()
    #得到ID，如果没有了怎么办
    #“update XXXX set stauts = 1,ip,uptime where ID= XXX and stauts = 1”
    #判断更新的行数，这里有可能更新失败，ID被其他机器更新走了
    #这里还有一个问题，如果这个ID是最后一个，那就没有了。
    cur.close()

    if count:
        return id,keyword,update_time #更新成功,获取任务成功
    else:
        return 0 #更新失败,获取任务失败


def spider(spider, para):
    '''
    Function doc
    调用命令行,执行爬虫
    Parameter doc
    @spider 爬虫名字
    @para 带参数的执行爬虫命令
    return 1 或者 None
    '''
    curDate = time.strftime("%Y-%m-%d")
    if os.name == 'nt':
        para = "%s " % (para)
        # elif spider == 'search':
        #     para = "%s -s LOG_LEVEL=DEBUG 2>> /home/admin/spider_logs/%s_%s.log " % (para,curDate,spider)
    else:
        para = "%s 2>> /home/admin/spider_logs/%s_%s.log " % (para,curDate,spider)
        
    print 'spider command:', para
    P = subprocess.Popen(para, shell=True,stdout=subprocess.PIPE)
    rt_code = P.wait()
    out = P.communicate()
    print out

    if rt_code == 0:
        print 'job success...'
    else:
        print 'job error:%d' % (rt_code)

    if isinstance(out,tuple) and 'OK!' in out[0]:
        return '1'
    else :
        return None


def updateJob(conn,spider,id,update_time,para,st = ''):
    '''
    Function doc
    1.更新任务执行状态,执行成功更新stuats = 2,任务异常更新stuats = 3
    2.把超时任务存入超时表
    Parameter doc
    @conn Mysql 数据库连接实例
    @spider 爬虫名称 如: bitem
    @id 任务的id
    @update_time 任务开始时间
    @para 任务关键词
    @st st存在则说明任务成功
    '''
    end_time = time.strftime("%Y-%m-%d %H:%M:%S")
    job_time = time_differ(end_time,update_time)
    job_time = round(job_time.total_seconds()/60,2) #统计每个任务的时间

    if st:
        sql = ''' UPDATE spider_jobs SET stauts = 2,end_time = '%s',job_time = '%s' 
                WHERE id = %s ''' % (end_time,job_time,id)
    else:#任务异常退出
        sql = ''' UPDATE spider_jobs SET stauts = 3,end_time = '%s',job_time = '%s' 
                WHERE id = %s ''' % (end_time,job_time,id)
    print sql
    cur = conn.cursor()
    count = cur.execute(sql)
    conn.commit()
    cur.close()

    #超时警报!
    # out_time_email(para,spider,job_time)
    out_time_jobs(conn,para,spider,job_time) #把超时任务存入表
    print 'end task id : %s'%id


def out_time_data(para,spider,job_time):
    '''
    Function
    统计超时任务数据
    Parameter doc
    @para 关键词字符串
    @spider 爬虫名字 如:bitem
    @job_time 任务用时
    return 返回 dict
    '''
    para = urllib2.unquote(para.split('para=')[1].replace('"',''))
    try:
        para = para.decode('gbk').encode('utf-8')
    except:
        para = para.decode('utf-8').encode('utf-8')
    item    = {}
    item['up_time']     = time.strftime("%Y-%m-%d %H:%M:%S") #更新时间
    item['up_date']     = time.strftime("%Y-%m-%d") #更新日期
    item['ip']          = socket.gethostbyname(socket.gethostname()) #本机ip
    item['keyword']     = para
    item['job_time']    = job_time
    item['task_type']   = spider
    items = [item]
    return items


def out_time_jobs(conn,para,spider,job_time):
    '''
    Fuction doc
    超时任务存入数据库
    Parameter doc
    @conn Mysql 数据库连接实例
    @para 关键词字符串
    @spider 爬虫名字 如:bitem
    @job_time 任务用时
    '''
    if spider == 'search':
        if job_time < 18:
            data = out_time_data(para,spider,job_time) #get data
            _Insert_Dicts_to_Table(data,'out_time_jobs',spider,conn) #insert into table
    elif spider == 'shop':
        if job_time < 82:
            data = out_time_data(para,spider,job_time) #get data
            _Insert_Dicts_to_Table(data,'out_time_jobs',spider,conn) #insert into table
    elif spider == 'bitem':
        if job_time < 51:
            data = out_time_data(para,spider,job_time) #get data
            _Insert_Dicts_to_Table(data,'out_time_jobs',spider,conn) #insert into table
    elif spider == 'citem':
        if job_time < 63:
            data = out_time_data(para,spider,job_time) #get data
            _Insert_Dicts_to_Table(data,'out_time_jobs',spider,conn) #insert into table


def out_time_email(para,spider,job_time):
    '''
    Funtion doc
    发送超时警报邮件(没有执行,警报标准自己设置)
    Parameter doc
    @para 关键词字符串
    @spider 爬虫名字 如: bitem
    @job_time 任务执行时间
    '''
    mail = ZYMail_z()
    mail.mail_to = TO_EMAILS_LIST_2
    mail.title = '行业爬虫 %s 任务监控 %s ' % (spider,today)
    para = urllib2.unquote(para.split('para=')[1].replace('"',''))
    try:
        para = para.decode('gbk').encode('utf-8')
    except:
        para = para.decode('utf-8').encode('utf-8')

    if spider == 'search':
        if job_time > 30 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    超过了 30 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'
        elif job_time < 10 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    低于 10 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'
    elif spider == 'shop':
        if job_time > 100 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    超过了 100 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'
        elif job_time < 10 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    低于 10 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'
    elif spider == 'bitem':
        if job_time > 70 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    超过了 70 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'
        elif job_time < 10 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    低于 10 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'
    elif spider == 'citem':
        if job_time > 80 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    超过了 80 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'
        elif job_time < 10 :
            text = ''' 
                    任务类型:%s <br> 
                    任务用时:%s 分钟<br> 
                    关键词:%s <br>
                    低于 10 分钟的限定值
                    ''' % (spider,job_time,para)
            mail.send_email(text,FROM_EMAIL_DICT['user_name'], FROM_EMAIL_DICT['passwd'])
            print 'send email!'


def main():
    '''
    Function doc
    1.判断进程中是否有相同的爬虫在运行(如果有,则退出)
    2.当进程中没有相同的爬虫运行的时候,去获取爬虫任务(
        1.当任务表没有任务时直接退出程序
        2.当获取任务失败的时候等待再获取
        3.当获取任务成功继续下一步)
    3.当获取任务成功后,开始执行爬虫(判断爬虫是否运行正常)
    4.更新任务列表,表示任务完成
    '''
    opts, args = parse_opts()
    print opts.type
    conn = get_conn(DBS,'scrapy')
    print 'job start :',datetime.datetime.now()
    
    if (judgeProcess(opts.type) == 0):#判断进程中是否有相同的爬虫在运行
        print 'judgeProcess success!'
        ydhy_job = judge_ydhy_job(conn, opts.type)#检测是否有运动行业的任务
        print 'ydhy_job:',ydhy_job

        while True:

            if ydhy_job > 0:
                stauts = 9
            else:
                stauts = 0

            get_Job = getJob(conn,opts.type,stauts)#获取任务状态
            if (get_Job == 0) :
                print 'get job fail !'#获取任务失败
                time.sleep(10)
            elif get_Job == 'not_id':
                print 'not id to task !'#没有任务了
                return
            else:
                print 'get job success !'#获取任务成功
                id,para,update_time = get_Job
                break

        print stauts,id,para,update_time
        suc = spider(opts.type, para)#执行爬虫
        if suc:#任务正常
            updateJob(conn,opts.type,id,update_time,para,1)
        else:#任务失败
            updateJob(conn,opts.type,id,update_time,para)
    conn.close()


if __name__ == '__main__':
	main()

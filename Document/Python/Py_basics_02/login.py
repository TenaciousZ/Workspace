#coding:utf8
'''
Date:2017/04/09
author:顽强
模拟登录网页
'''
import urllib2
import urllib
import cookielib

class Login(object):
	'''Class doc'''
	def __init__(self, login_url, post_data=None):
		self.login_url = login_url
		self.post_data = None
		if isinstance(post_data,dict):
			self.post_data = urllib.urlencode(post_data)

	def set_cookie_jar(self):
		'''
		Function doc
		设置自动接收cookie的容器
		'''
		cookie_jar = cookielib.LWPCookieJar()  
		cookie_support = urllib2.HTTPCookieProcessor(cookie_jar)  
		opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)  
		urllib2.install_opener(opener)

	def login(self):
		'''
		Function doc
		登录url
		'''
		self.set_cookie_jar()
		urllib2.urlopen(self.login_url,self.post_data)

	def login_next(self,next_url):
		'''
		Function doc
		登录完请求跳转页,此时已经有cookie了
		'''
		self.login()
		res = urllib2.urlopen(urllib2.Request(next_url))
		return res.read()



#登录
login_url = 'http://www.xmrc.com.cn/net/Talent/Login.aspx'
#登录后跳转页
next_url = 'http://www.xmrc.com.cn/net/Talent/Main.aspx'

post_data = {
	'username':123,
	'password':'xxx'
}

login_ = Login(login_url,post_data)
text = login_.login_next(next_url)
with open('xmrc.html','w') as f:
	f.write(text)

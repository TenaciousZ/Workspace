#-*-coding:utf8-*-
#字符串编码方式
import chardet #输出字符串的编码方式
print type(u'中文') #unicode编码
print type(u'中文'.encode('utf8')) #将 unicode 编码 utf8

s = '\xc3\x96\xc3\x90\xc3\x8e\xc3\x84'
print type(s)
print chardet.detect(s)
print s

print type('\xe4\xb8\xad\xe6\x96\x87'.decode('utf8')) #utf8编码转成unicode
print type('中文'.decode('utf8')) #utf8编码转解码unicode


print chardet.detect('中文')['encoding']
print '中文'.decode('utf8')
print u'中文'+u'中文'
print '中文%s'%('中文')
print '中文{1}{0}'.format('中文','文一')

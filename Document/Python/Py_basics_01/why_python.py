#-*-coding:utf8-*-
#例子1:对换两个变量的值
#简练写法:
a = 1
b = 2
a,b = b,a
print a,b

#正常写法
a = 4
b = 5
c = a #多出来一个变量
a = b
b = c
print a,b

print [m + n for m in 'ABC' for n in 'XYZ']#全排列
L = ['Hello', 'World', 'IBM', 'Apple']
print [s.lower() for s in L]

#例子2:列出列表的key和value
#明确的写法
array = [1, 2, 3, 4, 5]
for i, e in enumerate(array,0):
	print i, e

#复杂的写法
for i in xrange(len(array)):
	print i, array[i]


#例子3:变量是否为空
name = 'Tim'
langs = ['AS3', 'Lua', 'C']
info = {'name': 'Tim', 'sex': 'Male', 'age':23 }    

#优雅的写法
if name and langs and info:
	print('All True!')  #All True!

#普通的写法
if name != '' and len(langs) > 0 and info != {}:
	print('All True!') #All True!


#例子5:将字母倒序
#切片最后一个参数,数字代表步长(step), - 号代表反序
def reverse_str( s ):
	print s[0:5]
	print 's[5]:',s[5]
	print 's[0]:',s[0]
	print s[5:0:-1] #反序 s[5]-s[0]
	print s[::2]

reverse_str('123456789')


def reverse_str( s ):
    t = ''
    for x in xrange(len(s)-1,-1,1):
        t += s[x]
    print t

reverse_str('sdfsafd')

print list(xrange(100,-1`,-1))
print range(101)[::-1]
print list(xrange(5,0))
print list(xrange(0,5,2))

#coding:utf8
#函数的进阶


'''
函数的作用域:LEGB
L:local 函数内部使用
E:enclosing 函数内部和内嵌函数使用
G:global 全局作用一般定义在文件顶部
B:build-in Python内置变量:如list,tuple等

函数的实质和属性

1.函数是一个对象
2.函数执行完内部变量回收
3.函数的属性
4.函数的返回值
'''

'''1.闭包
	闭包的作用:
	1.实现代码的封装
	2.实现代码的复用
'''


def set_passline(full):
	'''
	Function doc
	返回的是整个cmp函数
	有参加返回的函数中的变量是不会回收的
	'''
	passline = int(full*0.6)
	def cmp(val):
		if val < passline:
			print 'full score:%s,passline:%s and %s failed'%(full,passline,val)
		else:
			print 'full score:%s,passline:%s and %s pass'%(full,passline,val)
	return cmp

f_100 = set_passline(100)
f_150 = set_passline(150)
f_100(89)
f_150(89)



'''2.装饰器'''

def dec(func):
	def in_dec(*arg):
		if len(arg) == 0:
			return 0
		for val in arg:
			if not isinstance(val,int):
				return 0
		return func(*arg)
	return in_dec

@dec
def my_sum(*arg):
	print arg
	return sum(arg)
'''
调用步骤:
1.执行dec() -> 返回 in_dec() -> 调用my_sum()
'''
print my_sum(1,2)


import time
def time_diff(func):
	start = time.time()
	def in_time(*arg):
		func(*arg)
		print time.time() - start
	return in_time

@time_diff
def my_sum1(*arg):
	return sum(arg)

my_sum1(*range(1000))

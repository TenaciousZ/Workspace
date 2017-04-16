#coding:utf-8
#递归
#递归有个特点是必须要有个退出的出口
import types


def fact(n):
	'''
	Fucntion doc
	递归函数,反复调用知道n==1时,停止调用,返回最终结果
	'''
	if n == 1:#当n == 1时递归结束
		return 1
	else:
		return fact(n-1) + n

print fact(5)


def fib(count, cur=0, next_=1):
	'''
	Function doc
	尾递归,
	斐波切尔数列,1,2,3,5,8
	'''
	if count <= 1:
		return cur
	else:
		print 1
		print cur
		return fib(count-1, next_, cur + next_)


def tramp(gen, *args, **kwargs):
	'''
	Functiong doc
	使用生成器优化尾递归,内存不在溢出,返回最后的结果
	'''
	g = gen(*args, **kwargs)
	print type(g)
	i = 0
	while isinstance(g, types.GeneratorType):
		g=g.next()
		i += 1
	print i
	print type(g)
	return g

def fact_list2(list,sum=0):
	'''
	Function doc
	列表内元素求和
	尾递归,生成器的方式
	递归求和太慢了,没有意义,必须用算法
	'''
	if len(list) == 1:
		yield sum
	else:
		yield fact_list2(list[:len(list)-1],sum+list[len(list)-1])


print tramp(fact_list2,range(100000))

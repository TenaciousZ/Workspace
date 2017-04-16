#coding:utf8
#单例模式:程序运行的时候,类只被实例化一次
#装饰器,实现单例模式
#

def singleton(cls, *arg, **kw):
	instances = {}
	def _in_single_ton(*arg, **kw):
		if cls not in instances:
			instances[cls] = cls(*arg,**kw)
		return instances[cls]
	return _in_single_ton

@singleton
class MyClass(object):
	def __init__(self, x=0):
		self.x = x


one = MyClass(1)
two = MyClass()
print id(one)
print id(two)


print two.x

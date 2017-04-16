#-*-coding:utf8-*-

#函数的学习
#例子1参赛的定义和使用
def enroll(name, gender, age=6, city='Beijing'):
	print 'name:', name
	print 'gender:', gender
	print 'age:', age
	print 'city:', city

enroll(gender=1,name=2,city='Xiamen')
enroll(1,2,3,4)

#例子2默认参数必须是固定的对象
def add_end(L=[]):
	print 'L = ',L
	L.append('END')
	return L

print 1
print add_end()
print 2
print add_end()
print 3
print add_end()

#例子3可变参数
#可变参数是把参数组合成一个list or tuple
def calc(*numbers):
    sum = 0
    for n in numbers:
        sum = sum + n * n
    return sum

print calc(1,2,3,4)
num = range(5)
print calc(*num) #*+list or *+tuple

#例子4关键词参数
def person(name, age, **kw):
    print 'name:', name, 'age:', age, 'other:', kw
person(1,2,c=3,d=4) #自动把 c=3,d=4 转换成 dict 所以说是关键词参数
kw = {'a':1,'b':2}
person(1,2,**kw) #** + dict 



#5.递归函数
# def fact(n):
#     if n==999:
#         return 1
#     return n + fact(n + 1)

# print fact(1)

# def fact_iter(num, product):
#     if num == 998:
#         return product
#     return fact_iter(num + 1, num + product)

# def fact(n):
#     return fact_iter(n, 1)

# print fact(1)

#高阶函数
#函数可以作为变量,赋值,也可以作为一个参数
f = person
f(1,2)

def add(x,y,f):
	return f(x) + f(y)

print type(abs) #内建函数
print add(1,-10,abs)


#内建高阶函数map
#将方法作用于列表中的每个元素,返回list
def f(x):
	return x * x

print map(f,range(5))
print map(f,[20])

def map2(f,nums):
	return [f(x) for x in nums]

print map2(f,range(5))
print map2(f,[20])

#内建高阶函数reduce
#educe把一个函数作用在一个序列[x1, x2, x3...]上，这个函数必须接收两个参数，reduce把结果继续和序列的下一个元素做累积计算，其效果就是：
#reduce(f, [x1, x2, x3, x4]) = f(f(f(x1, x2), x3), x4)
def add(x,y):
	return x*10 + y

def str(x,y):
	return x + y

print reduce(str,['1'])

def reduce2(f,nums):
	l = len(nums)
	if l == 1:
		return nums[0]
	if l == 2:
		return f(nums[0],nums[1])

	s = f(nums[0],nums[1])
	for i in range(2,len(nums)):
		s += nums[i]
	return s


print reduce2(str,['1','2','3','4'])


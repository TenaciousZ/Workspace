#coding:utf-8

#__author__:顽强

#01.Python默认参数的定义
def extendList(val, list=[]):
    list.append(val)
    return list
 
list1 = extendList(10)
list2 = extendList(123,[])
list3 = extendList('a')
 
print "list1 = %s" % list1
print "list2 = %s" % list2
print "list3 = %s" % list3

#这个问题的关键点是:
#python函数默认参数的计算是在函数定义的那一刻,而不是调用函数的时候
#当没有指定list的时候,list1和list3操作的是同一个list
#定义函数的时候要注意默认参数值不要使用可变的表达式,默认参数一般使用固定值
#End 01


#02.Python的函数闭包延迟绑定
def multipliers():
  return [lambda x: i * x for i in range(4)]

print [m(2) for m in multipliers()]

def multipliers():
    ll =[]
    for i in range(4):
        def lambda_(x):
            # print i
            return i*x
        ll.append(lambda_)
    return ll

print [m(2) for m in multipliers()]

#生成器的方式来实现需求,克服延迟绑定
def multipliers():
    for i in range(4):yield lambda x : i*x

print [m(2) for m in multipliers()]
#这个问题的关键点是:
#Python的函数闭包return返回结果延迟绑定,
#因此,在调用函数multipliers时for循环已经结束,循环次数不变,
#但是lambda_中的 i的值,因为延迟绑定最后定位在3
#End 02

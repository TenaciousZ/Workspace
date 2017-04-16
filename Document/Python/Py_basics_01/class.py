#-*-coding:utf8-*-
import inspect

#类的继承
class Student(object):
	'''
	Class doc
	幼儿园类
	'''
	name = 'zsl'
	score = '99'
	subject = 'game'
	def __init__(self,name='zsl'):
		self.name = name

instance = Student('sl')
print instance #实例对象
print Student #类
print 'child name is >>>',instance.name

class Student_small(Student):
	'''
	Class doc
	小学类
	'''
	score = '98'
	subject = 'code'
	
instance_small = Student_small()
print 'small name is >>>',instance_small.name
print 'small score is >>>',instance_small.score

class Student_middle(Student_small,Student):
	'''
	Class doc
	中学类
	'''
	hobby = 'play game'


instance_middle = Student_middle()
print 'middle name is >>>',instance_middle.name
print 'middle hobby is >>>',instance_middle.hobby
print 'middle score is >>>',instance_middle.score
print 'middle subject is >>>',instance_middle.subject




#super方法 多重继承的时需要初始化父类强烈要求使用super()
print 'super','-'*30

class A(object):
	def __init__(self):
		print "enter A"
		print "leave A"
class B(object):
	def __init__(self):
		print "enter B"
		print "leave B"
class C(A):
	def __init__(self):
		print "enter C"
		super(C, self).__init__()
		print "leave C"
class D(A):
	def __init__(self):
		print "enter D"
		super(D, self).__init__()
		print "leave D"
class E(B, C):
	def __init__(self):
		print "enter E"
		B.__init__(self)
		C.__init__(self)
		print "leave E"
class F(E, D):
	def __init__(self):
		print "enter F"
		E.__init__(self)
		D.__init__(self)
		print "leave F"
# F()
# print "enter F"
# print "enter E"
# print "enter B"
# print "leave B"
# print "enter C"
# print "enter A"
# print "leave A"
# print "leave C"
# print "leave E"
# print "enter D"
# print "enter A"
# print "leave A"
# print "leave D"
# print "leave F"

class A(object):
	def __init__(self):
		print "enter A"
		super(A, self).__init__()  # new
		print "leave A"
class B(object):
	def __init__(self):
		print "enter B"
		super(B, self).__init__()  # new
		print "leave B"
class C(A):
	def __init__(self):
		print "enter C"
		super(C, self).__init__()
		print "leave C"
class D(A):
	def __init__(self):
		print "enter D"
		super(D, self).__init__()
		print "leave D"
class E(B, C):
	def __init__(self):
		print "enter E"
		super(E, self).__init__()  # change
		print "leave E"
class F(E, D):
	def __init__(self):
		print "enter F"
		super(F, self).__init__()  # change
		print "leave F"
	
F()

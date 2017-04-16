# -*-coding:utf8-*-

#数据类型
print type(1)
print type(0.1)
print type('hello world')
print type(True)
print type(None)
print type([])
print type(())
print type({})
print type(set())

#例子
print '===============举个例子==============='
#<type 'int'>
print '1 + 1 = ',1 + 1
#<type 'float'>
print '0.1 + 0.1 = ',0.1 + 0.1
#<type 'str'>
print 'abc + abc = ','abc' + 'abc'
#<type 'bool'>
print 'True and False = ',True and False
print 'True or False = ',True or False
print 'True + False = ',True + False
print 'True == 1 is',True == 1
print 'False == 0 is',False == 0
#<type 'NoneType'>
print 'None and None = ',None and None
print 'None or None = ',None or None
#<type 'list'>
print '[1,2] + [3,4] = ' ,[1,2] + [3,4]
#<type 'tuple'>
print '(1,2) + (3,4) = ' ,(1,2) + (3,4)
#<type 'dict'>
print "a in {'c':3,'d':4} = " ,'a' in {'c':3,'d':4}
#<type 'set'>
print 'set((1,2,3,3,5)) = ' , set((1,2,3,3,5))
s1 = set((2,3,3,5))
s1.add(6)
s1.add(True)
s1.add('True')
s1.add('t')
s1.add('s')
print 's1.add(6) = ',s1
s1.remove(6)
print 's1.remove(6) = ',s1
print 'set((1,2,3,4)) | set((3,4,5,6)) = ',set((1,2,3,4)) | set((3,4,5,6)) #交集
print 'set((1,2,3,4)) & set((3,4,5,6)) = ',set((1,2,3,4)) & set((3,4,5,6)) #并集
print 'set((3,4,5,6,7,8)) ^ set((1,2,3,4)) = ',set((3,4,5,6,7,8)) ^ set((1,2,3,4)) #对称差集
print 'set((3,4,5,6)) - set((1,2,3,4)) = ',set((3,4,5,6)) - set((1,2,3,4)) #差集
print 'set((1,2,3,4)) - set((3,4,5,6)) = ',set((1,2,3,4)) - set((3,4,5,6)) #差集

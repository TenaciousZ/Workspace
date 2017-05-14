Mongodb 安装

Date:2017/05/10

[安装步骤]()

	1.下载安装包
		下载地址:https://www.mongodb.com/download-center#community

	2.双击安装包
		mongodb-win32-x86_64-2008plus-ssl-3.4.4-signed.msi
		a.选择Custom(自定义安装)
			D:\Mongodb\

	3.创建一个存放数据的文件夹
		D:\data\db # 存放数据
		D:\data\db_log\mongodb.log # 存放日志文件
		D:\data\mongo.config # 配置文件(
			加入两行
			dbpath=D:\data\db  
			logpath=D:\data\db_log\mongodb.log)
	4.配置
		a.进入目录 
			cd D:\Mongodb\bin
		b.配置
		配置服务:
			安装服务:
			mongod.exe --config D:\data\mongo.config --serviceName MongoDB --install
			删除服务
			mongod.exe --config D:\data\mongo.config --serviceName MongoDB --remove
			删除.lock文件

			--bind_ip 				# 绑定ip
			--logpath 				# 日志保存路径
			--logappend 			# 日志追加的方式写日志
			--dbpath 				# 存放数据地址
			--port 					#端口号
			--serviceName 			# 服务名称
			--serviceDisplayName 	# 指定服务名称，有多个mongodb服务时执行。
			--install 				# 指定作为Windows服务安装
			(mongod.exe --bind_ip yourIPadress --logpath "C:\data\db_log\mongodb.log" --logappend --dbpath "C:\data\db" --port yourPortNumber --serviceName "MongoDB" --serviceDisplayName "MongoDBs" --install)

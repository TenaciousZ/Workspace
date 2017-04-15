Java开发环境搭建

#Date: 2017/04/06
#__author__:顽强
1

JDK安装:
	JDK版本:jdk-8u121-windows-i586_8.0.1210.13.exe
	自定义安装路径:D:\Java\jdk1.8.0_121\

配置环境变量:
	1.JAVA_HOME : D:\Java\jdk1.8.0_121; (JDK的安装路径)
	2.PATH : D:\Java\jdk1.8.0_121\bin;D:\Java\jdk1.8.0_121\jre\bin; (JDK的命令文件路径)
	//记得前面有个"." java加载类路径
	3.CLASSPATH : .;D:\Java\jdk1.8.0_121\lib;%JAVA_HOME%\lib\tools.jar; (JDK的类库文件路径)


Eclipse安装:
	Eclipse是开发Java程序的IDE软件
	Eclipse解压包:eclipse-java-neon-3-win32.zip
	自定义安装路径:解压压缩包即可
	下载地址:
	https://www.eclipse.org/downloads/download.php?file=/technology/epp/downloads/release/neon/3/eclipse-java-neon-3-win32.zip&mirror_id=1248

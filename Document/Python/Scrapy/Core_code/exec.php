<html>
<head>
<meta charset="utf-8">
<title>关键字搜索</title>
</head>

<body>
<?php 
ini_set('max_execution_time', '0');
function execInBackground($cmd) 
	{ 
		if (substr(php_uname(), 0, 7) == "Windows"){ 
			pclose(popen("start /B " . $cmd, "r"));  
		} 
		else { 
			exec($cmd . " > /dev/null &");   
		} 
	}

$keyword =  rawurlencode($_GET["fname"]);
$user_id = $_GET["user_id"];
$pagenum = $_GET["pagenum"];
$sort = $_GET["sort"];


execInBackground("scrapy crawlall -a ".$keyword."=".$user_id."@@@@@@".$pagenum."@@@@@@@".$sort);

echo "exec success...keyword is ".rawurldecode($keyword);

?>
</body>
</html>

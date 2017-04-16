NAME=$(date +%Y-%m-%d)
cd /home/admin/Scrapy_crawlers
#1.生成 search 爬虫 任务
python client/client_main/client.py -t search -n 30 >> /home/admin/spider_logs/$NAME"_task_search".log 2>&1
#2.生成 shop 爬虫 任务
python client/client_main/client.py -t shop -n 5 >> /home/admin/spider_logs/$NAME"_task_shop".log 2>&1
#3.生成 citem 爬虫 任务
python client/client_main/client.py -t citem -n 5 >> /home/admin/spider_logs/$NAME"_task_citem".log 2>&1
#4.生成 bitem 爬虫 任务
python client/client_main/client.py -t bitem -n 5 >> /home/admin/spider_logs/$NAME"_task_bitem".log 2>&1

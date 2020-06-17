# twitter_scrapy
推送推特信息到钉钉机器人

## linux 定时任务脚本
```bash
function start_crawl(){
  num=`ps -ef|grep twitte |wc -l`;
  if [ $num -lt 6 ]
  then
   /home/zhd/python3/bin/python3 /home/zhd/python_project/twitter_scrapy/twitter_scraper_test.py
  fi
}
while ((1 < 2))
do
  start_crawl
  sleep 5
done
```

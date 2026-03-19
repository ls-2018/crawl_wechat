import datetime
import os
import subprocess
from sub.log import get_logger
from sub.config import *

logger = get_logger()


class Backup:
    def backup(self):
        d = datetime.datetime.now()
        date = f"{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}"
        cmd = (
            f'mysqldump -u {db_user} --password={db_password} -h {db_host} -P {db_port} {query_db} > /data/{date}-{query_db}.sql.pending ;'
            f'mv /data/{date}-{query_db}.sql.pending /data/{query_db}.sql'
        )
        logger.info(cmd)
        subprocess.getoutput(cmd)

        #  mysqldump -u root --password={db_password}  -h wechat-mysql -P 3306 wechat_article_exporter > /data/wechat_article_exporter.sql
        #  mysqldump -u root --password={db_password}  -h wechat-mysql -P 3306 wechat_query > /data/wechat_query.sql

        cmd = (
            f'mysqldump -u {db_user} --password={db_password} -h {db_host} -P {db_port} {crawl_db} > /data/{date}-{crawl_db}.sql.pending ;'
            f'mv /data/{date}-{crawl_db}.sql.pending /data/{crawl_db}.sql'
        )
        logger.info(cmd)
        subprocess.getoutput(cmd)

    def load(self):
        cmd = (
            f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} '
            f'-e \'DROP DATABASE IF EXISTS {query_db}; DROP DATABASE IF EXISTS {crawl_db};\''
        )
        logger.info(cmd)
        os.system(cmd)

        cmd = (
            f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} '
            f'-e \'CREATE DATABASE IF NOT EXISTS {query_db}; CREATE DATABASE IF NOT EXISTS {crawl_db};\''
        )
        logger.info(cmd)
        os.system(cmd)

        cmd = f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} {crawl_db} < /data/{crawl_db}.sql'
        logger.info(cmd)
        os.system(cmd)

        cmd = f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} {query_db} < /data/{query_db}.sql'
        logger.info(cmd)
        os.system(cmd)

import datetime
import os
import subprocess

from sub.config import *


class Backup:
    def backup(self):
        d = datetime.datetime.now()
        date = f"{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}"
        cmd = (
            f'mysqldump -u {db_user} --password={db_password} -h {db_host} -P {db_port} {query_db} > {data_path}/{date}-{query_db}.sql.pending ;'
            f'mv {data_path}/{date}-{query_db}.sql.pending {data_path}/{query_db}.sql'
        )
        print(cmd)
        subprocess.getoutput(cmd)

        #  mysqldump -u root --password={db_password}  -h wechat-mysql -P 3306 wechat_article_exporter > /data/wechat_article_exporter.sql
        #  mysqldump -u root --password={db_password}  -h wechat-mysql -P 3306 wechat_query > /data/wechat_query.sql

        cmd = (
            f'mysqldump -u {db_user} --password={db_password} -h {db_host} -P {db_port} {crawl_db} > {data_path}/{date}-{crawl_db}.sql.pending ;'
            f'mv {data_path}/{date}-{crawl_db}.sql.pending {data_path}/{crawl_db}.sql'
        )
        print(cmd)
        subprocess.getoutput(cmd)

    def load(self):
        cmd = (
            f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} '
            f'-e \'DROP DATABASE IF EXISTS {query_db}; DROP DATABASE IF EXISTS {crawl_db};\''
        )
        print(cmd)
        os.system(cmd)

        cmd = (
            f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} '
            f'-e \'CREATE DATABASE IF NOT EXISTS {query_db}; CREATE DATABASE IF NOT EXISTS {crawl_db};\''
        )
        print(cmd)
        os.system(cmd)

        cmd = f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} {crawl_db} < {data_path}/{crawl_db}.sql'
        print(cmd)
        os.system(cmd)

        cmd = f'mysql -u {db_user} --password={db_password} -h {db_host} -P {db_port} {query_db} < {data_path}/{query_db}.sql'
        print(cmd)
        os.system(cmd)

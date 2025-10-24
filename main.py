# -*- coding: utf-8 -*-
import datetime
import json
import multiprocessing
import os
import random
import subprocess
import threading
import time

import docker
import rumps

from sub.config import mysql_conf
from sub.crawl import Crawl
from sub.insert import mysql, logger
from sub.server import Server

port = random.randint(18000, 19000)

off_check = False


class PomodoroApp(rumps.App):

    def init(self, sender):
        ready = False
        client = docker.APIClient(base_url='unix:///var/run/docker.sock', version='auto')
        for data in client.containers(all=True):
            if data['Names'][0] == '/wechat-mysql':
                ready = True
                break
        if not ready:
            base_path = '/Users/acejilam/data/wechat-mysql'

            data = '''[mysqld]
host-cache-size=0
skip-name-resolve
datadir=/etc/mysql/data/
socket=/var/run/mysqld/mysqld.sock
secure-file-priv=/var/lib/mysql-files
user=mysql
pid-file=/var/run/mysqld/mysqld.pid
[client]
socket=/var/run/mysqld/mysqld.sock
!includedir /etc/mysql/conf.d/
'''
            try:
                os.makedirs(base_path, exist_ok=True)
            except Exception as e:
                logger.error(e)
                pass
            with open(os.path.join(base_path, 'my.cnf'), 'w', encoding='utf8') as f:
                f.write(data)

            os.system(
                f"docker run -p 18889:3306 --name wechat-mysql --restart=always -e MYSQL_ROOT_PASSWORD=root -v {os.path.join(base_path, 'my.cnf')}:/etc/my.cnf -v {os.path.join(base_path, 'data')}:/etc/mysql/data/ -v {os.path.join(base_path, 'conf')}:/etc/mysql/mysql.conf.d/ -d registry.cn-hangzhou.aliyuncs.com/acejilam/mysql:8"
            )
            time.sleep(3)
            with mysql() as cursor:
                cursor.execute('CREATE DATABASE `wechat`')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_name = args[0]

        self.config = {
            "crawl": "同步数据",
            "server": "运行flask",
            "display": "显示页面",
            "backup": "数据备份",
            "interval": 10
        }
        self.app = rumps.App("", icon="./bj.ico")
        self.interval = self.config["interval"]
        self.server_button = rumps.MenuItem(title=self.config["server"], callback=self.flask)
        self.crawl_button = rumps.MenuItem(title=self.config["crawl"], callback=self.crawl_wechat)
        self.open_button = rumps.MenuItem(title=self.config["display"], callback=self.open)
        self.backup_button = rumps.MenuItem(title=self.config["backup"], callback=self.backup)

        self.app.menu = [
            self.crawl_button,
            self.server_button,
            self.open_button,
            self.backup_button,
        ]
        global port
        self.ui_server = Server(port)
        self.crawl = Crawl()
        self.crawl_thread = None
        self.ui_server_thread = None

    def backup(self, sender):
        d = datetime.datetime.now()
        with open(mysql_conf, 'r', encoding='utf8') as f:
            mysql_info = json.loads(f.read())

        cmd = (
            f'/usr/local/bin/docker run -d --rm -v /etc/hosts:/etc/hosts -v /Users/acejilam/Desktop:/data/ registry.cn-hangzhou.aliyuncs.com/acejilam/mysql bash -c "mysqldump -u {mysql_info["user"]} '
            f'--password={mysql_info["password"]} '
            f'-h {mysql_info["host"]} '
            f'-P {mysql_info["port"]} '
            f'{mysql_info["database"]} > /data/wechat-{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}.sql.pending ;'
            f'mv /data/wechat-{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}.sql.pending /data/wechat-{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}.sql'
            f'"')
        logger.info(cmd)
        out = subprocess.getoutput(cmd)
        self.send_message("backup", out)

    def open(self, sender):
        self.ui_server.openChrome()

    def set_title(self, title):
        self.app.title = title

    def send_message(self, subtitle="", message=""):
        rumps.notification(
            icon="./bj.ico",
            title=self.app_name, subtitle=subtitle, message=message
        )

    def crawl_wechat(self, obj):
        self.crawl_button.state = not self.crawl_button.state
        if self.crawl_button.state:
            self.crawl_thread = threading.Thread(
                target=self.crawl.run,
                args=(self.call_back, self.set_title, self.send_message)
            )
            self.crawl_thread.start()
        else:
            self.crawl.need_crawl = not self.crawl.need_crawl
            self.app.title = ""

    def flask(self, obj):
        self.server_button.state = not self.server_button.state
        if self.server_button.state:
            self.ui_server_thread = multiprocessing.Process(
                target=self.ui_server.run,
            )
            self.ui_server_thread.start()
        else:
            self.ui_server_thread.terminate()

    def call_back(self):
        self.app.title = ""
        self.crawl_button.state = not self.crawl_button.state

    def run(self):
        self.app.run()


if __name__ == '__main__':
    PomodoroApp('微信公众号').run()

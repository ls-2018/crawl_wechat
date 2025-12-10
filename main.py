# -*- coding: utf-8 -*-
import datetime
import multiprocessing
import random
import subprocess
import threading

import rumps

from sub.config import *
from sub.crawl import Crawl
from sub.insert import logger
from sub.server import Server

port = random.randint(18000, 19000)

off_check = False


class PomodoroApp(rumps.App):

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
        self.timer = rumps.Timer(self.crawl_wechat, 60)
        self.timer.start()
        self.app.menu = [
            self.crawl_button,
            self.server_button,
            self.open_button,
            self.backup_button,
        ]
        global port
        # 创建队列用于进程间通信
        self.queue = multiprocessing.Queue()
        self.ui_server = Server(port, self.queue)
        self.crawl = Crawl(self.queue)
        self.crawl_thread = None
        self.ui_server_thread = None

    def backup(self, sender):
        d = datetime.datetime.now()
        date = f"{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}"
        img = 'ccr.ccs.tencentyun.com/acejilam/ib-zblwujy5oa:5ad6464196a383d799c1787f60061471-8'
        cmd = (
            f'/usr/local/bin/docker run -d --rm -v /etc/hosts:/etc/hosts -v {bak_dir}:/data/ {img} bash -c "mysqldump -u {db_user} '
            f'--password={db_password} '
            f'-h {db_host} '
            f'-P {db_port} '
            f'{query_db} > /data/{date}-{query_db}.sql.pending ;'
            f'mv /data/{date}-{query_db}.sql.pending /data/{date}-{query_db}.sql'
            f'"')
        logger.info(cmd)
        out = subprocess.getoutput(cmd)
        self.send_message(f"backup {query_db}", out)

        cmd = (
            f'/usr/local/bin/docker run -d --rm -v /etc/hosts:/etc/hosts -v {bak_dir}:/data/ {img} bash -c "mysqldump -u {db_user} '
            f'--password={db_password} '
            f'-h {db_host} '
            f'-P {db_port} '
            f'{crawl_db} > /data/{date}-{crawl_db}.sql.pending ;'
            f'mv /data/{date}-{crawl_db}.sql.pending /data/{date}-{crawl_db}.sql'
            f'"')
        logger.info(cmd)
        out = subprocess.getoutput(cmd)
        self.send_message(f"backup {crawl_db}", out)

    def open(self, sender):
        self.ui_server.openChrome()

    def set_title(self, title):
        self.app.title = title

    def send_message(self, subtitle="", message=""):
        rumps.notification(
            icon="./bj.ico",
            title=self.app_name, subtitle=subtitle, message=message
        )

    def crawl_wechat(self, sender):
        self.crawl_button.state = not self.crawl_button.state
        if self.crawl_button.state:
            self.crawl_thread = threading.Thread(
                target=self.crawl.run,
                args=(self.call_back, self.set_title, self.send_message)
            )
            self.crawl_thread.start()
        else:
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

# -*- coding: utf-8 -*-
import json
import multiprocessing
import os
import random
import subprocess
import sys
import threading
import time
import datetime

from config import mysql_conf
from insert import mysql, logger
from sub.crawl import Crawl
from sub.server import app, Server
import rumps
from queue import Queue, Empty
import docker

recv_q = Queue(1000)
send_q = Queue(1000)
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
        self.skey = ""
        self.app_name = args[0]

        self.config = {
            "crawl": "开始爬虫: " + str(os.getpid()),
            "pause": "暂停爬虫",
            "init": "初始化",
            "server": "运行flask",
            "display": "显示页面",
            "entry": "录入KEY",
            "backup": "数据备份",
            "interval": 10
        }
        self.app = rumps.App("", icon="./bj.ico")
        self.interval = self.config["interval"]
        self.init_button = rumps.MenuItem(title=self.config["init"], callback=self.init)
        self.server_button = rumps.MenuItem(title=self.config["server"], callback=self.flask)
        self.crawl_button = rumps.MenuItem(title=self.config["crawl"], callback=self.crawl_wechat)
        self.open_button = rumps.MenuItem(title=self.config["display"], callback=self.open)
        self.entry_button = rumps.MenuItem(title=self.config["entry"], callback=self.enter_key)
        self.backup_button = rumps.MenuItem(title=self.config["backup"], callback=self.backup)
        self.after_hours_reminder = rumps.MenuItem(title='after_hours_reminder',
                                                   callback=self.after_hours_reminder_click)
        self.app.menu = [
            self.init_button,
            self.crawl_button,
            self.entry_button,
            self.server_button,
            self.open_button,
            self.backup_button,
            self.after_hours_reminder,
        ]
        global port
        self.ui_server = Server(port)
        self.crawl = Crawl()
        self.crawl_thread = None
        self.ui_server_thread = None

    def enter_key(self, sender):
        response = rumps.Window('录入KEY').run()
        if response.clicked:
            self.skey = response.text.strip()
            if self.skey == "":
                self.app.quit_button.click()
                sys.exit(0)
            self.send_message("key", self.skey)

    def after_hours_reminder_click(self, sender):
        os.system(
            f"open -a '/Applications/Google Chrome.app' http://127.0.0.1:{self.ui_server.port}/after_hours_reminder")
        global off_check
        self.after_hours_reminder.state = not self.after_hours_reminder.state
        off_check = self.after_hours_reminder.state
        logger.info(off_check)

    def backup(self, sender):
        d = datetime.datetime.now()
        with open(mysql_conf, 'r', encoding='utf8') as f:
            mysql_info = json.loads(f.read())

        cmd = (f'/usr/local/bin/docker run --rm -v /etc/hosts:/etc/hosts -v /Users/acejilam/Desktop:/data/ registry.cn-hangzhou.aliyuncs.com/acejilam/mysql bash -c "mysqldump -u {mysql_info["user"]} '
               f'--password={mysql_info["password"]} '
               f'-h {mysql_info["host"]} '
               f'-P {mysql_info["port"]} '
               f'{mysql_info["database"]} > /data/wechat-{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}.sql"')
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
        if self.skey == "":
            self.enter_key(None)
        self.crawl_button.state = not self.crawl_button.state
        if self.crawl_button.state:
            self.crawl_thread = threading.Thread(
                target=self.crawl.run,
                args=(self.skey, self.call_back, self.set_title, self.send_message, send_q, recv_q)
            )
            self.crawl_thread.start()
        else:
            self.crawl.need_crawl = not self.crawl.need_crawl
            self.app.title = ""

    def flask(self, obj):
        self.server_button.state = not self.server_button.state
        if self.server_button.state:
            # self.ui_server_thread = threading.Thread(
            self.ui_server_thread = multiprocessing.Process(
                target=self.ui_server.run,
            )
            self.ui_server_thread.start()
        else:
            self.ui_server_thread.terminate()

    def call_back(self):
        self.app.title = ""
        self.crawl_button.state = not self.crawl_button.state

    @rumps.timer(1)  # create a new thread that calls the decorated function every 4 seconds
    def display_alert(self):
        try:
            res = send_q.get_nowait()
            data = json.loads(res)
            rumps.alert(title=data['title'], message=data['message'])
            if data['title'] == '机器人识别':
                recv_q.put(json.dumps({"state": "ok"}))
            if data['title'] == '重新获取验证码':
                response = rumps.Window('录入KEY').run()
                if response.clicked:
                    if response.text == "":
                        sys.exit(0)
                    recv_q.put(json.dumps({'code': response.text.strip()}))
        except Empty:
            pass
        return

    @rumps.timer(1)
    def after_hours_reminder(self):
        global off_check
        from datetime import datetime, time
        # 定义起始和结束时间
        start_time = time(19, 00)
        end_time = time(20, 0)
        current_time = datetime.now().time()
        # 判断当前时间是否在指定时间段内
        if off_check and start_time <= current_time <= end_time:
            if current_time.second % 60 == 0:
                global port
                os.system(
                    f"open -a '/Applications/Google Chrome.app' http://127.0.0.1:{port}/after_hours_reminder")

    def run(self):
        self.app.run()


if __name__ == '__main__':
    PomodoroApp('微信公众号').run()

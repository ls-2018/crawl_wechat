# -*- coding: utf-8 -*-
import multiprocessing

from sub.crawl import Crawl
from sub.server import Server
from sub.db import Backup

off_check = False


class PomodoroApp:
    def __init__(self, *args, **kwargs):
        self.process = []
        # 创建队列用于进程间通信
        self.queue = multiprocessing.Queue(maxsize=100)
        self.ui_server = Server(self.queue)
        self.crawl = Crawl(self.queue)

        self.process.append(multiprocessing.Process(target=self.ui_server.run))
        self.process.append(multiprocessing.Process(target=self.crawl.run))

    def start(self):
        for process in self.process:
            process.start()
        for process in self.process:
            process.join()


if __name__ == '__main__':
    app = PomodoroApp()
    app.start()

import time

from sub.config import *
from sub.db import Backup
from sub.insert import mysql, clean, insert, ArticleItem


class Crawl:
    def __init__(self, queue=None):
        self.handled_count = 0
        self.count = 0
        self.lastFile = ''
        self.user_map = {}
        self.queue = queue
        self.backup = Backup()
        self.backup.load()

    def run(self):
        while True:
            time.sleep(60)
            self.timer()

    def timer(self):
        try:
            with mysql(db=crawl_db) as crawl_cursor:
                with mysql() as cursor:
                    user_map = {}
                    crawl_cursor.execute(
                        f"select fakeid,nickname from `{crawl_db}`.`{crawl_info_table}`")
                    for item in crawl_cursor.fetchall():
                        user_map[item['fakeid']] = item['nickname']
                    self.user_map = user_map
                    self.count = len(user_map)
                    self.handled_count = 0

                    links = self.get_link_cache()
                    need_insert = []
                    crawl_cursor.execute(
                        f"select * from `{crawl_db}`.`{crawl_article_table}`")
                    res = crawl_cursor.fetchall()
                    for item in res:
                        if item['is_deleted'] == 1:
                            continue
                        if item['link'] in links:
                            continue
                        need_insert.append(item)

                    for item in need_insert:
                        account_name = self.user_map.get(item['fakeid'], None)
                        if account_name is None:
                            continue
                        obj = ArticleItem(
                            aid=item['aid'],
                            fakeid=item['fakeid'],
                            account_name=account_name,
                            author_name=item['author_name'],
                            title=item['title'],
                            cover=item['cover'],
                            create_time=item['create_time'],
                            link=item['link'],
                            read_status=0,
                            favorite=0,
                        )
                        links.add(item['link'])
                        print("inserting...(%s/%s)" % (self.handled_count, len(need_insert)))
                        print(obj)
                        insert(cursor, obj)
                        self.handled_count += 1
                    if len(need_insert) > 0:
                        # 通过队列发送消息到服务器进程
                        if self.queue:
                            print(f"向队列发送消息: {len(need_insert)}")
                            self.queue.put(len(need_insert))
                        self.backup.backup()

                    clean()
        except Exception as e:
            print(e)

    @staticmethod
    def get_link_cache():
        links = set()
        with mysql() as cursor:
            cursor.execute(f'select link from `{query_db}`.`{query_table}`')
            for item in cursor.fetchall():
                links.add(item['link'])
        return links

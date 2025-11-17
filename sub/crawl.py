import json
import os

from sub.config import config_path, link_cache, mysql_conf, crawl_info_table, crawl_article_table
from sub.insert import mysql, clean, insert, ArticleItem
from sub.log import get_logger

logger = get_logger()


class Crawl:
    def __init__(self):
        self.handled_count = 0
        self.count = 0
        self.set_title = None
        self.lastFile = ''
        self.user_map = {}
        with open(mysql_conf, 'r', encoding='utf8') as f:
            self.mysql_info = json.loads(f.read())

        try:
            os.mkdir(config_path)
        except FileExistsError:
            pass
        except Exception as e:
            logger.error(e)
            pass

    def run(self, callback, set_title, send_message):
        try:
            with mysql(db=self.mysql_info['crawl_db']) as crawl_cursor:
                with mysql() as cursor:
                    self.set_title = set_title
                    user_map = {}
                    crawl_cursor.execute(
                        f"select fakeid,nickname from `{self.mysql_info['crawl_db']}`.`{crawl_info_table}`")
                    for item in crawl_cursor.fetchall():
                        user_map[item['fakeid']] = item['nickname']
                    self.user_map = user_map
                    self.count = len(user_map)
                    self.handled_count = 0

                    links = self.get_link_cache()
                    need_insert = []
                    crawl_cursor.execute(
                        f"select * from `{self.mysql_info['crawl_db']}`.`{crawl_article_table}`")
                    res = crawl_cursor.fetchall()
                    for item in res:
                        if item['is_deleted']== 1:
                            continue
                        if item['link'] in links:
                            continue
                        need_insert.append(item)

                    for item in need_insert:
                        if self.set_title:
                            self.set_title("inserting...(%s/%s)" % (self.handled_count, len(need_insert)))
                        obj = ArticleItem(
                            aid=item['aid'],
                            fakeid=item['fakeid'],
                            account_name=self.user_map[item['fakeid']],
                            author_name=item['author_name'],
                            title=item['title'],
                            cover=item['cover'],
                            create_time=item['create_time'],
                            link=item['link'],
                            read_status=0,
                            favorite=0,
                        )
                        links.add(item['link'])
                        logger.info("inserting...(%s/%s)" % (self.handled_count, len(need_insert)))
                        logger.info(obj)
                        insert(cursor, obj)
                        self.handled_count += 1
                    self.save_link_cache(links)
                    if callback:
                        callback()
                    send_message("sync", "over")
                    clean()
        except Exception as e:
            logger.error(e)
            send_message("error", e)

    @staticmethod
    def get_link_cache():
        links = set()
        with mysql() as cursor:
            if os.path.exists(link_cache):
                with open(link_cache, 'r', encoding='utf-8') as f:
                    links = set(json.loads(f.read()))
            else:
                cursor.execute('select link from `wechat`.`article_info`')
                for item in cursor.fetchall():
                    links.add(item['link'])
        return links

    @staticmethod
    def save_link_cache(data: set):
        with open(link_cache, 'w', encoding='utf-8') as f:
            ll = list(data)
            ll.sort()
            f.write(json.dumps(ll, ensure_ascii=False, indent=4))

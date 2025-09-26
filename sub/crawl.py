import json
import os

from sub.config import config_path, download_path, link_cache
from sub.insert import mysql, clean, insert, ArticleItem
from sub.log import get_logger

logger = get_logger()


class Crawl:
    def __init__(self, ):
        self.handled_count = 0
        self.count = 0
        self.set_title = None
        self.lastFile = ''
        self.user_map = {}

        try:
            os.mkdir(config_path)
        except FileExistsError:
            pass
        except Exception as e:
            logger.error(e)
            pass

    def run(self, callback, set_title, send_message):
        try:
            with mysql() as cursor:
                self.set_title = set_title
                lastFile = ""
                lastTime = 0
                for file in os.listdir(download_path):
                    if file.startswith('exporter.wxdown.online'):
                        if os.stat(os.path.join(download_path, file)).st_ctime > lastTime:
                            lastFile = os.path.join(download_path, file)
                            lastTime = os.stat(lastFile).st_ctime

                self.lastFile = lastFile
                if self.lastFile == "":
                    send_message("error", "file 不存在")
                    if callback:
                        callback()
                    return
                logger.info("last file is {}".format(lastFile))
                user_map = {}
                with open(lastFile, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data['info']:
                        user_map[item['fakeid']] = item['nickname']
                self.user_map = user_map
                self.count = len(user_map)
                self.handled_count = 0

                links = self.get_link_cache()
                need_insert = []
                for item in data["article"]:
                    if item.get('is_deleted', False):
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

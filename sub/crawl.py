from sub.config import *
from sub.insert import mysql, clean, insert, ArticleItem
from sub.log import get_logger

logger = get_logger()


class Crawl:
    def __init__(self, queue=None):
        self.handled_count = 0
        self.count = 0
        self.set_title = None
        self.lastFile = ''
        self.user_map = {}
        self.queue = queue

    def run(self, callback, set_title, send_message):
        try:
            with mysql(db=crawl_db) as crawl_cursor:
                with mysql() as cursor:
                    self.set_title = set_title
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
                        if self.set_title:
                            self.set_title("inserting...(%s/%s)" % (self.handled_count, len(need_insert)))
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
                        logger.info("inserting...(%s/%s)" % (self.handled_count, len(need_insert)))
                        logger.info(obj)
                        insert(cursor, obj)
                        self.handled_count += 1
                    # self.save_link_cache(links)
                    if callback:
                        callback()
                    if len(need_insert) > 0:
                        send_message("Sync", f"新增{len(need_insert)}条数据")
                        # 通过队列发送消息到服务器进程
                        if self.queue:
                            logger.debug(f"向队列发送消息: {len(need_insert)}")
                            self.queue.put(len(need_insert))
                    clean()
        except Exception as e:
            logger.error(e)
            send_message("error", e)

    @staticmethod
    def get_link_cache():
        links = set()
        with mysql() as cursor:
            # if os.path.exists(link_cache):
            #     with open(link_cache, 'r', encoding='utf-8') as f:
            #         links = set(json.loads(f.read()))
            # else:
            cursor.execute(f'select link from `{query_db}`.`{query_table}`')
            for item in cursor.fetchall():
                links.add(item['link'])
        return links

    # @staticmethod
    # def save_link_cache(data: set):
    #     with open(link_cache, 'w', encoding='utf-8') as f:
    #         ll = list(data)
    #         ll.sort()
    #         f.write(json.dumps(ll, ensure_ascii=False, indent=4))

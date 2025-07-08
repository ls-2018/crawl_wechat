import datetime
import json
import os
import platform
import random
import time
from queue import Queue

import requests
import urllib3

from config import config_path, wechat_conf
from insert import mysql, clean
from sub.log import get_logger

logger = get_logger()

os.system('pip3 uninstall urllib3-secure-extra')
urllib3.disable_warnings()


class CrawlItem:
    def __init__(self, account_id=None, account_name=None, crawl_time=0):
        self.account_id = account_id
        self.account_name = account_name
        self.crawl_time = crawl_time


class ArticleItem:
    def __init__(
            self,
            account_id, account_name, review_id, type, title, avatar, time, pic_url, doc_url, author, read_status,
            favorite
    ):
        self.account_id = account_id
        self.account_name = account_name
        self.review_id = review_id
        self.type = type
        self.title = title
        self.avatar = avatar
        self.time = time
        self.pic_url = pic_url
        self.doc_url = doc_url
        self.author = author
        self.avatar = avatar
        self.read_status = read_status
        self.favorite = favorite

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False)


class Crawl:
    def __init__(self, ):
        self.send_q: Queue = None
        self.recv_q: Queue = None
        self.handled_count = 0
        self.count = 0
        self.set_title = None
        self.need_crawl = True
        try:
            os.mkdir(config_path)
        except FileExistsError:
            pass
        except Exception as e:
            logger.error(e)
            pass
        if os.path.exists(wechat_conf):
            with open(wechat_conf, "r", encoding='utf8') as f:
                self.headers = json.loads(f.read())
            return
        self.headers = {
            "Host": "i.weread.qq.com",
            "accept": "*/*",
            "channelid": "AppStore",
            "vid": "329107044",
            "basever": "9.3.1.37",
            "v": "9.3.1.37",
            "skey": "WTxaXfsL",
            "user-agent": "WeRead/9.3.1 (iPad; iOS 18.5; Scale/2.00)",
            "accept-language": "zh-Hans-CN;q=1",
        }
        if 'arm' in platform.platform().lower():
            self.headers = {
                "Host": "i.weread.qq.com",
                "accept": "*/*",
                "channelid": "AppStore",
                "vid": "329107044",
                "basever": "9.3.1.37",
                "v": "9.3.1.37",
                "skey": "WTxaXfsL",
                "user-agent": "WeRead/9.3.1 (iPad; iOS 18.5; Scale/2.00)",
                "accept-language": "zh-Hans-CN;q=1",
            }

        with open(wechat_conf, "w", encoding='utf8') as f:
            f.write(json.dumps(self.headers, ensure_ascii=False, indent=4))

    @staticmethod
    def last_crawl_time():
        # 获取当前时间
        now = datetime.datetime.now()
        # 计算昨天的日期
        yesterday = now - datetime.timedelta(days=1)
        # 设置时间为晚上12点
        yesterday_at_midnight = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        # 转换为时间戳
        timestamp = int(time.mktime(yesterday_at_midnight.timetuple()))
        return timestamp

    @staticmethod
    def need_to_crawl():
        with mysql() as cursor:
            cursor.execute("select * from crawl_time order by crawl_time ASC ")
            res = cursor.fetchall()
            return [CrawlItem(**item) for item in res]

    def run(self, key, callback, set_title, send_message, send_q, recv_q):
        self.send_q = send_q
        self.recv_q = recv_q
        self.set_title = set_title
        if len(key) == 0:
            if send_message:
                send_message(subtitle="key is null", message="")
            return
        else:
            self.headers['skey'] = key
        self.count = len(self.need_to_crawl())
        self.handled_count = 0
        for item in self.need_to_crawl():
            if not self.need_crawl:  # toggle
                return
            if self.set_title:
                self.set_title("%s/%s %s" % (self.handled_count, self.count, item.account_name))
            logger.info("%s/%s %s" % (self.handled_count, self.count, item.account_name))
            try:
                self.crawl(item)
                s = 5 + random.randint(5, 10)
                for i in range(s):
                    if self.set_title:
                        self.set_title("%s/%s %s,sleep:%d" % (self.handled_count, self.count, item.account_name, s - i))
                    time.sleep(1)
            except Exception as e:
                logger.error(e)
                if self.set_title:
                    self.set_title("")
                self.send_q.put(json.dumps({'title': item.account_name, 'message': str(e)}))
                break
            self.handled_count += 1
        if callback:
            callback()
        clean()

    @staticmethod
    def already_exists(account: CrawlItem):
        with mysql() as cursor:
            cursor.execute("select review_id from article_info where account_id = %s", [account.account_id, ])
            res = [item['review_id'] for item in cursor.fetchall()]
            return set(res)

    def crawl(self, account: CrawlItem):
        already_data = self.already_exists(account)
        offset = 0
        all_count = 0
        insert_data = []
        for i in range(1000):
            if not self.need_crawl:
                return
            params = {
                "bookId": account.account_id,
                "count": "20",
                "offset": str(offset),
                "synckey": str(int(time.time())),
                # "version": "2"
            }
            url = "https://i.weread.qq.com/book/articles"

            res = requests.get(
                url,
                headers=self.headers,
                params=params,
            )
            data = res.json()
            if data.get('reviews', None) is None and 'err' in json.dumps(data, ensure_ascii=False):
                logger.info("%s %s %s" % (account.account_id, account.account_name, data))
                if data['errcode'] == -2041:  # 人工识别
                    self.send_q.put(
                        json.dumps({'title': '机器人识别', 'message': json.dumps(data, ensure_ascii=False)})
                    )
                    if self.set_title:
                        self.set_title("机器人识别")
                    print(self.recv_q.get(block=True))
                    continue
                if data['errcode'] == -2012:  # 重新获取验证码
                    self.send_q.put(
                        json.dumps({'title': '重新获取验证码', 'message': json.dumps(data, ensure_ascii=False)})
                    )
                    if self.set_title:
                        self.set_title("重新获取验证码")
                    self.headers['skey'] = json.loads(self.recv_q.get(block=True))['code']
                    continue
                else:
                    raise Exception(json.dumps(data, ensure_ascii=False))
            if len(data.get("reviews", [])) == 0:
                break
            offset += len(data.get("reviews", []))
            if self.set_title:
                self.set_title("%s/%s %s(%d)" % (self.handled_count, self.count, account.account_name, offset))
            non_new_count = 0
            for item in data.get("reviews", []):
                review_id = item['review']['mpInfo']['originalId']
                if review_id in already_data:
                    non_new_count += 1
                else:
                    insert_data.append(ArticleItem(
                        account_id=account.account_id,
                        account_name=account.account_name,
                        review_id=review_id,
                        type=item['review']['type'],
                        title=item['review']['mpInfo']['title'],
                        avatar=item['review']['mpInfo']['avatar'],
                        time=item['review']['mpInfo']['time'],
                        pic_url=item['review']['mpInfo']['pic_url'],
                        doc_url=item['review']['mpInfo']['doc_url'],
                        author=item['review']['mpInfo']['mp_name'],
                        read_status=False,
                        favorite=False
                    ))
            sl = 5 + random.randint(1, 10)
            logger.info("爬取页数:%s 当前页文章数%s %s " % (i, len(data.get("reviews", [])), 'sleep:%d' % sl))
            all_count += len(data.get("reviews", [])) - non_new_count
            if non_new_count != 0:
                break
            for j in range(sl):
                if self.set_title:
                    self.set_title(
                        "%s/%s %s(%d) sleep:%d" % (self.handled_count, self.count, account.account_name, offset, sl - j)
                    )
                time.sleep(1)
        for item in insert_data:
            logger.info(item)
            self.insert_article(item)
        self.update_crawl_time(account)

    @staticmethod
    def insert_article(param: ArticleItem):
        with mysql() as cursor:
            cursor.execute(
                r"INSERT INTO `wechat`.`article_info` ( `account_id`,`account_name`, `review_id`, `type`, `title`, "
                r"`avatar`, `time`,`pic_url`, `doc_url`, `author`, `read_status`, `favorite`) VALUES ("
                r"%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",
                args=(
                    param.account_id,
                    param.account_name,
                    param.review_id,
                    param.type,
                    param.title,
                    param.avatar,
                    param.time,
                    param.pic_url,
                    param.doc_url,
                    param.author,
                    param.read_status,
                    param.favorite,
                )
            )

    @staticmethod
    def update_crawl_time(param: CrawlItem):
        with mysql() as cursor:
            cursor.execute(
                r"update `wechat`.`crawl_time` set `crawl_time` = %s where `account_id` = %s;",
                args=(int(time.time()), param.account_id,)
            )


if __name__ == '__main__':
    Crawl().run('UGFzJqnc', None, None, None, Queue(10000), Queue(10000))

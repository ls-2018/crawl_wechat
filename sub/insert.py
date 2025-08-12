import contextlib
import json
import time
from collections import defaultdict

import pymysql
import pymysql.cursors

from .config import mysql_conf
from sub.log import get_logger

logger = get_logger()

with open(mysql_conf, 'r', encoding='utf8') as f:
    mysql_info = json.loads(f.read())


# 定义上下文管理器，连接后自动关闭连接
@contextlib.contextmanager
def mysql(
        host=mysql_info['host'],
        port=mysql_info['port'],
        user=mysql_info['user'],
        passwd=mysql_info['password'],
        db=mysql_info['database'],
        charset='utf8mb4'):
    conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset, autocommit=False,
                           write_timeout=60, connect_timeout=60, read_timeout=60)
    _cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    try:
        yield _cursor
    finally:
        conn.commit()
        _cursor.close()
        conn.close()


def exists(account, _id):
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute("select count(*) as count from article_info where id=%s and public_account=%s",
                       args=(_id, account))
        # row_count = cursor.execute("select * from stu")
        if cursor.fetchone().get("count") > 0:
            return True
    return False


def insert(account, data):
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        for i, item in enumerate(data):
            logger.info(i, len(data))
            try:
                if exists(account, item['comm_msg_info']['id']):
                    continue
                else:
                    if 'app_msg_ext_info' not in item:
                        continue
                    if item['app_msg_ext_info']['title'] == "":
                        for ref_item in item['app_msg_ext_info'].get('multi_app_msg_item_list', []):
                            cursor.execute(
                                r"INSERT INTO `wechat`.`ref`"
                                r" (`id`, `type`, `datetime`, `fakeid`, `status`,"
                                r" `title`, `digest`, `fileid`, `content_url`, `source_url`,"
                                r" `cover`,  `public_account`, `author`, `copyright_stat`, `del_flag`) VALUES "
                                "(%s,%s,%s,%s,%s,"
                                "%s,%s,%s,%s,%s,"
                                "%s,%s,%s,%s,%s);",
                                args=(
                                    item["comm_msg_info"]['id'],
                                    item["comm_msg_info"]['type'],
                                    item["comm_msg_info"]['datetime'],
                                    item["comm_msg_info"]['fakeid'],
                                    item["comm_msg_info"]['status'],
                                    ref_item['title'],
                                    ref_item['digest'],
                                    ref_item['fileid'],
                                    ref_item['content_url'],
                                    ref_item['source_url'],
                                    ref_item['cover'],
                                    account,
                                    ref_item['author'],
                                    ref_item.get('copyright_stat', None),
                                    ref_item.get('del_flag', 1),
                                )
                            )
                    else:
                        cursor.execute(
                            r"INSERT INTO `wechat`.`article_info`"
                            r" (`id`, `type`, `datetime`, `fakeid`, `status`,"
                            r" `title`, `digest`, `fileid`, `content_url`, `source_url`,"
                            r" `cover`, `subtype`,`public_account`, `author`, `copyright_stat`, `del_flag`) VALUES "
                            "(%s,%s,%s,%s,%s,"
                            "%s,%s,%s,%s,%s,"
                            "%s,%s,%s,%s,%s,%s);",
                            args=(
                                item["comm_msg_info"]['id'],
                                item["comm_msg_info"]['type'],
                                item["comm_msg_info"]['datetime'],
                                item["comm_msg_info"]['fakeid'],
                                item["comm_msg_info"]['status'],
                                item["app_msg_ext_info"]['title'],
                                item["app_msg_ext_info"]['digest'],
                                item["app_msg_ext_info"]['fileid'],
                                item["app_msg_ext_info"]['content_url'],
                                item["app_msg_ext_info"]['source_url'],
                                item["app_msg_ext_info"]['cover'],
                                item["app_msg_ext_info"]['subtype'],
                                account,
                                item["app_msg_ext_info"]['author'],
                                item["app_msg_ext_info"].get('copyright_stat', None),
                                item["app_msg_ext_info"].get('del_flag', 1),
                            )
                        )
            except Exception as e:
                logger.error(account)
                logger.error(e)
                return
    record_crawl_time(account)


def record_crawl_time(_account):
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute("select count(*) as count from `wechat`.`crawl_time` where account=%s", args=(_account,))
        # row_count = cursor.execute("select * from stu")
        if cursor.fetchone().get("count") > 0:
            cursor.execute("update `wechat`.`crawl_time` set time=%s where account=%s",
                           args=(int(time.time()), _account,))
            return
        cursor.execute("INSERT INTO `wechat`.`crawl_time` (`account`, `time`) VALUES (%s,%s)",
                       args=(_account, int(time.time())))


def get_old_crawl_account():
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        res = []
        cursor.execute("select account,`time` from `wechat`.`crawl_time` where `time`=0 ")
        for item in cursor.fetchall():
            res.append(item['account'])
        return res


def clean():
    x = defaultdict(list)
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute("select * from article_info order by `time` desc;")
        for item in cursor.fetchall():
            item['title'] = item['title'].replace('\xa0', ' ')
            x[item['title'].lower()].append(item)

        for k, vs in x.items():
            vs = sorted(vs, key=lambda _x: _x['time'])
            if len(vs) > 1:
                fav = False
                read = False
                for item in vs:
                    if item['favorite'] == 1:
                        fav = True
                    if item['read_status'] == 1:
                        read = True
                if fav or read:
                    for item in vs:
                        if item['read_status'] == 1:
                            continue
                        cursor.execute(
                            "update `wechat`.`article_info` set read_status=1 where `account_id`=%s and review_id=%s",
                            args=(item['account_id'], item['review_id'])
                        )
                        logger.info(item)
                else:
                    for item in vs[1:]:
                        cursor.execute(
                            "update `wechat`.`article_info` set read_status=1 where `account_id`=%s and review_id=%s",
                            args=(item['account_id'], item['review_id'])
                        )
                        logger.info(item)


if __name__ == '__main__':
    clean()

import contextlib
from collections import defaultdict

import pymysql
import pymysql.cursors

from sub.config import *
from sub.log import get_logger

logger = get_logger()


# 定义上下文管理器，连接后自动关闭连接
@contextlib.contextmanager
def mysql(
        host=db_host,
        port=db_port,
        user=db_user,
        passwd=db_password,
        db=query_db,
        charset=db_charset
):
    conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset, autocommit=True,
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
        cursor.execute(f"select count(*) as count from `{query_db}`.`{query_table}` where id=%s and public_account=%s",
                       args=(_id, account))
        # row_count = cursor.execute("select * from stu")
        if cursor.fetchone().get("count") > 0:
            return True
    return False


class ArticleItem:
    def __init__(
            self,
            aid, fakeid, account_name, author_name, title, create_time, link, cover, read_status, favorite
    ):
        self.aid = aid
        self.fakeid = fakeid
        self.account_name = account_name
        self.author_name = author_name
        self.title = title
        self.create_time = create_time
        self.cover = cover
        self.link = link
        self.read_status = read_status
        self.favorite = favorite

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False)


def insert(cursor: pymysql.cursors.DictCursor, obj: ArticleItem):
    # with mysql() as cursor:  # type: pymysql.cursors.DictCursor
    cursor.execute(
        f"INSERT INTO `{query_db}`.`{query_table}` ( `aid`,`fakeid`, `account_name`, `author_name`, `title`, "
        r"`create_time`, `link`,`read_status`, `favorite`,`cover`) VALUES ("
        r"%s,%s,%s,%s,%s,"
        r"%s,%s,%s,%s,%s);",
        args=(
            obj.aid, obj.fakeid, obj.account_name, obj.author_name, obj.title,
            obj.create_time, obj.link, obj.read_status, obj.favorite, obj.cover
        )
    )


def clean():
    x = defaultdict(list)
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute(f"select * from `{query_db}`.`{query_table}` order by `create_time` desc;")
        for item in cursor.fetchall():
            # item['title'] = item['title'].replace('\xa0', ' ')
            x[item['title'].lower()].append(item)

        for k, vs in x.items():
            vs = sorted(vs, key=lambda _x: _x['create_time'])
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
                            f"update `{query_db}`.`{query_table}` set read_status=1 where id=%s",
                            args=(item['id'],)
                        )
                else:
                    for item in vs[1:]:
                        cursor.execute(
                            f"update `{query_db}`.`{query_table}` set read_status=1 where id=%s",
                            args=(item['id'],)
                        )


if __name__ == '__main__':
    clean()

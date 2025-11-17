import copy
import os.path
import time

from flask import Flask, request, render_template
from flask_cors import CORS

from sub.config import *
from sub.insert import mysql
from sub.log import get_logger

logger = get_logger()

TEMPLATE = {
    "status": 200,
    "message": "",
    "total": 0,
    "rows": {
        "item": []
    }
}

app = Flask(
    "wechat",
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
)

app.logger = get_logger()
CORS(app, resources={
    r'*': {'origins': '*', 'methods': 'GET', 'allow_headers': 'Content-Type', 'supports_credentials': True}})

port = 0

remote_addr = '127.0.0.1'


@app.route('/')
def index():
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute(f"select account_name from `{query_db}`.`{query_table}` group by account_name;")
        user = [item["account_name"] for item in cursor.fetchall()]

    content = {
        'user': user,
        "port": port,
        'addr': '127.0.0.1',
    }
    if request.remote_addr != remote_addr:
        content['addr'] = request.host.split(':')[0]
    return render_template("index.html", **content)


@app.route('/data')
def data():
    b = copy.deepcopy(TEMPLATE)
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    if request.remote_addr != remote_addr and limit > 200:
        limit = 200
    offset = (page - 1) * limit
    xxx = 'where'
    args = []
    search = request.args.get('search', '')
    if search != "":
        if xxx != 'where':
            xxx += 'and'
        xxx += ' LOWER(title) like LOWER(%s)'
        args.append('%' + search.lower() + '%')

    fav = request.args.get('fav', 'N')

    if fav != 'ALL':
        if xxx != 'where':
            xxx += 'and'

        xxx += ' favorite = %s '
        if fav == 'N':
            args.append(0)
        else:
            args.append(1)

    read = request.args.get('read', 'N')

    if read != 'ALL':
        if xxx != 'where':
            xxx += 'and'
        xxx += '  read_status = %s '
        if read == 'N':
            args.append(0)
        else:
            args.append(1)

    accounts = json.loads(request.args.get('account', "[]"))
    if len(accounts) > 0:
        if xxx != 'where':
            xxx += 'and'
        xxx += ' account_name in %s '
        args.append(accounts)

    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        if xxx == 'where':
            xxx = ''
        cursor.execute(
            f"select count(*) as count from `{query_db}`.`{query_table}` {xxx}  order by `create_time` desc", args=args
        )
        res = cursor.fetchone()
        b['total'] = res['count']

        asd = args
        asd.append(limit)
        asd.append(offset)
        cursor.execute(
            f"select * from `{query_db}`.`{query_table}`  {xxx} order by `create_time` desc limit %s offset %s ", args=asd
        )
        res = cursor.fetchall()
        b['rows']["item"] = res
        for i, _ in enumerate(res):
            res[i]['num'] = i
    return json.dumps(b, ensure_ascii=False, indent=4)


@app.route("/fav-status/up/<_id>", methods=['POST'])
def favstatusup(_id):
    if request.remote_addr != remote_addr:
        return 'ok'
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute(f"update `{query_db}`.`{query_table}` set favorite=1 where id=%s", args=(_id,))
    return "ok"


@app.route("/fav-status/down/<_id>", methods=['POST'])
def favstatusdown(_id):
    if request.remote_addr != remote_addr:
        return 'ok'
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute(f"update `{query_db}`.`{query_table}` set favorite=0 where id=%s", args=(_id,))
    return "ok"


@app.route("/read-status/up/<_id>", methods=['POST'])
def readstatusup(_id):
    if request.remote_addr != remote_addr:
        return 'ok'
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute(f"update `{query_db}`.`{query_table}` set read_status=1 where id=%s", args=(_id,))
    return "ok"


@app.route("/read-status/down/<_id>", methods=['POST'])
def readstatusdown(_id):
    if request.remote_addr != remote_addr:
        return 'ok'
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        cursor.execute(f"update `{query_db}`.`{query_table}` set read_status=0 where id=%s", args=(_id,)
                       )
    return "ok"


class Server:
    def run(self):
        global port
        port = self.port
        app.run("0.0.0.0", self.port, debug=False)
        time.sleep(10)

    def __init__(self, port):
        self.port = port

    def openChrome(self):
        os.system(f'open -a "/Applications/Google Chrome.app" http://127.0.0.1:{self.port}')


if __name__ == '__main__':
    port = 18888
    app.run("0.0.0.0", 18888, debug=True)

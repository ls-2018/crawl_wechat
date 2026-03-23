import copy
import os.path
import threading
import time

from flask import Flask, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from sub.config import *
from sub.insert import mysql

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

CORS(app, resources={
    r'*': {'origins': '*', 'methods': 'GET', 'allow_headers': 'Content-Type', 'supports_credentials': True}})

# 初始化SocketIO，显式指定异步模式为threading
ws = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

remote_addr = os.getenv('REMOTE_ADDR')


# WebSocket事件处理
@ws.on('connect')
def handle_connect():
    print('Client connected')
    emit('server_response', {'data': 'Connected'}, broadcast=True)


@ws.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# 发送消息给所有客户端的函数
def send_websocket_message(data):
    print(f"websocket message: {data}")
    ws.emit('sync_data', data)


# 公开函数供外部调用
def notify_ui_sync(count):
    send_websocket_message({'message': f'新增{count}条数据', 'action': 'refresh'})


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
    import json
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
            f"select * from `{query_db}`.`{query_table}`  {xxx} order by `create_time` desc limit %s offset %s ",
            args=asd
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

        # Start queue listener in a background thread
        listener = threading.Thread(target=self.listen_queue, daemon=True)
        listener.start()

        ws.run(app, host="0.0.0.0", port=self.port, debug=False, allow_unsafe_werkzeug=True)

    def __init__(self, queue=None):
        self.port = 13001
        self.queue = queue

    def listen_queue(self):
        """监听队列中的消息并发送WebSocket通知"""
        print("开始监听队列")
        while True:
            try:
                # 阻塞等待队列中的消息
                count = self.queue.get()
                print(f"从队列接收到消息: {count}")
                # 发送WebSocket通知
                send_websocket_message({'message': f'新增{count}条数据', 'action': 'refresh'})
            except Exception as e:
                print(f"处理队列消息时出错: {e}")
                time.sleep(1)  # 出错后暂停1秒再继续

    def openChrome(self):
        os.system(f'open -a "/Applications/Chromium.app" http://127.0.0.1:{self.port}')


if __name__ == '__main__':
    port = 13001
    ws.run(app, "0.0.0.0", 13001, debug=True, allow_unsafe_werkzeug=True)

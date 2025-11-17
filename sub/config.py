import json
import os.path

_config_path = '/Volumes/Tf/config/wechat'

try:
    os.mkdir(_config_path)
except FileExistsError:
    pass
except Exception as e:
    print(e)
    pass

_mysql_conf = os.path.join(_config_path, "mysql.json")

with open(_mysql_conf, 'r', encoding='utf8') as f:
    _mysql_info = json.loads(f.read())

db_host = _mysql_info["host"]
db_port = _mysql_info["port"]
db_user = _mysql_info["user"]
db_password = _mysql_info["password"]
db_charset = _mysql_info["charset"]

query_db = _mysql_info["query_db"]
query_table = _mysql_info["query_table"]

crawl_db = _mysql_info["crawl_db"]
crawl_article_table = _mysql_info["crawl_article_table"]
crawl_info_table = _mysql_info["crawl_info_table"]

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

_cfg_conf = os.path.join(_config_path, "cfg.json")

with open(_cfg_conf, 'r', encoding='utf8') as f:
    _cfg_info = json.loads(f.read())

db_host = _cfg_info["host"]
db_port = _cfg_info["port"]
db_user = _cfg_info["user"]
db_password = _cfg_info["password"]
db_charset = _cfg_info["charset"]

query_db = _cfg_info["query_db"]
query_table = _cfg_info["query_table"]

crawl_db = _cfg_info["crawl_db"]
crawl_article_table = _cfg_info["crawl_article_table"]
crawl_info_table = _cfg_info["crawl_info_table"]

bak_dir=_cfg_info["bak_dir"]

import os.path
from dotenv import load_dotenv
load_dotenv()

db_host = os.getenv("DB_HOST", 'wechat-mysql')
db_port =  int(os.getenv("DB_PORT", '3306'))
db_user = 'root'
db_password = os.getenv('DB_PASSWORD', '')
db_charset = 'utf8mb4'

query_db = os.getenv("QUERY_DB", 'wechat_query')
query_table = os.getenv("QUERY_TABLE", 'article_info')

crawl_db = os.getenv("CRAWL_DB", 'wechat_article_exporter')
crawl_article_table = os.getenv("CRAWL_ARTICLE_TABLE", 'articles')
crawl_info_table = os.getenv("CRAWL_INFO_TABLE", 'info')

data_path = os.getenv("DATA_PATH", '')
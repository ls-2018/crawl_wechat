# 微信公众号文章爬取与管理系统

本项目旨在实现对微信公众号文章的自动化爬取、存储与管理，并提供可视化的Web界面进行数据浏览和操作。

## 主要功能

- **自动化爬虫**：通过模拟请求，自动批量抓取指定微信公众号的文章信息。
- **数据存储**：将抓取到的文章、账号等信息存入本地MySQL数据库，支持断点续爬。
- **Web管理界面**：基于Flask实现的前端页面，支持文章的筛选、收藏、已读标记等操作。
- **备份与提醒**：支持数据备份、下班提醒等实用功能。
- **跨平台支持**：支持Mac平台的菜单栏应用集成。
- **优化爬虫**：使用 https://github.com/ls-2018/wechat-article-exporter

## 系统架构

- `main.py`：主入口，集成爬虫、Web服务、菜单栏应用等功能。
- `sub/crawl.py`：爬虫核心逻辑，实现文章抓取、断点续爬、异常处理等。
- `sub/server.py`：Web服务，提供数据接口和前端页面。
- `insert.py`：数据库操作相关。
- `images/`：项目相关的界面截图或示意图。

## 部分界面预览

![公众号管理](images/accounts.png)

![文章列表](images/articles.png)

![菜单栏](images/menu.png)

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 启动MySQL服务（可用docker，详见main.py自动化部分）
3. 运行主程序：`python main.py`
4. 访问Web界面或使用菜单栏应用进行操作

## 打包
- python3 setup.py py2app -O2
---

## 配置
```

{
    "host":"wechat",
    "port":18889,
    "user":"root",
    "password":"",
    "database":"wechat",
    "charset":"utf8mb4"
}

需要再运行开始，抓包获取

```

## 一键启动
```
#! /usr/bin/env zsh
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE:-$0}")" && pwd)"
source "$SCRIPT_DIR/.alias.sh"

dataDir="/Users/acejilam/Documents/wechat"

# dataDir="/Volumes/Tf/data/wechat"

dataPath=$dataDir/wechat-mysql
exporterPath=$dataDir/wechat-article-exporter

mkdir -p $dataPath
mkdir -p $exporterPath

docker rm wechat-article-exporter -f
docker rm wechat-mysql -f
docker network rm wechat
docker network create wechat

cat >$dataPath/my.cnf <<EOF
[mysqld]
host-cache-size=0
skip-name-resolve
binlog_expire_logs_seconds = 10
datadir=/etc/mysql/data/
socket=/var/run/mysqld/mysqld.sock
secure-file-priv=/var/lib/mysql-files
lower_case_table_names=1
user=mysql
pid-file=/var/run/mysqld/mysqld.pid
[client]
socket=/var/run/mysqld/mysqld.sock
!includedir /etc/mysql/conf.d/
EOF

docker run \
	-d \
	-p 13306:3306 \
	--name wechat-mysql \
	--label com.docker.compose.project=wechat \
	--network wechat \
	--restart=always \
	-e MYSQL_ROOT_PASSWORD=sk3RCBqtWxF2Tg4pawUv \
	-e MYSQL_LOG_BIN=OFF \
	-v $dataPath/my.cnf:/etc/my.cnf \
	-v $dataPath/data:/etc/mysql/data/ \
	-v $dataPath/conf:/etc/mysql/mysql.conf.d/ \
	$(trans_image_name.py docker.io/library/mysql:8)

docker pull ccr.ccs.tencentyun.com/ls-2018/wechat-article-exporter

docker run \
	--name wechat-article-exporter \
	--restart=always \
	--label com.docker.compose.project=wechat \
	--network wechat \
	-d \
	-e MYSQL_HOST=$(python3 -c'from print_proxy import *;print(get_ip())') \
	-e MYSQL_PORT=13306 \
	-e MYSQL_LOG_BIN=OFF \
	-e MYSQL_USER=root \
	-e MYSQL_PASSWORD=sk3RCBqtWxF2TgpawUv \
	-e MYSQL_DATABASE=wechat_article_exporter \
	-p 13000:3000 \
	-v $exporterPath:/app/.data \
	ccr.ccs.tencentyun.com/ls-2018/wechat-article-exporter

pkill -9 'Chromium'
sleep 2
open -a "/Applications/Chromium.app" "http://localhost:13000"

cat /tmp/wechat.log | awk -F ' ' '{print $10}' | grep '\.' | grep -v '\.\.' | sort -nr | uniq -c

# SHOW BINARY LOGS;
# PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 1 MINUTE);
```

如有问题请联系作者。

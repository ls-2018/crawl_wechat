# update `wechat`.`article_info` set read_status=0 where true ;
import json

import pymysql
import pymysql.cursors

from sub.config import *
from sub.insert import mysql

# update `wechat`.`article_info` set read_status=1 where lower(title) like "%规划%";
keys = [" ui ", ".net", "1024", "12306", "96w", "ai", "aigc", "android", "ansible", "apipost", "apollo", "aws", "c#",
        "c++", "centos", "ceph", "chatgpt", "cka", "cks", "clickhouse", "cnn", "dbms", "debian", "devops", "dockerfile",
        "dpdk", "drbd", "druid", "dubbo", "elasticsearch", "elk", "epoll", "ffmpeg", "fiber", "flink", "fluxflatmap",
        "fpga", "github", "gpt", "hadoop", "hikari", "hr ", "idc", "idea", "ios", "iphone", "ipv4", "java", "jdk",
        "jenkins", "jmeter", "jvm", "kafka", "kafka", "kisflow", "kubebuilder", "kvm", "leader", "llm", "lvm",
        "mybatis", "mysql", "nacos", "nasa", "navicat", "netty", "nginx", "nodejs", "offer", "offer",
        "openapi", "openmandriva", "openstack", "oracle", "orca", "php", "pmp", "podman", "polaris", "postgresql",
        "postman", "prometheus", "promql", "python", "pytorch", "qt", "quic", "rabbit", "redis", "rocketmq", "rocky",
        "ruby", "rust", "sealos", "semantic", "serverless", "shell", "skywalking", "sofa", "sora", "spring", "sql",
        "sql server", "stntinel", "storm", "thinkbook", "thrift", "tidb", "tiobe", "turbo", "ubuntu", "virtio",
        "vmware", "vscode", "vue", "weave", "web", "webassem", "websocket", "windows", "zabbix", "zookeeper", "上海",
        "中学生", "中年", "中标", "主板", "之父", "互联网", "交换机", "亿", "会议", "低代码", "作息", "倒计时", "元宵",
        "入局", "八股文", "公司", "公布", "公益编程操练", "冠军", "分库", "分表", "创业", "删", "前端", "剪辑", "北京",
        "北漂", "协议栈", "可视化", "后期", "后端", "四川", "回放", "回顾", "团队", "基金", "外包", "大会", "大模型",
        "央企", "安全", "安卓", "实习", "宣布", "封杀", "小程序", "峰会", "年薪", "幻兽", "微信", "德国", "心理",
        "成都", "战斗机", "手机", "打工", "报名", "报名", "报告", "挤进", "排行", "推送", "推送", "摄影", "播放",
        "播放", "操作系统", "支付宝", "数仓", "数据中心", "数据库", "数据湖", "旅行", "春招", "智能", "曝光", "机器人",
        "机房", "机房", "机房", "杭州站", "架构师", "校招", "榜单", "毕业", "汗", "注解", "流媒体", "浦发", "消息队列",
        "深圳", "湖仓", "漏洞", "火山", "爱奇艺", "独立", "生存", "电商", "电子书", "直播", "知识库", "研发效能",
        "破产", "破局", "秋招", "科学院", "程序员", "简历", "算法", "红黑树", "美元", "美女", "考研", "职级", "范式",
        "获奖", "落标", "补助", "裁", "西藏", "规划", "认证", "许可证", "论坛", "设计", "趋势", "路由器", "金融", "附",
        "难听", "预约", "风格", "飞机", "香港", "马云", "高德", "魔术", "鸿蒙", "麒麟"]


def export_invalid():
    res = {}
    with mysql() as cursor:  # type: pymysql.cursors.DictCursor
        for x in keys:
            key = f'%{x}%'
            sql = f"select * from `{query_db}`.`{query_table}` where lower(title) like %s and read_status = 0 and favorite = 0;"
            cursor.execute(sql, (key,))

            user = {}
            for item in cursor.fetchall():
                user[item['title']] = item['doc_url']
                # cursor.execute(
                #     "update `wechat`.`article_info` set read_status=1 where `account_id`=%s and review_id=%s",
                #     args=(item['account_id'], item['review_id'])
                # )
                # print(item)
                res[x] = user
    with open('clean.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=4))


if __name__ == '__main__':
    export_invalid()

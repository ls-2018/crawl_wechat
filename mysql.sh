docker rm $(docker ps -qa) -f
rm -rf /mysql
mkdir -p /mysql/data
mkdir -p /mysql/conf
mkdir -p /me

cat > /mysql/my.cnf << EOF
[mysqld]
host-cache-size=0
skip-name-resolve
datadir=/etc/mysql/data/
socket=/var/run/mysqld/mysqld.sock
secure-file-priv=/var/lib/mysql-files
user=mysql
pid-file=/var/run/mysqld/mysqld.pid
[client]
socket=/var/run/mysqld/mysqld.sock
!includedir /etc/mysql/conf.d/

EOF

docker run -p 18889:3306 --name wechat-mysql --restart=always -e MYSQL_ROOT_PASSWORD=- -v /me:/me -v /mysql/my.cnf:/etc/my.cnf -v /mysql/data:/etc/mysql/data/ -v /mysql/conf:/etc/mysql/mysql.conf.d/ -d registry.cn-hangzhou.aliyuncs.com/acejilam/mysql:8


FROM alpine/curl:8.17.0 AS curl
WORKDIR /root
RUN curl -o change_mirror.sh https://linuxmirrors.cn/main.sh


FROM ubuntu:24.04 AS ca
RUN apt update -y && apt-get install --download-only ca-certificates -y

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=ca /var/cache/apt/archives/*.deb /tmp/debs/
COPY --from=curl /root/change_mirror.sh .
RUN dpkg -i /tmp/debs/*.deb && rm -rf /tmp/debs

RUN bash change_mirror.sh \
  --source mirrors.aliyun.com \
  --protocol https \
  --use-intranet-source false \
  --install-epel true \
  --backup true \
  --upgrade-software false \
  --clean-cache false \
  --ignore-backup-tips

# Install MySQL and Python
RUN apt-get update && \
    apt-get install -y \
        mysql-server \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --break-system-packages -r requirements.txt

COPY . .

CMD ["python3","main.py"]


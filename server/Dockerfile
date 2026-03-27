FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx openssl iperf3 iputils-ping vsftpd openssh-server supervisor iproute2 \
    && rm -rf /var/lib/apt/lists/*

# SSH setup
RUN mkdir -p /run/sshd && \
    useradd -m -s /bin/bash testuser && echo "testuser:testpass" | chpasswd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
    echo 'LogLevel INFO' >> /etc/ssh/sshd_config

# FTP user
RUN useradd -m -s /bin/bash ftpuser && echo "ftpuser:ftppass" | chpasswd

# SSL certs
RUN mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/server.key -out /etc/nginx/ssl/server.crt \
    -subj "/C=US/ST=CA/L=SanJose/O=TrafficGen/CN=traffic-server"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY nginx.conf /etc/nginx/nginx.conf
COPY vsftpd.conf /etc/vsftpd.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY app.py echo_server.py dashboard.py stats_collector.py ./

# Generate test files for FTP/HTTP download
RUN mkdir -p /data/uploads && \
    dd if=/dev/urandom of=/data/testfile_100mb.bin bs=1M count=100 && \
    dd if=/dev/urandom of=/data/testfile_1gb.bin bs=1M count=1024 && \
    chown -R ftp:ftp /data

EXPOSE 80 443 5201 5201/udp 9999 9998/udp 21 21100-21110 22 8082

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

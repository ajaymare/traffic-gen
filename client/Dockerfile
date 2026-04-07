FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 iptables iputils-ping iperf3 hping3 curl nginx openssl supervisor sudo openssh-client sshpass \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with sudo access for network commands (tc, iptables, ip)
# Default password: trafficgen (override with SUDO_PASSWORD env var at runtime)
ARG SUDO_PASSWORD=trafficgen
RUN useradd -m -s /bin/bash appuser && \
    echo "appuser:${SUDO_PASSWORD}" | chpasswd && \
    echo 'appuser ALL=(root) PASSWD: /sbin/tc, /usr/sbin/tc, /sbin/iptables, /usr/sbin/iptables, /sbin/ip, /usr/sbin/ip, /usr/sbin/hping3' > /etc/sudoers.d/appuser && \
    chmod 0440 /etc/sudoers.d/appuser

# Generate self-signed SSL cert for dashboard HTTPS
RUN mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/client.key -out /etc/nginx/ssl/client.crt \
    -subj "/C=US/ST=CA/L=SanJose/O=TrafficGen/CN=traffic-client"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY . .

# Give appuser ownership of the app directory
RUN chown -R appuser:appuser /app

EXPOSE 8080 8443

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

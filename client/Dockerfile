FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 iputils-ping iperf3 hping3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8080

CMD ["gunicorn", "-w", "1", "--threads", "8", "-b", "0.0.0.0:8080", "app:app"]

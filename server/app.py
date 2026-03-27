import os
import json
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD_DIR = '/data/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

STATS_FILE = '/tmp/http_stats.json'
stats_lock = threading.Lock()
http_stats = {
    'requests': 0,
    'bytes_recv': 0,
    'bytes_sent': 0,
    'errors': 0,
    'uploads': 0,
    'downloads': 0,
}


def save_http_stats():
    with stats_lock:
        with open(STATS_FILE, 'w') as f:
            json.dump(http_stats, f)


@app.before_request
def track_request():
    with stats_lock:
        http_stats['requests'] += 1
        http_stats['bytes_recv'] += request.content_length or 0


@app.after_request
def track_response(response):
    with stats_lock:
        content_length = response.content_length or 0
        http_stats['bytes_sent'] += content_length
    save_http_stats()
    return response


@app.route('/')
def index():
    return jsonify({"status": "ok", "service": "traffic-server",
                    "protocols": ["http", "https", "tcp", "udp", "ftp", "ssh", "icmp"]})


@app.route('/health')
def health():
    return jsonify({"status": "healthy"})


FTP_DATA_DIR = '/data'


@app.route('/upload', methods=['POST'])
def upload():
    with stats_lock:
        http_stats['uploads'] += 1

    if 'file' in request.files:
        f = request.files['file']
        path = os.path.join(UPLOAD_DIR, f.filename)
        f.save(path)
        return jsonify({"status": "ok", "filename": f.filename, "size": os.path.getsize(path)})

    data = request.get_data()
    path = os.path.join(UPLOAD_DIR, 'raw_upload.bin')
    with open(path, 'wb') as f:
        f.write(data)
    return jsonify({"status": "ok", "size": len(data)})


@app.route('/api/files/upload', methods=['POST'])
def upload_ftp_file():
    """Upload a file to the FTP data directory."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({"error": "No filename"}), 400
    path = os.path.join(FTP_DATA_DIR, f.filename)
    f.save(path)
    os.chmod(path, 0o644)
    return jsonify({"ok": True, "filename": f.filename, "size": os.path.getsize(path)})


@app.route('/api/files')
def list_ftp_files():
    """List files available for FTP download."""
    files = []
    for name in sorted(os.listdir(FTP_DATA_DIR)):
        path = os.path.join(FTP_DATA_DIR, name)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            files.append({"name": name, "size": size})
    return jsonify({"files": files})


@app.route('/api/files/<name>', methods=['DELETE'])
def delete_ftp_file(name):
    """Delete a file from the FTP data directory."""
    path = os.path.join(FTP_DATA_DIR, name)
    if not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    os.remove(path)
    return jsonify({"ok": True, "message": f"Deleted {name}"})


@app.route('/generate/<int:size_mb>')
def generate_data(size_mb):
    """Stream zeroed data of specified size in MB for bandwidth testing."""
    size_mb = min(size_mb, 1024)

    with stats_lock:
        http_stats['downloads'] += 1
        http_stats['bytes_sent'] += size_mb * 1024 * 1024

    def generate():
        chunk = b'\x00' * (1024 * 1024)
        for _ in range(size_mb):
            yield chunk

    return app.response_class(
        generate(), mimetype='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename=testdata_{size_mb}mb.bin'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

import os
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD_DIR = '/data/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route('/')
def index():
    return jsonify({"status": "ok", "service": "traffic-server",
                    "protocols": ["http", "https", "tcp", "udp", "ftp", "ssh", "icmp"]})


@app.route('/health')
def health():
    return jsonify({"status": "healthy"})


@app.route('/upload', methods=['POST'])
def upload():
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


@app.route('/generate/<int:size_mb>')
def generate_data(size_mb):
    """Stream zeroed data of specified size in MB for bandwidth testing."""
    size_mb = min(size_mb, 1024)

    def generate():
        chunk = b'\x00' * (1024 * 1024)
        for _ in range(size_mb):
            yield chunk

    return app.response_class(
        generate(), mimetype='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename=testdata_{size_mb}mb.bin'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

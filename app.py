import os
import subprocess
import sys
from flask import Flask, render_template_string, request, redirect
from datetime import datetime, timedelta

app = Flask(__name__)

# في Koyeb المسارات تكون مباشرة في مجلد العمل
ROOT = os.getcwd()
PROJECT_DIR = os.path.join(ROOT, "projects")
LOG_FILE = os.path.join(ROOT, "output.log")

if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR, exist_ok=True)

hixu_hosting = {"process": None, "name": None, "expiry": None}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hixu Cloud | Koyeb</title>
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: sans-serif; text-align: center; padding: 20px; }
        .card { background: #1e293b; padding: 30px; border-radius: 20px; max-width: 500px; margin: auto; border: 1px solid #334155; }
        h1 { color: #38bdf8; font-size: 35px; }
        .btn { width: 100%; padding: 15px; border-radius: 10px; border: none; cursor: pointer; font-weight: bold; margin-top: 10px; }
        .btn-run { background: #38bdf8; color: #0f172a; }
        .btn-stop { background: #ef4444; color: white; }
        .logs { background: #000; color: #4ade80; text-align: left; padding: 15px; font-family: monospace; height: 150px; overflow-y: auto; margin: 15px 0; border-radius: 10px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>Hixu Cloud</h1>
    <div class="card">
        {% if not active %}
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept=".py" required><br><br>
                <button class="btn btn-run">تشغيل على Koyeb</button>
            </form>
        {% else %}
            <p>نشط: {{ name }}</p>
            <div class="logs">{{ logs }}</div>
            <form action="/stop" method="post">
                <button class="btn btn-stop">إيقاف</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

def stop_process():
    if hixu_hosting["process"]:
        try: hixu_hosting["process"].terminate()
        except: pass
    hixu_hosting["process"] = None

@app.route('/')
def index():
    logs = "جاري الانتظار..."
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f: logs = f.read()[-2000:]
    return render_template_string(HTML, active=(hixu_hosting["process"] is not None), name=hixu_hosting["name"], logs=logs)

@app.route('/upload', methods=['POST'])
def upload():
    stop_process()
    file = request.files.get('file')
    if file:
        f_path = os.path.join(PROJECT_DIR, "user_app.py")
        file.save(f_path)
        with open(LOG_FILE, "w") as f: f.write("--- Start ---\n")
        
        log_f = open(LOG_FILE, "a")
        # تشغيل العملية في بيئة Koyeb
        proc = subprocess.Popen([sys.executable, "-u", f_path], stdout=log_f, stderr=log_f)
        hixu_hosting["process"] = proc
        hixu_hosting["name"] = file.filename
    return redirect('/')

@app.route('/stop', methods=['POST'])
def stop():
    stop_process()
    return redirect('/')

if __name__ == "__main__":
    # Koyeb يستخدم المنفذ 8000 تلقائياً في أغلب الأحيان أو يمكنك تحديده
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

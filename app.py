from flask import Flask, render_template_string, request, flash, session, redirect, url_for
import datetime
import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
app.secret_key = "hixuz_ultra_premium_v5_final"

# --- إعدادات الربط المحدثة ---
API_URL = "https://kd1s.com/api/v2"
API_KEY = "452d55cf3cb4db443648a9c64e0d3c31"
TELEGRAM_URL = "https://t.me/cvbnm_6"
ADMIN_PASSWORD = "8461893480"

# الخدمات المحدثة بناءً على طلبك الأخير
SERVICES_CONFIG = {
    "متابعين": {
        "id": "16235", "count": 10, "icon": "👤", "type": "user",
        "desc": "تعزيز ملفك الشخصي بمتابعين حقيقيين لزيادة الهيبة."
    },
    "مشاهدات": {
        "id": "17463", "count": 100, "icon": "👁️", "type": "video",
        "desc": "زيادة مشاهدات الفيديو بسرعة البرق لتصدر قوائم البحث."
    },
    "لايكات": {
        "id": "12156", "count": 10, "icon": "❤️", "type": "video",
        "desc": "تفاعلات قوية ترفع من تقييم الفيديو في خوارزمية تيك توك."
    },
    "اكسبلور": {
        "id": "11650", "count": 10, "icon": "🚀", "type": "video",
        "desc": "نشر الفيديو على نطاق واسع لزيادة الوصول العالمي."
    },
    "حفظ": {
        "id": "16400", "count": 10, "icon": "🔖", "type": "video",
        "desc": "زيادة عدد مرات الحفظ مما يجعل الفيديو مرشحاً للاكسبلور."
    }
}

DB_FILE = "hixuz_data.json"
STATUS_FILE = "hixuz_status.json"

def get_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

def get_status():
    if not os.path.exists(STATUS_FILE):
        initial = {name: True for name in SERVICES_CONFIG}
        save_status(initial)
        return initial
    with open(STATUS_FILE, "r") as f: return json.load(f)

def save_status(data):
    with open(STATUS_FILE, "w") as f: json.dump(data, f)

user_template = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HIXUZ | المنصة العالمية</title>
    <style>
        :root { --cyan: #00f2ea; --pink: #ff0050; --dark-bg: #030303; }
        * { box-sizing: border-box; }
        body { 
            margin: 0; font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--dark-bg); color: white;
            min-height: 100vh; overflow-x: hidden;
        }
        
        /* تصميم الهيدر العلوي */
        .top-nav {
            background: linear-gradient(to bottom, rgba(0,0,0,0.9), transparent);
            padding: 40px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .top-nav h1 { 
            margin: 0; font-size: 3.5rem; font-weight: 900; color: var(--cyan);
            text-shadow: 0 0 30px rgba(0,242,234,0.6); letter-spacing: 8px;
        }
        .top-nav p { color: #666; margin-top: 10px; font-size: 1rem; }

        .container { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); 
            gap: 25px; padding: 40px 20px; max-width: 1250px; margin: auto; 
        }

        .card { 
            background: rgba(255,255,255,0.02); border: 1px solid #1a1a1a; 
            border-radius: 30px; padding: 35px; text-align: center; 
            transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
        }
        .card:hover { border-color: var(--cyan); transform: translateY(-12px); background: rgba(255,255,255,0.04); }
        
        .icon { font-size: 3.5rem; margin-bottom: 15px; display: block; }
        .card h3 { font-size: 1.7rem; margin: 10px 0; color: #eee; }
        .desc { font-size: 0.9rem; color: #777; margin-bottom: 25px; line-height: 1.6; }
        
        .badge { background: rgba(0,242,234,0.1); color: var(--cyan); padding: 6px 18px; border-radius: 50px; font-weight: bold; border: 1px solid rgba(0,242,234,0.2); }

        input { 
            width: 100%; padding: 16px; margin: 25px 0 15px; border-radius: 15px; border: 1px solid #222; 
            background: #000; color: white; text-align: center; font-size: 1rem; transition: 0.3s;
        }
        input:focus { border-color: var(--pink); outline: none; box-shadow: 0 0 15px rgba(255,0,80,0.2); }

        .btn { 
            width: 100%; padding: 16px; border-radius: 15px; border: none; 
            background: linear-gradient(90deg, var(--pink), #ff4d8d); color: white; 
            font-weight: bold; cursor: pointer; font-size: 1.2rem; transition: 0.3s;
        }
        .btn:hover { box-shadow: 0 10px 30px rgba(255,0,80,0.4); transform: scale(1.02); }

        .tg-float { position: fixed; bottom: 30px; left: 30px; width: 65px; height: 65px; background: #26A5E4; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; text-decoration: none; box-shadow: 0 10px 25px rgba(38, 165, 228, 0.4); z-index: 1000; transition: 0.3s; }
        .tg-float:hover { transform: scale(1.1); }

        .alert { padding: 20px; margin: 10px auto; max-width: 700px; border-radius: 20px; text-align: center; font-weight: bold; }
        .success { border: 2px solid #00ff88; color: #00ff88; background: rgba(0,255,136,0.05); }
        .error { border: 2px solid var(--pink); color: var(--pink); background: rgba(255,0,80,0.05); }
    </style>
</head>
<body>
    <div class="top-nav">
        <h1>HIXUZ</h1>
        <p>الجيل القادم من خدمات تيك توك التلقائية</p>
    </div>
    
    <a href="{{ tg }}" class="tg-float" target="_blank">✈️</a>

    {% with msgs = get_flashed_messages(with_categories=true) %}
      {% if msgs %}{% for cat, msg in msgs %}<div class="alert {{ cat }}">{{ msg }}</div>{% endfor %}{% endif %}
    {% endwith %}

    <div class="container">
        {% for name, info in config.items() %}
            {% if status[name] %}
            <div class="card">
                <span class="icon">{{ info.icon }}</span>
                <h3>{{ name }}</h3>
                <p class="desc">{{ info.desc }}</p>
                <span class="badge">الكمية: {{ info.count }}</span>
                <form method="POST">
                    <input type="hidden" name="s_name" value="{{ name }}">
                    <input type="text" name="target" placeholder="اليوزر أو الرابط" required>
                    <button type="submit" class="btn">تأكيد الطلب</button>
                </form>
            </div>
            {% endif %}
        {% endfor %}
    </div>
</body>
</html>
"""

# لوحة التحكم تظل كما هي لسهولة الاستخدام
admin_template = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>HIXUZ ADMIN</title>
    <style>
        body { background: #000; color: white; font-family: sans-serif; text-align: center; padding: 50px; }
        .box { background: #111; padding: 40px; border-radius: 20px; border: 1px solid #333; display: inline-block; min-width: 350px; }
        input { padding: 12px; width: 90%; margin: 15px 0; border-radius: 8px; border: 1px solid #333; background: #000; color: white; }
        .btn { width: 90%; padding: 12px; border-radius: 8px; border: none; background: #00f2ea; color: black; font-weight: bold; cursor: pointer; }
        .row { display: flex; justify-content: space-between; padding: 12px; border-bottom: 1px solid #222; }
        .t-btn { padding: 5px 12px; border-radius: 5px; border: none; cursor: pointer; color: white; font-weight: bold; }
    </style>
</head>
<body>
    {% if not auth %}
    <div class="box">
        <h2>دخول المسؤول</h2>
        <form method="POST">
            <input type="password" name="pw" placeholder="كود الدخول" required>
            <button type="submit" class="btn">دخول</button>
        </form>
    </div>
    {% else %}
    <div class="box" style="width: 500px;">
        <h2>التحكم بالخدمات</h2>
        {% for n, active in status.items() %}
        <div class="row">
            <span>{{ n }}</span>
            <form method="POST" action="/toggle">
                <input type="hidden" name="n" value="{{ n }}">
                <button type="submit" class="t-btn" style="background: {{ '#2ecc71' if active else '#e74c3c' }}">
                    {{ 'مفعّل' if active else 'مغلق' }}
                </button>
            </form>
        </div>
        {% endfor %}
        <form method="POST" action="/reset">
            <button type="submit" class="btn" style="background: white; margin-top: 20px;">تصفير الحماية</button>
        </form>
        <br><a href="/" style="color:#888;">عرض الموقع</a> | <a href="/logout" style="color:red;">خروج</a>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    db = get_db()
    status = get_status()
    if request.method == 'POST':
        target = request.form.get('target').strip()
        s_name = request.form.get('s_name')
        if not status.get(s_name):
            flash("عذراً، الخدمة مغلقة حالياً.", "error")
            return redirect('/')
        
        info = SERVICES_CONFIG[s_name]
        now = datetime.datetime.now()
        
        for key, t_str in db.items():
            if target in key:
                if now < datetime.datetime.fromisoformat(t_str) + datetime.timedelta(hours=24):
                    flash("⚠️ نظام الحماية: طلب واحد كل 24 ساعة لكل حساب.", "error")
                    return redirect('/')
        
        try:
            payload = {'key': API_KEY, 'action': 'add', 'service': info['id'], 'link': target, 'quantity': info['count']}
            res = requests.post(API_URL, data=payload, timeout=15, verify=False).json()
            if 'order' in res:
                db[f"{target}_{s_name}"] = now.isoformat()
                save_db(db)
                flash(f"✅ تم الإرسال بنجاح! رقم طلبك: {res['order']}", "success")
            else:
                flash(f"❌ رد الموقع: {res.get('error', 'خطأ في الكمية')}", "error")
        except: flash("❌ فشل الاتصال بالسيرفر الرئيسي.", "error")
    return render_template_string(user_template, config=SERVICES_CONFIG, status=status, tg=TELEGRAM_URL)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pw') == ADMIN_PASSWORD:
            session['auth'] = True
            return redirect('/login')
    return render_template_string(admin_template, auth=session.get('auth'), status=get_status())

@app.route('/toggle', methods=['POST'])
def toggle():
    if session.get('auth'):
        n = request.form.get('n')
        st = get_status()
        if n in st: st[n] = not st[n]
        save_status(st)
    return redirect('/login')

@app.route('/reset', methods=['POST'])
def reset():
    if session.get('auth'): save_db({})
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('auth', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

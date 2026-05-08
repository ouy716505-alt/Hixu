import os
import secrets
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# --- إعدادات المسارات ---
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'hixu_ultimate_v13.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- نماذج قاعدة البيانات (Models) ---
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(200))
    file_filename = db.Column(db.String(200))
    video_url = db.Column(db.String(500))
    external_link = db.Column(db.String(500))
    downloads_count = db.Column(db.Integer, default=0)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(200))
    link_url = db.Column(db.String(500))
    title = db.Column(db.String(100))

# --- الواجهة البرمجية (HTML) ---
MASTER_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1628282388136551" crossorigin="anonymous"></script>

    <title>Hixu Store | Ultra Performance</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    
    <style>
        :root { --primary: #2563eb; --accent: #ff0050; --bg: #f8fafc; }
        body { background: var(--bg); font-family: 'Tajawal', sans-serif; color: #1e293b; overflow-x: hidden; }
        
        .navbar { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(0,0,0,0.05); padding: 15px 0; z-index: 1000; }
        .nav-logo { font-weight: 900; font-size: 2rem; color: var(--primary) !important; text-decoration: none; letter-spacing: -1px; }

        /* Slider Fixed Dimensions 1280x720 */
        .slider-container { max-width: 1280px; margin: 0 auto 40px auto; border-radius: 30px; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.15); border: 4px solid #fff; }
        .carousel-item { height: 0; padding-bottom: 56.25%; /* نسبة 16:9 (720/1280) */ background: #000; position: relative; }
        .carousel-item img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.7; transition: 1.2s cubic-bezier(0.4, 0, 0.2, 1); }
        .carousel-item.active img { transform: scale(1.08); }
        .carousel-caption { bottom: 15%; text-align: right; z-index: 10; }
        .carousel-caption h2 { font-weight: 900; font-size: clamp(1.5rem, 5vw, 3.5rem); text-shadow: 0 4px 15px rgba(0,0,0,0.6); }

        .hero-section { padding: 40px 0; text-align: center; }
        .hero-title { font-weight: 900; font-size: clamp(2.5rem, 8vw, 4.5rem); background: linear-gradient(45deg, #111, var(--primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .search-input { max-width: 600px; margin: 30px auto 15px auto; border-radius: 50px; padding: 18px 35px; border: 2px solid #e2e8f0; text-align: center; font-size: 1.2rem; transition: 0.4s; }
        
        .filter-btns { display: flex; justify-content: center; gap: 10px; margin-bottom: 40px; flex-wrap: wrap; }
        .btn-filter { background: #fff; border: 1px solid #e2e8f0; color: #64748b; padding: 8px 25px; border-radius: 50px; font-weight: 700; transition: 0.3s; text-decoration: none; font-size: 0.9rem; }
        .btn-filter:hover, .btn-filter.active { background: var(--primary); color: #fff; border-color: var(--primary); }

        .game-card { border: none; border-radius: 25px; background: #fff; transition: 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); overflow: hidden; height: 100%; border: 1px solid rgba(0,0,0,0.03); cursor: pointer; }
        .game-card:hover { transform: translateY(-15px); box-shadow: 0 30px 60px rgba(0,0,0,0.1); }
        .game-img { width: 100%; height: 230px; object-fit: cover; }

        .admin-card { background: #fff; padding: 30px; border-radius: 25px; border: 1px solid #eee; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.02); }
        .management-item { background: #f8fafc; padding: 12px 20px; border-radius: 15px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; transition: 0.3s; }
        .management-item:hover { background: #f1f5f9; border-color: var(--primary); }
        
        .social-links { display: flex; justify-content: center; gap: 20px; margin-top: 20px; }
        .tiktok-link { display: inline-flex; align-items: center; gap: 10px; background: #000; color: #fff; padding: 12px 30px; border-radius: 50px; text-decoration: none; font-weight: 900; transition: 0.4s; }
        .telegram-link { display: inline-flex; align-items: center; gap: 10px; background: #0088cc; color: #fff; padding: 12px 30px; border-radius: 50px; text-decoration: none; font-weight: 900; transition: 0.4s; }
        .tiktok-link:hover, .telegram-link:hover { transform: scale(1.05); color: #fff; }
        
        footer { padding: 60px 0; text-align: center; background: #fff; border-top: 1px solid #eee; margin-top: 100px; }
    </style>
</head>
<body>

<nav class="navbar sticky-top">
    <div class="container d-flex justify-content-between align-items-center">
        <a class="nav-logo" href="/" data-aos="fade-left">HIXU STORE</a>
        <div class="d-flex align-items-center gap-2">
            <a href="https://t.me/cvbnm_6" target="_blank" class="text-primary me-3 fs-4"><i class="fab fa-telegram"></i></a>
            {% if session.get('admin') %}
                <a href="/upload" class="btn btn-dark rounded-pill px-4">لوحة التحكم</a>
            {% endif %}
        </div>
    </div>
</nav>

<div class="container mt-4">
    {% if page == 'home' %}
        {% if banners %}
        <div class="slider-container" data-aos="zoom-in">
            <div id="mainSlider" class="carousel slide carousel-fade" data-bs-ride="carousel">
                <div class="carousel-inner">
                    {% for b in banners %}
                    <div class="carousel-item {% if loop.first %}active{% endif %}" data-bs-interval="4000">
                        <a href="{{ b.link_url or '#' }}">
                            <img src="{{ url_for('uploaded_file', filename=b.image_filename) }}">
                            <div class="carousel-caption">
                                <h2 class="fw-bold">{{ b.title }}</h2>
                            </div>
                        </a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}

        <div class="hero-section" data-aos="fade-up">
            <h1 class="hero-title">HIXU STORE</h1>
            <p class="text-muted fs-5">استكشف عالم الألعاب بأعلى سرعة وأمان</p>
            <form action="/" method="GET">
                <input type="text" name="q" class="form-control search-input" placeholder="بحث سريع..." value="{{ q }}">
            </form>
            
            <div class="filter-btns">
                <a href="/?sort=new" class="btn-filter {% if sort == 'new' or sort == '' %}active{% endif %}">الأحدث</a>
                <a href="/?sort=trend" class="btn-filter {% if sort == 'trend' %}active{% endif %}">الأكثر تحميلاً</a>
                <a href="/?sort=old" class="btn-filter {% if sort == 'old' %}active{% endif %}">الأقدم</a>
            </div>
        </div>

        <div class="row g-4">
            {% for game in games %}
            <div class="col-6 col-md-4 col-lg-3" data-aos="fade-up" data-aos-delay="{{ loop.index * 30 }}">
                <div class="game-card" onclick="location.href='/game/{{ game.id }}'">
                    <img src="{{ url_for('uploaded_file', filename=game.image_filename) if game.image_filename else 'https://via.placeholder.com/400x300' }}" class="game-img">
                    <div class="p-4 text-center">
                        <h6 class="fw-bold mb-3 text-truncate">{{ game.title }}</h6>
                        <span class="btn btn-outline-primary rounded-pill btn-sm px-4">دخول المتجر</span>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

    {% elif page == 'details' %}
        <div class="mx-auto mt-5" style="max-width: 1100px;" data-aos="fade-up">
            <div class="video-container" style="border-radius: 30px; overflow: hidden; background: #000; box-shadow: 0 30px 60px rgba(0,0,0,0.3);">
                {% if game.video_url %}
                    {% set video_id = game.video_url.split('v=')[-1] if 'v=' in game.video_url else game.video_url.split('/')[-1] %}
                    <iframe src="https://www.youtube.com/embed/{{ video_id }}?autoplay=1&rel=0" style="width: 100%; aspect-ratio: 16/9;" frameborder="0" allowfullscreen></iframe>
                {% else %}
                    <img src="{{ url_for('uploaded_file', filename=game.image_filename) }}" class="w-100">
                {% endif %}
            </div>

            <div class="p-5 bg-white rounded-5 shadow-lg mt-4 border">
                <div class="d-flex justify-content-between align-items-center">
                    <h1 class="fw-900">{{ game.title }}</h1>
                    <span class="badge bg-primary px-3 py-2 rounded-pill">تحميلات: {{ game.downloads_count }}</span>
                </div>
                <p class="fs-5 text-secondary mt-4" style="line-height: 2;">{{ game.description }}</p>

                <button id="startDownload" class="btn btn-success btn-lg w-100 py-4 rounded-pill fw-900 mt-5 shadow-lg">
                    <i class="fas fa-bolt me-2"></i> بدء التحميل المباشر
                </button>

                <div id="timerContainer" class="timer-box" style="display:none; text-align:center; padding: 40px; background: #f0f7ff; border-radius: 30px; margin-top: 30px; border: 2px dashed #2563eb;">
                    <p class="fw-bold fs-4">جاري التحقق من أمان الملف...</p>
                    <div style="font-size: 5rem; font-weight: 900; color: #2563eb;" id="countdown">15</div>
                </div>

                <form id="realDownloadForm" action="/count_download/{{ game.id }}" method="POST" style="display:none;"></form>

                <script>
                    document.getElementById('startDownload').onclick = function() {
                        this.style.display = 'none';
                        document.getElementById('timerContainer').style.display = 'block';
                        let count = 15;
                        let counter = setInterval(function() {
                            count--;
                            document.getElementById('countdown').innerHTML = count;
                            if (count <= 0) {
                                clearInterval(counter);
                                document.getElementById('realDownloadForm').submit();
                            }
                        }, 1000);
                    };
                </script>
            </div>
        </div>

    {% elif page == 'upload' %}
        <div class="row g-4" data-aos="fade-in">
            <div class="col-md-7">
                <div class="admin-card">
                    <h4 class="fw-900 mb-4 text-primary"><i class="fas fa-plus-circle me-2"></i>إضافة لعبة جديدة</h4>
                    <form method="POST" action="/upload_game" enctype="multipart/form-data">
                        <input type="text" name="title" class="form-control mb-3 p-3 rounded-4" placeholder="اسم اللعبة" required>
                        <textarea name="desc" class="form-control mb-3 p-3 rounded-4" rows="4" placeholder="وصف اللعبة"></textarea>
                        <label class="small text-muted ms-2">صورة اللعبة:</label>
                        <input type="file" name="img_file" class="form-control mb-3 p-2 rounded-4">
                        <input type="text" name="video_url" class="form-control mb-3 p-3 rounded-4" placeholder="رابط يوتيوب">
                        <label class="small text-muted ms-2">ملف اللعبة:</label>
                        <input type="file" name="game_file" class="form-control mb-3 p-2 rounded-4">
                        <input type="text" name="ext_link" class="form-control mb-3 p-3 rounded-4" placeholder="رابط خارجي مباشر">
                        <button type="submit" class="btn btn-primary w-100 py-3 fw-bold rounded-pill">نشر الآن</button>
                    </form>
                </div>
            </div>

            <div class="col-md-5">
                <div class="admin-card bg-light">
                    <h5 class="fw-900 mb-4"><i class="fas fa-cog me-2"></i>إدارة المحتوى</h5>
                    
                    <p class="fw-bold text-muted border-bottom pb-2">إضافة سلايدر (1280x720)</p>
                    <form method="POST" action="/upload_banner" enctype="multipart/form-data" class="mb-4">
                        <input type="text" name="b_title" class="form-control mb-2 rounded-4" placeholder="العنوان" required>
                        <input type="file" name="b_img" class="form-control mb-2 rounded-4" required>
                        <input type="text" name="b_link" class="form-control mb-2 rounded-4" placeholder="الرابط">
                        <button class="btn btn-success btn-sm w-100 rounded-pill">حفظ السلايدر</button>
                    </form>
                    
                    <p class="fw-bold text-danger border-bottom pb-2 mt-4">حذف السلايدرات</p>
                    <div class="mb-4" style="max-height: 200px; overflow-y: auto;">
                        {% for b in all_banners %}
                        <div class="management-item">
                            <span class="small fw-bold text-truncate" style="max-width: 150px;">{{ b.title }}</span>
                            <a href="/delete_banner/{{ b.id }}" class="btn btn-outline-danger btn-sm rounded-pill px-3" onclick="return confirm('حذف هذا السلايدر؟')">حذف</a>
                        </div>
                        {% endfor %}
                    </div>

                    <p class="fw-bold text-danger border-bottom pb-2">حذف الألعاب</p>
                    <div style="max-height: 300px; overflow-y: auto;">
                        {% for g in all_games %}
                        <div class="management-item">
                            <span class="small fw-bold text-truncate" style="max-width: 150px;">{{ g.title }}</span>
                            <a href="/delete_game/{{ g.id }}" class="btn btn-danger btn-sm rounded-pill px-3" onclick="return confirm('حذف هذه اللعبة نهائياً؟')">حذف</a>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    {% elif page == 'login' %}
        <div class="mx-auto mt-5 text-center" style="max-width: 450px;" data-aos="zoom-in">
            <div class="p-5 bg-white rounded-5 shadow-lg border">
                <h3 class="fw-900 mb-4">الدخول للمسؤول</h3>
                <form method="POST">
                    <input type="password" name="password" class="form-control mb-4 text-center p-3 rounded-pill" placeholder="كلمة السر" required>
                    <button type="submit" class="btn btn-primary w-100 py-3 rounded-pill fw-bold">تحقق ودخول</button>
                </form>
            </div>
        </div>
    {% endif %}
</div>

<footer>
    <div class="container">
        <h2 class="fw-900 text-primary mb-3">HIXU STORE</h2>
        <p class="text-muted small mb-4">جميع الحقوق محفوظة © 2026</p>
        <div class="social-links">
            <a href="https://tiktok.com/@r_tyy7" target="_blank" class="tiktok-link">
                <i class="fab fa-tiktok"></i> TikTok
            </a>
            <a href="https://t.me/cvbnm_6" target="_blank" class="telegram-link">
                <i class="fab fa-telegram"></i> Telegram
            </a>
        </div>
        <br>
        <a href="/login" style="opacity: 0.1; color: #000; font-size: 0.7rem; text-decoration: none;" class="mt-5 d-inline-block">Admin Terminal</a>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
<script>
    AOS.init({ duration: 800, once: true });
</script>
</body>
</html>
"""

# --- الأوامر البرمجية (Routes) ---

@app.route('/')
def index():
    q = request.args.get('q', '')
    sort = request.args.get('sort', '')
    query = Game.query
    if q: query = query.filter(Game.title.contains(q))
    
    if sort == 'trend': games = query.order_by(Game.downloads_count.desc()).all()
    elif sort == 'old': games = query.order_by(Game.date_added.asc()).all()
    else: games = query.order_by(Game.date_added.desc()).all()
    
    banners = Banner.query.all()
    return render_template_string(MASTER_HTML, page='home', games=games, banners=banners, q=q, sort=sort)

@app.route('/game/<int:game_id>')
def details(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template_string(MASTER_HTML, page='details', game=game)

@app.route('/count_download/<int:game_id>', methods=['POST'])
def count_download(game_id):
    game = Game.query.get_or_404(game_id)
    game.downloads_count += 1
    db.session.commit()
    if game.file_filename: return redirect(url_for('uploaded_file', filename=game.file_filename))
    return redirect(game.external_link or '/')

@app.route('/upload')
def upload():
    if not session.get('admin'): return redirect(url_for('login'))
    all_banners = Banner.query.all()
    all_games = Game.query.order_by(Game.date_added.desc()).all()
    return render_template_string(MASTER_HTML, page='upload', all_banners=all_banners, all_games=all_games)

@app.route('/upload_game', methods=['POST'])
def upload_game():
    if not session.get('admin'): abort(403)
    img = request.files.get('img_file')
    file = request.files.get('game_file')
    img_name = secrets.token_hex(8) + "_" + secure_filename(img.filename) if img and img.filename else None
    if img_name: img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
    file_name = secrets.token_hex(8) + "_" + secure_filename(file.filename) if file and file.filename else None
    if file_name: file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
    new_game = Game(title=request.form['title'], description=request.form['desc'], image_filename=img_name, file_filename=file_name, video_url=request.form.get('video_url'), external_link=request.form.get('ext_link'))
    db.session.add(new_game)
    db.session.commit()
    return redirect(url_for('upload'))

@app.route('/delete_game/<int:id>')
def delete_game(id):
    if not session.get('admin'): abort(403)
    game = Game.query.get_or_404(id)
    db.session.delete(game)
    db.session.commit()
    return redirect(url_for('upload'))

@app.route('/upload_banner', methods=['POST'])
def upload_banner():
    if not session.get('admin'): abort(403)
    img = request.files.get('b_img')
    if img:
        img_name = "banner_" + secrets.token_hex(4) + "_" + secure_filename(img.filename)
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
        new_banner = Banner(title=request.form['b_title'], image_filename=img_name, link_url=request.form.get('b_link'))
        db.session.add(new_banner)
        db.session.commit()
    return redirect(url_for('upload'))

@app.route('/delete_banner/<int:id>')
def delete_banner(id):
    if not session.get('admin'): abort(403)
    b = Banner.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    return redirect(url_for('upload'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # كلمة السر الجديدة هنا
    if request.method == 'POST' and request.form.get('password') == '8461893480':
        session['admin'] = True
        return redirect(url_for('upload'))
    return render_template_string(MASTER_HTML, page='login')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

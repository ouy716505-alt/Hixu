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

# --- إعداد قاعدة البيانات (تم التعديل لربط PostgreSQL) ---
# سيستخدم PostgreSQL إذا كانت موجودة في إعدادات Render، وإلا سيعود لـ SQLite محلياً
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or ('sqlite:///' + os.path.join(basedir, 'hixu_store_v50.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- نماذج قاعدة البيانات (Models) ---
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(200))
    screenshots = db.Column(db.Text) # تخزين حتى 8 صور مفصولة بفاصلة
    file_filename = db.Column(db.String(200))
    video_url = db.Column(db.String(500))
    external_link = db.Column(db.String(500))
    downloads_count = db.Column(db.Integer, default=0)
    rating_sum = db.Column(db.Float, default=5.0) # مجموع النقاط
    rating_count = db.Column(db.Integer, default=1) # عدد المقيمين
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def average_rating(self):
        if self.rating_count == 0: return 0
        return round(self.rating_sum / self.rating_count, 1)

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
    <title>Hixu Store | Ultra Professional</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <style>
        :root { 
            --primary: #00ff41; 
            --dark-bg: #000000; 
            --card-bg: #0a0a0a; 
            --accent: #003b00;
            --text-white: #ffffff;
        }
        
        body { background: var(--dark-bg); font-family: 'Tajawal', sans-serif; color: var(--text-white); overflow-x: hidden; }

        .navbar { background: rgba(0, 0, 0, 0.95); backdrop-filter: blur(12px); border-bottom: 1px solid var(--primary); padding: 15px 0; z-index: 1000; }
        .nav-logo { font-weight: 900; font-size: 2rem; color: var(--primary) !important; text-decoration: none; text-shadow: 0 0 10px var(--primary); }

        /* السلايدر الرئيسي */
        .slider-container { max-width: 1100px; margin: 30px auto; border-radius: 30px; overflow: hidden; border: 2px solid var(--primary); box-shadow: 0 0 30px rgba(0,255,65,0.2); }
        .carousel-item { height: 400px; background: #000; position: relative; }
        .carousel-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
        .carousel-caption h2 { font-weight: 900; color: #fff; }

        /* الفلاتر */
        .filter-btn { background: #111; border: 1px solid var(--primary); color: var(--primary); border-radius: 50px; padding: 8px 20px; transition: 0.3s; text-decoration: none; }
        .filter-btn:hover, .filter-btn.active { background: var(--primary); color: #000; box-shadow: 0 0 10px var(--primary); }

        /* لقطات الشاشة 8 صور */
        .screenshot-slider { display: flex; overflow-x: auto; gap: 15px; padding: 10px 0; scrollbar-width: none; }
        .screenshot-slider::-webkit-scrollbar { display: none; }
        .screenshot-img { flex: 0 0 280px; height: 160px; object-fit: cover; border-radius: 20px; border: 2px solid var(--primary); transition: 0.4s; }
        .screenshot-img:hover { transform: scale(1.05); }

        /* مربع الوصف (أسود بالكامل) */
        .description-box { 
            background: #000000 !important; 
            color: #ffffff !important; 
            padding: 30px; 
            border-radius: 25px; 
            border: 1px solid var(--primary); 
            margin-top: 25px; 
            line-height: 1.8;
        }

        .game-card { border: none; border-radius: 25px; background: var(--card-bg); transition: 0.4s; overflow: hidden; height: 100%; border: 1px solid rgba(0,255,65,0.1); cursor: pointer; }
        .game-card:hover { transform: translateY(-10px); box-shadow: 0 0 25px var(--primary); border-color: var(--primary); }
        .game-img { width: 100%; height: 230px; object-fit: cover; }
        
        .star-rating { direction: ltr; display: inline-block; }
        .star-rating input { display: none; }
        .star-rating label { color: #333; font-size: 2.2rem; cursor: pointer; transition: 0.2s; }
        .star-rating label:hover, .star-rating label:hover ~ label, .star-rating input:checked ~ label { color: #ffcc00; }

        .btn-primary { background: var(--primary); border: none; color: #000 !important; font-weight: 900; border-radius: 50px; }
        .btn-primary:hover { background: #fff; box-shadow: 0 0 15px #fff; }

        footer { padding: 60px 0; text-align: center; background: #000; border-top: 1px solid var(--primary); position: relative; margin-top: 50px; }
        .hidden-admin { position: absolute; bottom: 0; left: 0; width: 15px; height: 15px; background: transparent; cursor: default; }

        .admin-card { background: var(--card-bg); padding: 30px; border-radius: 25px; border: 1px solid var(--primary); margin-bottom: 20px; }
        .form-control { background: #000; border: 1px solid var(--accent); color: #fff !important; }
        .form-control:focus { border-color: var(--primary); box-shadow: none; }
    </style>
</head>
<body>
    <nav class="navbar sticky-top">
        <div class="container d-flex justify-content-between align-items-center">
            <a class="nav-logo" href="/">HIXU STORE</a>
            <div class="d-flex align-items-center gap-2">
                <a href="https://t.me/cvbnm_6" target="_blank" style="color:var(--primary)" class="me-3 fs-4"><i class="fab fa-telegram"></i></a>
                {% if session.get('admin') %}
                    <a href="/upload" class="btn btn-outline-primary rounded-pill px-4">لوحة التحكم</a>
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

        <div class="hero-section text-center" data-aos="fade-up">
            <h1 class="fw-900" style="font-size: 3.5rem;">HIXU STORE</h1>
            <p class="opacity-75 fs-5" style="color: var(--primary)">عالم الألعاب بين يديك بأقصى سرعة</p>
            <form action="/" method="GET" class="mt-4">
                <input type="text" name="q" class="form-control mb-4 mx-auto text-center rounded-pill border-primary" style="max-width:600px; padding:15px;" placeholder="بحث عن الألعاب..." value="{{ q }}">
            </form>
            <div class="d-flex justify-content-center gap-2 mb-5 flex-wrap">
                <a href="/?sort=new" class="filter-btn {% if sort == 'new' or sort == '' %}active{% endif %}">الأحدث</a>
                <a href="/?sort=trend" class="filter-btn {% if sort == 'trend' %}active{% endif %}">الأكثر تحميلاً</a>
                <a href="/?sort=old" class="filter-btn {% if sort == 'old' %}active{% endif %}">الأقدم</a>
            </div>
        </div>

        <div class="row g-4">
            {% for game in games %}
            <div class="col-6 col-md-4 col-lg-3" data-aos="fade-up">
                <div class="game-card" onclick="location.href='/game/{{ game.id }}'">
                    <img src="{{ url_for('uploaded_file', filename=game.image_filename) if game.image_filename else 'https://via.placeholder.com/400' }}" class="game-img">
                    <div class="p-3 text-center">
                        <h6 class="fw-bold mb-1 text-truncate">{{ game.title }}</h6>
                        <div class="mb-2">
                            <span style="color:#ffcc00"><i class="fas fa-star"></i> {{ game.average_rating }}</span>
                            <small class="opacity-50 text-white">({{ game.rating_count }})</small>
                        </div>
                        <span class="btn btn-primary btn-sm rounded-pill px-4 w-100">فتح اللعبة</span>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

    {% elif page == 'details' %}
        <div class="row g-4 mt-4" data-aos="fade-in">
            <div class="col-lg-8">
                <div style="border-radius: 30px; overflow: hidden; border: 2px solid var(--primary); background: #000;">
                    {% if game.video_url %}
                        {% set video_id = game.video_url.split('v=')[-1] if 'v=' in game.video_url else game.video_url.split('/')[-1] %}
                        <iframe src="https://www.youtube.com/embed/{{ video_id }}?autoplay=1" style="width: 100%; aspect-ratio: 16/9;" frameborder="0" allowfullscreen></iframe>
                    {% else %}
                        <img src="{{ url_for('uploaded_file', filename=game.image_filename) }}" class="w-100">
                    {% endif %}
                </div>

                <h1 class="fw-900 mt-4">{{ game.title }}</h1>
                
                <h5 class="mt-5 mb-3 text-primary"><i class="fas fa-images me-2"></i> لقطات الشاشة (8 صور)</h5>
                <div class="screenshot-slider">
                    {% if game.screenshots %}
                        {% for img in game.screenshots.split(',') %}
                            <img src="{{ url_for('uploaded_file', filename=img) }}" class="screenshot-img">
                        {% endfor %}
                    {% else %}
                        <p class="opacity-50">لا توجد صور مرفوعة.</p>
                    {% endif %}
                </div>

                <div class="description-box">
                    <h4 class="fw-900 text-primary mb-3">عن اللعبة:</h4>
                    <p>{{ game.description }}</p>
                </div>
            </div>

            <div class="col-lg-4">
                <div class="admin-card text-center shadow-lg">
                    <h2 class="fw-900 text-warning" style="font-size: 3rem;">{{ game.average_rating }}</h2>
                    <p class="opacity-75">من {{ game.rating_count }} تقييم</p>
                    
                    {% if session.get('rated_' ~ game.id|string) %}
                        <div class="alert alert-success bg-transparent border-success text-success">شكراً على تقييمك ✅</div>
                    {% else %}
                        <form action="/rate_game/{{ game.id }}" method="POST">
                            <div class="star-rating mb-3">
                                <input type="radio" id="st5" name="val" value="5" required/><label for="st5" class="fas fa-star"></label>
                                <input type="radio" id="st4" name="val" value="4"/><label for="st4" class="fas fa-star"></label>
                                <input type="radio" id="st3" name="val" value="3"/><label for="st3" class="fas fa-star"></label>
                                <input type="radio" id="st2" name="val" value="2"/><label for="st2" class="fas fa-star"></label>
                                <input type="radio" id="st1" name="val" value="1"/><label for="st1" class="fas fa-star"></label>
                            </div>
                            <button class="btn btn-outline-primary btn-sm d-block mx-auto rounded-pill mb-4">إرسال تقييمك</button>
                        </form>
                    {% endif %}

                    <hr class="border-secondary">
                    <button id="startDownload" class="btn btn-primary w-100 py-3 fs-5 mt-3">تحميل الآن</button>
                    
                    <div id="timerContainer" style="display:none; text-align:center; margin-top:20px;">
                        <p class="small">يتم تجهيز الرابط الآمن...</p>
                        <h1 id="countdown" class="text-primary fw-900">15</h1>
                    </div>
                    <form id="realDownloadForm" action="/count_download/{{ game.id }}" method="POST" style="display:none;"></form>
                </div>
            </div>
        </div>
        <script>
            document.getElementById('startDownload').onclick = function() {
                this.style.display = 'none';
                document.getElementById('timerContainer').style.display = 'block';
                let count = 15;
                let counter = setInterval(function() {
                    count--;
                    document.getElementById('countdown').innerHTML = count;
                    if (count <= 0) { clearInterval(counter); document.getElementById('realDownloadForm').submit(); }
                }, 1000);
            };
        </script>

    {% elif page == 'upload' %}
        <div class="row g-4">
            <div class="col-md-7">
                <div class="admin-card">
                    <h4 class="fw-900 mb-4 text-primary">إضافة لعبة</h4>
                    <form method="POST" action="/upload_game" enctype="multipart/form-data">
                        <input type="text" name="title" class="form-control mb-3" placeholder="اسم اللعبة" required>
                        <textarea name="desc" class="form-control mb-3" rows="4" placeholder="الوصف"></textarea>
                        <label class="small text-primary">الأيقونة الرئيسية:</label>
                        <input type="file" name="main_img" class="form-control mb-3">
                        <label class="small text-primary">لقطات الشاشة (اختر حتى 8 صور):</label>
                        <input type="file" name="screens" class="form-control mb-3" multiple>
                        <input type="text" name="video_url" class="form-control mb-3" placeholder="رابط فيديو (يوتيوب)">
                        <input type="text" name="ext_link" class="form-control mb-3" placeholder="رابط التحميل المباشر">
                        <button type="submit" class="btn btn-primary w-100 py-3">نشر اللعبة</button>
                    </form>
                </div>
                <div class="admin-card">
                    <h5 class="fw-900 mb-3">إدارة الألعاب (حذف)</h5>
                    {% for g in all_games_list %}
                        <div class="d-flex justify-content-between p-2 border-bottom border-secondary mb-2 bg-black rounded">
                            <span>{{ g.title }}</span>
                            <a href="/delete_game/{{ g.id }}" class="btn btn-danger btn-sm" onclick="return confirm('حذف اللعبة؟')">حذف</a>
                        </div>
                    {% endfor %}
                </div>
            </div>
            <div class="col-md-5">
                <div class="admin-card">
                    <h5 class="fw-900 mb-3 text-primary">إدارة السلايدر الرئيسي</h5>
                    <form method="POST" action="/upload_banner" enctype="multipart/form-data" class="mb-4">
                        <input type="text" name="b_title" class="form-control mb-2" placeholder="العنوان" required>
                        <input type="file" name="b_img" class="form-control mb-2" required>
                        <input type="text" name="b_link" class="form-control mb-2" placeholder="الرابط">
                        <button class="btn btn-primary btn-sm w-100">حفظ في السلايدر</button>
                    </form>
                    <hr class="border-secondary">
                    {% for b in banners_list %}
                        <div class="d-flex justify-content-between p-2 mb-2 bg-black rounded">
                            <small>{{ b.title }}</small>
                            <a href="/delete_banner/{{ b.id }}" class="text-danger">حذف</a>
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>

    {% elif page == 'login' %}
        <div class="mx-auto mt-5 text-center" style="max-width: 400px;">
            <div class="p-5 admin-card shadow-lg">
                <h3 class="fw-900 mb-4">الدخول للمسؤول</h3>
                <form method="POST">
                    <input type="password" name="password" class="form-control mb-4 text-center p-3 rounded-pill" placeholder="كلمة السر" required>
                    <button type="submit" class="btn btn-primary w-100 py-3 rounded-pill fw-bold">دخول</button>
                </form>
            </div>
        </div>
    {% endif %}
    </div>

    <footer>
        <div class="container text-center">
            <h2 class="fw-900 text-primary">HIXU STORE</h2>
            <p class="opacity-50 small mb-4">جميع الحقوق محفوظة © 2026</p>
            <div class="d-flex justify-content-center gap-3">
                <a href="https://tiktok.com/@r_tyy7" target="_blank" class="text-white fs-4"><i class="fab fa-tiktok"></i></a>
                <a href="https://t.me/cvbnm_6" target="_blank" class="text-white fs-4"><i class="fab fa-telegram"></i></a>
            </div>
        </div>
        <a href="/login" class="hidden-admin"></a>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    <script>AOS.init({ duration: 800, once: true });</script>
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

@app.route('/rate_game/<int:game_id>', methods=['POST'])
def rate_game(game_id):
    if session.get(f'rated_{game_id}'): return redirect(url_for('details', game_id=game_id))
    game = Game.query.get_or_404(game_id)
    val = request.form.get('val', type=float)
    if val:
        game.rating_sum += val
        game.rating_count += 1
        db.session.commit()
        session[f'rated_{game_id}'] = True
    return redirect(url_for('details', game_id=game_id))

@app.route('/count_download/<int:game_id>', methods=['POST'])
def count_download(game_id):
    game = Game.query.get_or_404(game_id)
    game.downloads_count += 1
    db.session.commit()
    return redirect(game.external_link or '/')

@app.route('/upload')
def upload():
    if not session.get('admin'): return redirect(url_for('login'))
    all_games_list = Game.query.order_by(Game.date_added.desc()).all()
    banners_list = Banner.query.all()
    return render_template_string(MASTER_HTML, page='upload', all_games_list=all_games_list, banners_list=banners_list)

@app.route('/upload_game', methods=['POST'])
def upload_game():
    if not session.get('admin'): abort(403)
    img = request.files.get('main_img')
    screens = request.files.getlist('screens')
    
    img_name = secrets.token_hex(4) + "_" + secure_filename(img.filename) if img and img.filename else None
    if img_name: img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
    
    screen_list = []
    for s in screens[:8]:
        if s.filename:
            s_name = "sc_" + secrets.token_hex(4) + "_" + secure_filename(s.filename)
            s.save(os.path.join(app.config['UPLOAD_FOLDER'], s_name))
            screen_list.append(s_name)
    
    new_game = Game(
        title=request.form['title'], description=request.form['desc'],
        image_filename=img_name, screenshots=",".join(screen_list),
        video_url=request.form.get('video_url'), external_link=request.form.get('ext_link')
    )
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
        img_name = "bn_" + secrets.token_hex(4) + "_" + secure_filename(img.filename)
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

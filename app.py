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

# --- إعداد قاعدة البيانات ---
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
    <title>Hixu Store | Ultra Performance</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <style>
        :root { 
            --primary: #4e73df; 
            --indigo-dark: #1a1a2e; 
            --indigo-card: #16213e; 
            --accent: #0f3460;
            --text-white: #ffffff;
        }
        
        body { 
            background: var(--indigo-dark); 
            font-family: 'Tajawal', sans-serif; 
            color: var(--text-white); 
            overflow-x: hidden; 
        }

        .navbar { 
            background: rgba(22, 33, 62, 0.95); 
            backdrop-filter: blur(12px); 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
            padding: 15px 0; 
            z-index: 1000; 
        }
        .nav-logo { font-weight: 900; font-size: 2rem; color: #fff !important; text-decoration: none; }

        .slider-container { 
            max-width: 1280px; margin: 0 auto 40px auto; 
            border-radius: 30px; overflow: hidden; 
            box-shadow: 0 25px 50px rgba(0,0,0,0.5); 
            border: 2px solid rgba(255,255,255,0.1); 
        }
        .carousel-item { height: 0; padding-bottom: 56.25%; background: #000; position: relative; }
        .carousel-item img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
        .carousel-caption { bottom: 15%; text-align: right; }
        .carousel-caption h2 { color: #fff; font-weight: 900; }

        .hero-title { 
            font-weight: 900; font-size: clamp(2.5rem, 8vw, 4.5rem); 
            background: linear-gradient(45deg, #fff, var(--primary)); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        }
        .search-input { 
            max-width: 600px; margin: 30px auto; 
            border-radius: 50px; padding: 18px 35px; 
            background: var(--indigo-card); 
            border: 1px solid rgba(255,255,255,0.2); 
            color: #fff; text-align: center; 
        }
        .search-input:focus { background: var(--accent); color: #fff; border-color: var(--primary); outline: none; box-shadow: none; }

        .btn-filter { 
            background: var(--indigo-card); border: 1px solid rgba(255,255,255,0.1); 
            color: #fff; padding: 8px 25px; border-radius: 50px; 
            text-decoration: none; font-weight: 700; transition: 0.3s; 
        }
        .btn-filter:hover, .btn-filter.active { background: var(--primary); color: #fff; }

        .game-card { 
            border: none; border-radius: 25px; 
            background: var(--indigo-card); 
            transition: 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
            overflow: hidden; height: 100%; 
            border: 1px solid rgba(255,255,255,0.05); cursor: pointer; 
        }
        .game-card:hover { transform: translateY(-15px); box-shadow: 0 30px 60px rgba(0,0,0,0.4); border-color: var(--primary); }
        .game-img { width: 100%; height: 230px; object-fit: cover; }
        .game-card h6 { color: #fff; }

        .admin-card { background: var(--indigo-card); padding: 30px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.1); color: #fff; }
        .form-control { background: var(--accent); border: 1px solid rgba(255,255,255,0.1); color: #fff !important; }
        .form-control::placeholder { color: rgba(255,255,255,0.5); }
        .management-item { background: var(--accent); padding: 12px 20px; border-radius: 15px; margin-bottom: 8px; color: #fff; border: 1px solid rgba(255,255,255,0.1); }

        .timer-box { background: var(--accent) !important; border-color: var(--primary) !important; color: #fff; }

        footer { padding: 60px 0; text-align: center; background: var(--indigo-card); border-top: 1px solid rgba(255,255,255,0.05); margin-top: 100px; }
        .tiktok-link { background: #ee1d52; color: #fff; padding: 12px 30px; border-radius: 50px; text-decoration: none; font-weight: 900; }
        .telegram-link { background: #0088cc; color: #fff; padding: 12px 30px; border-radius: 50px; text-decoration: none; font-weight: 900; }
        
        /* Modal Style for About, Contact, Privacy */
        .modal-content { background: var(--indigo-card); color: #fff; border: 1px solid var(--primary); border-radius: 25px; }
        .modal-header { border-bottom: 1px solid rgba(255,255,255,0.1); }
        .modal-footer { border-top: 1px solid rgba(255,255,255,0.1); }
        .footer-links-btn { color: rgba(255,255,255,0.6); text-decoration: none; font-size: 0.9rem; margin: 0 10px; transition: 0.3s; cursor: pointer; border:none; background:none; }
        .footer-links-btn:hover { color: var(--primary); }
    </style>
</head>
<body>
    <nav class="navbar sticky-top">
        <div class="container d-flex justify-content-between align-items-center">
            <a class="nav-logo" href="/" data-aos="fade-left">HIXU STORE</a>
            <div class="d-flex align-items-center gap-2">
                <a href="https://t.me/cvbnm_6" target="_blank" class="text-white me-3 fs-4"><i class="fab fa-telegram"></i></a>
                {% if session.get('admin') %}
                    <a href="/upload" class="btn btn-outline-light rounded-pill px-4">لوحة التحكم</a>
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
            <h1 class="hero-title">HIXU STORE</h1>
            <p class="text-light opacity-75 fs-5">استكشف عالم الألعاب بأعلى سرعة وأمان</p>
            <form action="/" method="GET">
                <input type="text" name="q" class="form-control search-input" placeholder="بحث سريع عن الألعاب..." value="{{ q }}">
            </form>
            <div class="d-flex justify-content-center gap-2 mb-5 flex-wrap">
                <a href="/?sort=new" class="btn-filter {% if sort == 'new' or sort == '' %}active{% endif %}">الأحدث</a>
                <a href="/?sort=trend" class="btn-filter {% if sort == 'trend' %}active{% endif %}">الأكثر تحميلاً</a>
                <a href="/?sort=old" class="btn-filter {% if sort == 'old' %}active{% endif %}">الأقدم</a>
            </div>
        </div>

        <div class="row g-4">
            {% for game in games %}
            <div class="col-6 col-md-4 col-lg-3" data-aos="fade-up">
                <div class="game-card" onclick="location.href='/game/{{ game.id }}'">
                    <img src="{{ url_for('uploaded_file', filename=game.image_filename) if game.image_filename else 'https://via.placeholder.com/400x300/16213e/ffffff?text=Hixu+Store' }}" class="game-img">
                    <div class="p-4 text-center">
                        <h6 class="fw-bold mb-3 text-truncate">{{ game.title }}</h6>
                        <span class="btn btn-primary rounded-pill btn-sm px-4">تفاصيل اللعبة</span>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

    {% elif page == 'details' %}
        <div class="mx-auto mt-5" style="max-width: 1100px;" data-aos="fade-up">
            <div class="video-container" style="border-radius: 30px; overflow: hidden; background: #000; box-shadow: 0 30px 60px rgba(0,0,0,0.5);">
                {% if game.video_url %}
                    {% set video_id = game.video_url.split('v=')[-1] if 'v=' in game.video_url else game.video_url.split('/')[-1] %}
                    <iframe src="https://www.youtube.com/embed/{{ video_id }}?autoplay=1&rel=0" style="width: 100%; aspect-ratio: 16/9;" frameborder="0" allowfullscreen></iframe>
                {% else %}
                    <img src="{{ url_for('uploaded_file', filename=game.image_filename) }}" class="w-100">
                {% endif %}
            </div>
            <div class="p-5 bg-white bg-opacity-10 rounded-5 shadow-lg mt-4 border border-secondary">
                <div class="d-flex justify-content-between align-items-center">
                    <h1 class="fw-900 text-white">{{ game.title }}</h1>
                    <span class="badge bg-primary px-3 py-2 rounded-pill">تحميلات: {{ game.downloads_count }}</span>
                </div>
                <p class="fs-5 text-light mt-4" style="line-height: 2;">{{ game.description }}</p>
                <button id="startDownload" class="btn btn-success btn-lg w-100 py-4 rounded-pill fw-900 mt-5 shadow-lg">
                    <i class="fas fa-bolt me-2"></i> بدء التحميل المباشر
                </button>
                <div id="timerContainer" class="timer-box" style="display:none; text-align:center; padding: 40px; border-radius: 30px; margin-top: 30px; border: 2px dashed #2563eb;">
                    <p class="fw-bold fs-4">جاري تجهيز الرابط الآمن...</p>
                    <div style="font-size: 5rem; font-weight: 900; color: #fff;" id="countdown">15</div>
                </div>
                <form id="realDownloadForm" action="/count_download/{{ game.id }}" method="POST" style="display:none;"></form>
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
                    if (count <= 0) {
                        clearInterval(counter);
                        document.getElementById('realDownloadForm').submit();
                    }
                }, 1000);
            };
        </script>

    {% elif page == 'upload' %}
        <div class="row g-4">
            <div class="col-md-7">
                <div class="admin-card">
                    <h4 class="fw-900 mb-4 text-primary">إضافة لعبة جديدة</h4>
                    <form method="POST" action="/upload_game" enctype="multipart/form-data">
                        <input type="text" name="title" class="form-control mb-3 p-3 rounded-4" placeholder="اسم اللعبة" required>
                        <textarea name="desc" class="form-control mb-3 p-3 rounded-4" rows="4" placeholder="وصف اللعبة"></textarea>
                        <label class="small text-light ms-2">صورة اللعبة:</label>
                        <input type="file" name="img_file" class="form-control mb-3 p-2 rounded-4">
                        <input type="text" name="video_url" class="form-control mb-3 p-3 rounded-4" placeholder="رابط فيديو (يوتيوب)">
                        <label class="small text-light ms-2">ملف اللعبة (اختياري):</label>
                        <input type="file" name="game_file" class="form-control mb-3 p-2 rounded-4">
                        <input type="text" name="ext_link" class="form-control mb-3 p-3 rounded-4" placeholder="أو رابط خارجي مباشر">
                        <button type="submit" class="btn btn-primary w-100 py-3 fw-bold rounded-pill">نشر الآن</button>
                    </form>
                </div>
            </div>
            <div class="col-md-5">
                <div class="admin-card">
                    <h5 class="fw-900 mb-4">إدارة المحتوى</h5>
                    <p class="fw-bold text-light border-bottom pb-2">إضافة سلايدر</p>
                    <form method="POST" action="/upload_banner" enctype="multipart/form-data" class="mb-4">
                        <input type="text" name="b_title" class="form-control mb-2 rounded-4" placeholder="العنوان" required>
                        <input type="file" name="b_img" class="form-control mb-2 rounded-4" required>
                        <input type="text" name="b_link" class="form-control mb-2 rounded-4" placeholder="الرابط عند الضغط">
                        <button class="btn btn-success btn-sm w-100 rounded-pill">حفظ السلايدر</button>
                    </form>
                    <p class="fw-bold text-danger border-bottom pb-2 mt-4">حذف السلايدرات</p>
                    <div style="max-height: 200px; overflow-y: auto;">
                        {% for b in all_banners %}
                        <div class="management-item d-flex justify-content-between">
                            <span class="text-truncate" style="max-width: 150px;">{{ b.title }}</span>
                            <a href="/delete_banner/{{ b.id }}" class="btn btn-danger btn-sm rounded-pill">حذف</a>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

    {% elif page == 'login' %}
        <div class="mx-auto mt-5 text-center" style="max-width: 450px;">
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
        <div class="container">
            <h2 class="fw-900 text-white mb-3">HIXU STORE</h2>
            <p class="text-light opacity-50 small mb-4">جميع الحقوق محفوظة © 2026</p>
            
            <div class="mb-4">
                <button class="footer-links-btn" data-bs-toggle="modal" data-bs-target="#aboutModal">About Us</button>
                <button class="footer-links-btn" data-bs-toggle="modal" data-bs-target="#contactModal">Contact Us</button>
                <button class="footer-links-btn" data-bs-toggle="modal" data-bs-target="#privacyModal">Privacy Policy</button>
            </div>

            <div class="social-links d-flex justify-content-center gap-3">
                <a href="https://tiktok.com/@r_tyy7" target="_blank" class="tiktok-link"><i class="fab fa-tiktok me-2"></i>TikTok</a>
                <a href="https://t.me/cvbnm_6" target="_blank" class="telegram-link"><i class="fab fa-telegram me-2"></i>Telegram</a>
            </div>
            <a href="/login" style="opacity: 0.2; color: #fff; font-size: 0.7rem; text-decoration: none;" class="mt-5 d-inline-block">Admin Terminal</a>
        </div>
    </footer>

    <div class="modal fade" id="aboutModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header"><h5 class="modal-title">About Us | من نحن</h5></div>
                <div class="modal-body text-end">
                    مرحباً بكم في HIXU STORE، وجهتكم الأولى لتحميل أفضل الألعاب والتطبيقات الحصرية. نحن نسعى لتقديم تجربة تحميل آمنة وسريعة لجميع المستخدمين مع واجهة عصرية وسهلة الاستخدام.
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="contactModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header"><h5 class="modal-title">Contact Us | تواصل معنا</h5></div>
                <div class="modal-body">
                    لأي استفسارات أو طلبات برمجية، يمكنك التواصل معنا مباشرة عبر البريد الإلكتروني:<br>
                    <a href="mailto:osama2009th3@gmail.com" class="text-primary fw-bold">osama2009th3@gmail.com</a>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="privacyModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header"><h5 class="modal-title">Privacy Policy | سياسة الخصوصية</h5></div>
                <div class="modal-body text-end">
                    نحن في HIXU STORE نحترم خصوصيتك. لا نقوم بجمع أي بيانات شخصية حساسة عن الزوار. الملفات المرفوعة يتم فحصها بدقة لضمان أمان جهازك، واستخدام الكوكيز يقتصر فقط على تحسين تجربة التصفح وحفظ الجلسات.
                </div>
            </div>
        </div>
    </div>

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

@app.route('/count_download/<int:game_id>', methods=['POST'])
def count_download(game_id):
    game = Game.query.get_or_404(game_id)
    game.downloads_count += 1
    db.session.commit()
    if game.file_filename: 
        return redirect(url_for('uploaded_file', filename=game.file_filename))
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
    
    new_game = Game(
        title=request.form['title'], 
        description=request.form['desc'], 
        image_filename=img_name, 
        file_filename=file_name, 
        video_url=request.form.get('video_url'), 
        external_link=request.form.get('ext_link')
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

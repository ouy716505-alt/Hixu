import os
import secrets
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, abort, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# --- [ إعدادات التطبيق الأساسية ] ---
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(64)),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,  # 20MB Max
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True, # تفعل عند استخدام HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    UPLOAD_FOLDER=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
)

# --- [ تهيئة الحماية والخدمات ] ---
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])

# --- [ قاعدة البيانات المطورة ] ---
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=True, nullable=False)
    slug = db.Column(db.String(150), unique=True) # لروابط SEO
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default="Action")
    version = db.Column(db.String(20), default="1.0.0")
    size = db.Column(db.String(20))
    system_req = db.Column(db.String(100), default="Windows 10/11")
    
    main_image = db.Column(db.String(200))
    video_url = db.Column(db.String(500))
    download_link = db.Column(db.String(500))
    
    views = db.Column(db.Integer, default=0)
    downloads = db.Column(db.Integer, default=0)
    rating_score = db.Column(db.Float, default=5.0)
    rating_count = db.Column(db.Integer, default=1)
    is_trending = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self): return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Analytics(db.Model): # لتخزين الزيارات اليومية
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date(), unique=True)
    page_views = db.Column(db.Integer, default=0)

# --- [ الواجهة الرسومية الاحترافية ] ---
# ملاحظة: تم استخدام Tailwind CSS + Custom Neon CSS للتحكم الكامل في الفخامة
MASTER_UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HIXU STORE | {{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Cairo:wght@300;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        :root { --neon-green: #00ff41; --dark-core: #020202; }
        body { background-color: var(--dark-core); font-family: 'Cairo', sans-serif; color: #e5e7eb; scroll-behavior: smooth; }
        .font-gaming { font-family: 'Orbitron', sans-serif; }
        
        .neon-border { border: 1px solid rgba(0, 255, 65, 0.2); box-shadow: 0 0 15px rgba(0, 255, 65, 0.1); }
        .neon-text { color: var(--neon-green); text-shadow: 0 0 10px rgba(0, 255, 65, 0.5); }
        .glass-nav { background: rgba(2, 2, 2, 0.8); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.05); }
        
        .game-card { transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); background: #0a0a0a; overflow: hidden; border-radius: 1.5rem; position: relative; }
        .game-card:hover { transform: translateY(-10px) scale(1.02); box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 20px rgba(0, 255, 65, 0.2); border: 1px solid var(--neon-green); }
        
        .hero-gradient { background: radial-gradient(circle at 50% 50%, rgba(0, 255, 65, 0.1) 0%, transparent 70%); }
        
        /* Skeleton Loading */
        .skeleton { background: linear-gradient(90deg, #121212 25%, #1a1a1a 50%, #121212 75%); background-size: 200% 100%; animation: loading 1.5s infinite; }
        @keyframes loading { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        
        .btn-primary { background: var(--neon-green); color: #000; font-weight: 900; transition: 0.3s; border-radius: 9999px; box-shadow: 0 0 20px rgba(0, 255, 65, 0.3); }
        .btn-primary:hover { transform: scale(1.05); box-shadow: 0 0 30px var(--neon-green); }
    </style>
</head>
<body class="overflow-x-hidden">

    <nav class="glass-nav fixed w-full z-50 px-6 py-4 flex justify-between items-center">
        <a href="/" class="font-gaming text-3xl neon-text font-black tracking-tighter">HIXU STORE</a>
        <div class="hidden md:flex space-x-8 rtl:space-x-reverse items-center">
            <a href="/" class="hover:neon-text transition">المتجر</a>
            <a href="/?filter=trending" class="hover:neon-text transition">الرائج</a>
            <a href="/?filter=top" class="hover:neon-text transition">الأعلى تقييماً</a>
            <form action="/" method="GET" class="relative">
                <input type="text" name="q" placeholder="ابحث عن لعبتك..." class="bg-black/50 border border-white/10 rounded-full px-5 py-2 w-64 focus:border-neon-green outline-none transition">
                <i class="fas fa-search absolute left-4 top-3 text-gray-500"></i>
            </form>
        </div>
        <div class="flex items-center space-x-4">
            {% if session.admin %}
                <a href="/admin" class="bg-white/10 p-2 px-4 rounded-full text-sm hover:bg-white/20 transition"><i class="fas fa-user-shield ml-2"></i>الأدمن</a>
            {% endif %}
            <button class="md:hidden text-2xl"><i class="fas fa-bars"></i></button>
        </div>
    </nav>

    <div class="pt-24 min-h-screen">
        {% if page == 'home' %}
            <section class="px-6 mb-16 relative" data-aos="zoom-out">
                <div class="hero-gradient absolute inset-0 pointer-events-none"></div>
                <div class="max-w-7xl mx-auto rounded-[3rem] overflow-hidden neon-border h-[500px] relative">
                    <img src="https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=2070" class="w-full h-full object-cover opacity-60">
                    <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent p-12 flex flex-col justify-end">
                        <span class="bg-neon-green text-black px-4 py-1 rounded-full text-xs font-bold w-fit mb-4">حصرياً في HIXU</span>
                        <h1 class="font-gaming text-6xl font-black mb-4">GAMING UNLEASHED</h1>
                        <p class="text-xl text-gray-400 max-w-2xl mb-8">استكشف مكتبة ضخمة من الألعاب الاحترافية بروابط مباشرة وسرعة تحميل فائقة.</p>
                        <div class="flex space-x-4 rtl:space-x-reverse">
                            <button class="btn-primary px-10 py-4 fs-5">استكشف الآن</button>
                            <button class="bg-white/5 backdrop-blur-md border border-white/10 px-10 py-4 rounded-full font-bold hover:bg-white/10">المزيد</button>
                        </div>
                    </div>
                </div>
            </section>

            <main class="max-w-7xl mx-auto px-6 pb-20">
                <div class="flex justify-between items-end mb-10">
                    <div>
                        <h2 class="text-3xl font-bold mb-2">أحدث الإصدارات</h2>
                        <div class="h-1 w-20 bg-neon-green"></div>
                    </div>
                    <div class="flex space-x-2 rtl:space-x-reverse">
                        <button class="bg-white/5 p-3 rounded-xl hover:bg-neon-green hover:text-black transition"><i class="fas fa-th-large"></i></button>
                        <button class="bg-white/5 p-3 rounded-xl"><i class="fas fa-list"></i></button>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {% for game in games %}
                    <div class="game-card group" data-aos="fade-up" data-aos-delay="{{ loop.index0 * 100 }}">
                        <div class="relative h-64 overflow-hidden">
                            <img src="{{ url_for('uploaded_file', filename=game.main_image) if game.main_image else 'https://via.placeholder.com/400' }}" class="w-full h-full object-cover transition duration-700 group-hover:scale-110">
                            <div class="absolute top-4 right-4 bg-black/60 backdrop-blur-md px-3 py-1 rounded-lg text-sm border border-white/10">
                                <i class="fas fa-star text-yellow-500 mr-1"></i> {{ game.rating_score }}
                            </div>
                        </div>
                        <div class="p-6">
                            <h3 class="font-bold text-xl mb-2 group-hover:neon-text transition">{{ game.title }}</h3>
                            <div class="flex justify-between text-gray-500 text-sm mb-4">
                                <span><i class="fas fa-hdd ml-1"></i> {{ game.size }}</span>
                                <span><i class="fas fa-tags ml-1"></i> {{ game.category }}</span>
                            </div>
                            <a href="/game/{{ game.id }}" class="block text-center border border-white/10 group-hover:border-neon-green py-3 rounded-xl transition font-bold">عرض التفاصيل</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </main>

        {% elif page == 'admin' %}
            <div class="max-w-7xl mx-auto px-6 py-10">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
                    <div class="bg-black/40 border border-white/5 p-8 rounded-[2rem] neon-border">
                        <p class="text-gray-500 font-bold mb-2">إجمالي الألعاب</p>
                        <h2 class="text-4xl font-gaming neon-text">{{ stats.total_games }}</h2>
                    </div>
                    <div class="bg-black/40 border border-white/5 p-8 rounded-[2rem]">
                        <p class="text-gray-500 font-bold mb-2">التحميلات</p>
                        <h2 class="text-4xl font-gaming">{{ stats.total_downloads }}</h2>
                    </div>
                    <div class="bg-black/40 border border-white/5 p-8 rounded-[2rem]">
                        <p class="text-gray-500 font-bold mb-2">المشاهدات</p>
                        <h2 class="text-4xl font-gaming">{{ stats.total_views }}</h2>
                    </div>
                    <div class="bg-black/40 border border-white/5 p-8 rounded-[2rem]">
                        <p class="text-gray-500 font-bold mb-2">معدل التقييم</p>
                        <h2 class="text-4xl font-gaming text-yellow-500">4.9</h2>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="bg-black/40 p-8 rounded-[2rem] border border-white/5">
                        <h3 class="text-xl font-bold mb-6">إحصائيات الزيارات</h3>
                        <canvas id="analyticsChart"></canvas>
                    </div>
                    <div class="bg-black/40 p-8 rounded-[2rem] border border-white/5">
                        <h3 class="text-xl font-bold mb-6">إضافة لعبة جديدة</h3>
                        <form action="/admin/add" method="POST" enctype="multipart/form-data" class="space-y-4">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <input type="text" name="title" placeholder="اسم اللعبة" class="w-full bg-black/50 border border-white/10 p-4 rounded-2xl outline-none focus:border-neon-green">
                            <div class="grid grid-cols-2 gap-4">
                                <input type="text" name="category" placeholder="التصنيف" class="bg-black/50 border border-white/10 p-4 rounded-2xl outline-none focus:border-neon-green">
                                <input type="text" name="size" placeholder="الحجم (مثال: 50GB)" class="bg-black/50 border border-white/10 p-4 rounded-2xl outline-none focus:border-neon-green">
                            </div>
                            <textarea name="description" placeholder="وصف اللعبة" class="w-full bg-black/50 border border-white/10 p-4 rounded-2xl h-32 outline-none focus:border-neon-green"></textarea>
                            <div class="border-2 border-dashed border-white/10 p-8 rounded-2xl text-center hover:border-neon-green transition cursor-pointer relative">
                                <input type="file" name="main_image" class="absolute inset-0 opacity-0 cursor-pointer">
                                <p class="text-gray-500">اسحب صورة الغلاف هنا أو اضغط للرفع</p>
                            </div>
                            <input type="text" name="download_link" placeholder="رابط التحميل المباشر" class="w-full bg-black/50 border border-white/10 p-4 rounded-2xl outline-none focus:border-neon-green">
                            <button type="submit" class="btn-primary w-full py-4 text-lg">نشر اللعبة الآن</button>
                        </form>
                    </div>
                </div>
            </div>
            <script>
                const ctx = document.getElementById('analyticsChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                        datasets: [{
                            label: 'الزيارات',
                            data: [65, 59, 80, 81, 56, 55, 90],
                            borderColor: '#00ff41',
                            backgroundColor: 'rgba(0, 255, 65, 0.1)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: { plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(255,255,255,0.05)' } } } }
                });
            </script>
        {% endif %}
    </div>

    <footer class="bg-black py-20 border-t border-white/5 mt-20">
        <div class="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
            <div class="col-span-2">
                <h2 class="font-gaming text-3xl neon-text mb-6">HIXU STORE</h2>
                <p class="text-gray-500 max-w-sm mb-8">الوجهة الأولى للاعبين العرب لتحميل أحدث الألعاب وأكثرها قوة بأعلى معايير الأمان والأداء.</p>
                <div class="flex space-x-4 rtl:space-x-reverse">
                    <a href="#" class="w-12 h-12 bg-white/5 flex items-center justify-center rounded-full hover:bg-neon-green hover:text-black transition"><i class="fab fa-telegram"></i></a>
                    <a href="#" class="w-12 h-12 bg-white/5 flex items-center justify-center rounded-full hover:bg-neon-green hover:text-black transition"><i class="fab fa-discord"></i></a>
                    <a href="#" class="w-12 h-12 bg-white/5 flex items-center justify-center rounded-full hover:bg-neon-green hover:text-black transition"><i class="fab fa-tiktok"></i></a>
                </div>
            </div>
            <div>
                <h4 class="font-bold mb-6">روابط سريعة</h4>
                <ul class="space-y-4 text-gray-500">
                    <li><a href="#" class="hover:text-white transition">سياسة الخصوصية</a></li>
                    <li><a href="#" class="hover:text-white transition">شروط الخدمة</a></li>
                    <li><a href="#" class="hover:text-white transition">تواصل معنا</a></li>
                </ul>
            </div>
            <div>
                <h4 class="font-bold mb-6">النشرة الإخبارية</h4>
                <p class="text-gray-500 mb-4 text-sm">اشترك لتصلك أحدث الألعاب المضافة فوراً.</p>
                <div class="relative">
                    <input type="email" placeholder="بريدك الإلكتروني" class="w-full bg-white/5 border border-white/10 p-3 rounded-lg focus:border-neon-green outline-none">
                    <button class="absolute left-2 top-2 bg-neon-green text-black px-4 py-1 rounded-md font-bold">تم</button>
                </div>
            </div>
        </div>
    </footer>

    <script> AOS.init({ duration: 1000, once: true }); </script>
</body>
</html>
"""

# --- [ منطق التحكم (Logic & Security) ] ---

@app.before_request
def track_analytics():
    today = datetime.utcnow().date()
    stat = Analytics.query.filter_by(date=today).first()
    if not stat:
        stat = Analytics(date=today, page_views=1)
        db.session.add(stat)
    else:
        stat.page_views += 1
    db.session.commit()

@app.route('/')
def home():
    games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template_string(MASTER_UI, page='home', title="Home", games=games)

@app.route('/game/<int:game_id>')
def game_details(game_id):
    game = Game.query.get_or_404(game_id)
    game.views += 1
    db.session.commit()
    # يمكن إضافة صفحة تفاصيل مشابهة لـ Steam هنا
    return render_template_string(MASTER_UI, page='details', title=game.title, game=game)

@app.route('/admin')
def admin_panel():
    if not session.get('admin'): return redirect(url_for('admin_login'))
    stats = {
        'total_games': Game.query.count(),
        'total_downloads': db.session.query(db.func.sum(Game.downloads)).scalar() or 0,
        'total_views': db.session.query(db.func.sum(Game.views)).scalar() or 0
    }
    return render_template_string(MASTER_UI, page='admin', title="Admin Panel", stats=stats)

@app.route('/admin/add', methods=['POST'])
@limiter.limit("5 per minute")
def add_game():
    if not session.get('admin'): abort(403)
    
    file = request.files.get('main_image')
    filename = None
    if file and file.filename != '':
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext in {'png', 'jpg', 'jpeg', 'webp'}:
            filename = secrets.token_hex(16) + '.' + ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_game = Game(
        title=request.form['title'],
        description=request.form['description'],
        category=request.form['category'],
        size=request.form['size'],
        download_link=request.form['download_link'],
        main_image=filename
    )
    db.session.add(new_game)
    db.session.commit()
    flash("تمت إضافة اللعبة بنجاح")
    return redirect(url_for('admin_panel'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # استخدام Password Hash مستقبلاً لمزيد من الأمان
        if request.form.get('password') == os.environ.get('ADMIN_PASS', '8461893480'):
            session['admin'] = True
            session.permanent = True
            return redirect(url_for('admin_panel'))
    return render_template_string(MASTER_UI, page='login', title="Login")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- [ التشغيل ] ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False) # دائماً False في الإنتاج

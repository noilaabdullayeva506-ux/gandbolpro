import os
import random
import string
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gandbolpro-dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "gandbolpro.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------------------------------------------------------
# MODELS
# ------------------------------------------------------------------

class Settings(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(50))


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, default=20)
    position = db.Column(db.String(80), default="Markaziy")
    group = db.Column(db.String(20), default="tajriba")  # tajriba | nazorat

    pre_vo2 = db.Column(db.Float)
    pre_rsa = db.Column(db.Float)
    pre_fitness = db.Column(db.Float)
    post_vo2 = db.Column(db.Float)
    post_rsa = db.Column(db.Float)
    post_fitness = db.Column(db.Float)

    user = db.relationship("User", backref="player", uselist=False)
    results = db.relationship("Result", backref="player", cascade="all, delete-orphan",
                              order_by="desc(Result.created_at)")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # coach | athlete
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    test_name = db.Column(db.String(80))
    phase = db.Column(db.String(20))  # pretest | posttest
    result_text = db.Column(db.String(200))
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            u = current_user()
            if not u:
                return redirect(url_for("login"))
            if role and u.role != role:
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapper
    return deco


def get_phase():
    row = db.session.get(Settings, "phase")
    return row.value if row else "pretest"


def set_phase(val):
    row = db.session.get(Settings, "phase")
    if not row:
        row = Settings(key="phase", value=val)
        db.session.add(row)
    else:
        row.value = val
    db.session.commit()


def slugify_surname(name):
    cleaned = name.strip().lower()
    repl = {"o'": "o", "g'": "g", "ʻ": "", "ʼ": "", "`": "", "'": ""}
    for a, b in repl.items():
        cleaned = cleaned.replace(a, b)
    cleaned = "".join(c for c in cleaned if c.isalnum() or c.isspace()).strip()
    first_word = cleaned.split()[0] if cleaned.split() else "sportchi"
    return first_word


def unique_login(name):
    base = slugify_surname(name)
    login = base
    i = 1
    while User.query.filter_by(username=login).first():
        i += 1
        login = f"{base}{i}"
    return login


def random_password():
    return "".join(random.choice(string.digits) for _ in range(4))


# ------------------------------------------------------------------
# TEST FORMULAS
# ------------------------------------------------------------------

BLEEP_SPEEDS = [8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5,
                14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5]


def calc_yoyo(dist):
    return round(dist * 0.0084 + 36.4, 1)


def calc_bleep(level, age):
    v = BLEEP_SPEEDS[min(level - 1, len(BLEEP_SPEEDS) - 1)] if level >= 1 else 8.0
    vo2 = 31.025 + 3.238 * v - 3.248 * age + 0.1536 * v * age
    return round(max(0, vo2), 1)


def calc_ift(vift, age, weight, gender):
    vo2 = 28.3 - 2.15 * gender - 0.741 * age - 0.0357 * weight + 0.0586 * age * vift + 1.03 * vift
    return round(max(0, vo2), 1)


def calc_hgbpt(times, hits, total):
    avg = round(sum(times) / len(times), 2)
    best = round(min(times), 2)
    fi = round((avg - best) / best * 100, 1) if best else 0
    acc = round(hits / total * 100) if total else 0
    fitness = min(100, max(10, round(acc * 0.6 + (100 - fi * 2) * 0.4)))
    return avg, best, fi, acc, fitness


def apply_rpe(fitness, rpe):
    if fitness is None:
        fitness = 50
    if rpe >= 19:
        fitness = max(10, fitness - 8)
    elif rpe >= 17:
        fitness = max(20, fitness - 4)
    elif rpe >= 15:
        fitness = max(30, fitness - 1)
    elif rpe <= 10:
        fitness = min(100, fitness + 3)
    elif rpe <= 13:
        fitness = min(100, fitness + 1)
    return fitness


# ------------------------------------------------------------------
# 12-HAFTALIK MASHG'ULOT DASTURI (HAR BIRI 100% TURLICHA VA O'ZIGA XOS)
# ------------------------------------------------------------------

def _week(n, stage, title, goal, intensity, days):
    return {"n": n, "stage": stage, "title": title, "goal": goal, "intensity": intensity, "days": days}

WEEKS_DATA = {
    1: {
        'stage': 'I', 'title': '1-hafta — Aerob poydevor va yugurish bazasi',
        'goal': 'Umumiy aerob chidamlilik va yurak-qon tomir tizimini ishga tushirish',
        'intensity': '60–70% YUQSmax',
        'days': [
            ('Dushanba', 'Uzluksiz bir maromdagi yugurish', '30 daqiqa', 62, '—'),
            ('Seshanba', 'Texnik to‘p uzatish va ushlab qolish', '45 daqiqa', 68, '—'),
            ('Chorshanba', 'Yengil tiknovchi faol dam', '20 daqiqa', 45, '—'),
            ('Payshanba', 'Fartlek (erkin tezlikdagi yugurish)', '25 daqiqa', 70, '—'),
            ('Juma', 'Qisqa intervalli yugurish: 6×3 daqiqa', '18 daqiqa', 75, '90 sek'),
            ('Shanba', 'Asosiy qoidalar va harakatli o‘yin', '60 daqiqa', 65, '—')
        ]
    },
    2: {
        'stage': 'I', 'title': '2-hafta — Aerob hajmni bosqichma-bosqich oshirish',
        'goal': 'Ish qobiliyati davomiyligini uzaytirish va tayyorgarlikni kuchaytirish',
        'intensity': '65–75% YUQSmax',
        'days': [
            ('Dushanba', 'O‘zgaruvchan tezlikdagi kross', '35 daqiqa', 68, '—'),
            ('Seshanba', 'To‘p bilan harakatli texnik kompleks', '50 daqiqa', 72, '—'),
            ('Chorshanba', 'Nafas olish va cho‘zilish mashqlari', '20 daqiqa', 48, '—'),
            ('Payshanba', 'To‘p bilan firtlek va yugurish', '30 daqiqa', 74, '—'),
            ('Juma', 'Aerob interval: 5×4 daqiqa', '20 daqiqa', 78, '90 sek'),
            ('Shanba', 'Hujum va himoya asoslari (3vs3)', '60 daqiqa', 70, '2 daqiqa')
        ]
    },
    3: {
        'stage': 'I', 'title': '3-hafta — Aerob-maxsus chidamlilik',
        'goal': 'Gandbol harakatlariga mos uzun muddatli yuklamalarga o‘tish',
        'intensity': '70–78% YUQSmax',
        'days': [
            ('Dushanba', 'Masofaga chidamli yugurish', '35 daqiqa', 72, '—'),
            ('Seshanba', 'To‘p bilan tezkor uzatmalar va kombinatsiyalar', '50 daqiqa', 75, '—'),
            ('Chorshanba', 'Erkin faol tiklanish', '20 daqiqa', 50, '—'),
            ('Payshanba', 'Yo‘nalishni tez o‘zgartirib yugurish', '30 daqiqa', 76, '—'),
            ('Juma', 'Intensiv aerob interval: 4×5 daqiqa', '20 daqiqa', 80, '90 sek'),
            ('Shanba', 'Kichik maydon o‘yini (4vs4)', '60 daqiqa', 75, '2 daqiqa')
        ]
    },
    4: {
        'stage': 'I', 'title': '4-hafta — Aerob bosqichni yakunlash va test oldi tayyorgarlik',
        'goal': 'Birinchi bosqich natijalarini mustahkamlash',
        'intensity': '72–80% YUQSmax',
        'days': [
            ('Dushanba', 'Uzluksiz tempdagi uzoq yugurish', '40 daqiqa', 75, '—'),
            ('Seshanba', 'Texnik-taktik seriyali mashqlar', '50 daqiqa', 78, '—'),
            ('Chorshanba', 'Yengil tiklanish va massaj elementlari', '20 daqiqa', 50, '—'),
            ('Payshanba', 'Fartlek va qisqa portlovchi tezlanishlar', '30 daqiqa', 78, '—'),
            ('Juma', 'Interval qism: 3×6 daqiqa', '18 daqiqa', 82, '2 daqiqa'),
            ('Shanba', 'Nazorat o‘yini (To‘liq vaqt)', '60 daqiqa', 78, '3 daqiqa')
        ]
    },
    5: {
        'stage': 'II', 'title': '5-hafta — Glikolitik o‘tish va qisqa HIIT',
        'goal': 'Anaerob energiyani yoqish va laktatga chidamlilikni boshlash',
        'intensity': '80–88% YUQSmax',
        'days': [
            ('Dushanba', 'Qisqa HIIT protokoli: 4×3 daqiqa', '12 daqiqa', 85, '2.5 daqiqa'),
            ('Seshanba', '20 metrli takroriy sprint seriyalari', '5×4 takror', 88, '45 sek'),
            ('Chorshanba', 'Faol tiklanish va harakatchanlik', '25 daqiqa', 52, '—'),
            ('Payshanba', 'Yonlama siljishlar + darvozaga otish', '5×4 takror', 86, '60 sek'),
            ('Juma', 'Kichik maydonda shiddatli o‘yin (3vs3)', '4×4 daqiqa', 88, '2 daqiqa'),
            ('Shanba', 'Taktik kombinatsiyalashgan o‘yin', '60 daqiqa', 82, '—')
        ]
    },
    6: {
        'stage': 'II', 'title': '6-hafta — Tezkor-kuch va portlovchi chidamlilik',
        'goal': 'Sakrash va keskin tezlanishlar sifatini yuqori charchoqda ushlash',
        'intensity': '82–90% YUQSmax',
        'days': [
            ('Dushanba', 'Maksimal tezlikdagi sprintlar: 6×25m', '4 seriya', 90, '50 sek'),
            ('Seshanba', 'To‘siqdan sakrash + tezkor qarshi hujum', '5×5 takror', 88, '60 sek'),
            ('Chorshanba', 'Regeneratsiya va yengil cho‘zilish', '25 daqiqa', 50, '—'),
            ('Payshanba', 'Himoyada zich siljish va pressing', '6×40 sek', 89, '70 sek'),
            ('Juma', 'Dinamik o‘yin seriyasi (4vs4)', '5×4 daqiqa', 90, '2 daqiqa'),
            ('Shanba', 'Hujum elementlariga asoslangan o‘yin', '60 daqiqa', 85, '—')
        ]
    },
    7: {
        'stage': 'II', 'title': '7-hafta — Anaerob laktatsid maksimal quvvat',
        'goal': 'Laktat kislotasiga tolerantlikni (chidashni) oshirish',
        'intensity': '85–93% YUQSmax',
        'days': [
            ('Dushanba', '15 soniyali o‘ta yuqori intensiv intervallar', '4×5 takror', 92, '30 sek'),
            ('Seshanba', 'Slalom yugurish va to‘p bilan yakunlash', '5×5 takror', 93, '50 sek'),
            ('Chorshanba', 'Tiknovchi yengil mashg‘ulot', '25 daqiqa', 55, '—'),
            ('Payshanba', 'Tezkor qarshi hujumga chiqish (Counter-attack)', '6×3 daqiqa', 90, '90 sek'),
            ('Juma', 'Shiddatli kichik o‘yin (5vs5)', '5×4 daqiqa', 92, '2 daqiqa'),
            ('Shanba', 'Katta maydon sinov o‘yini', '2×30 daqiqa', 86, '5 daqiqa')
        ]
    },
    8: {
        'stage': 'II', 'title': '8-hafta — Glikolitik bosqichni yakunlash',
        'goal': 'Ikkinchi bosqich yuklamalarini barqarorlashtirish va laktatni boshqarish',
        'intensity': '85–95% YUQSmax',
        'days': [
            ('Dushanba', 'To‘liq intensivlikdagi HIIT: 4×4 daqiqa', '16 daqiqa', 93, '3 daqiqa'),
            ('Seshanba', 'Seriyali tezlanish va darvozaga sakrab otish', '6×4 takror', 94, '45 sek'),
            ('Chorshanba', 'Faol dam olish', '25 daqiqa', 50, '—'),
            ('Payshanba', 'Hujum va himoyada shiddatli almashinuv', '6×4 daqiqa', 91, '90 sek'),
            ('Juma', 'Model o‘yin sharoiti', '5×5 daqiqa', 92, '2 daqiqa'),
            ('Shanba', 'Musobaqaga yaqin nazorat uchrashuvi', '60 daqiqa', 88, '—')
        ]
    },
    9: {
        'stage': 'III', 'title': '9-hafta — Musobaqaga xos o‘yin ritmi',
        'goal': 'O‘yin sharoitidagi maxsus chidamlilik va portlovchi harakatlarni uzviylashtirish',
        'intensity': '88–95% YUQSmax',
        'days': [
            ('Dushanba', 'O‘yin tempidagi 5vs5 kichik maydon', '5×5 daqiqa', 90, '2 daqiqa'),
            ('Seshanba', 'Tezkor chiqish va aniq nishonga otish', '6×4 takror', 92, '60 sek'),
            ('Chorshanba', 'Texnik elementlar va tiklanish', '25 daqiqa', 50, '—'),
            ('Payshanba', 'Himoyadan hujumga o‘tish tezligi', '6×4 daqiqa', 91, '90 sek'),
            ('Juma', 'O‘yin qismlarini modellashtirish', '4×7 daqiqa', 93, '3 daqiqa'),
            ('Shanba', 'Rasmiy formatdagi o‘yin', '2×30 daqiqa', 89, '10 daqiqa')
        ]
    },
    10: {
        'stage': 'III', 'title': '10-hafta — Hujum va himoyada barqarorlik',
        'goal': 'Og‘ir charchoq paytida ham taktik ongli va aniq harakat qilish',
        'intensity': '90–96% YUQSmax',
        'days': [
            ('Dushanba', 'Taktik qattiq o‘yin (6vs6)', '5×6 daqiqa', 91, '2 daqiqa'),
            ('Seshanba', 'Zich himoya va tezkor qarshi hujumlar', '6×45 sek', 94, '75 sek'),
            ('Chorshanba', 'Yengil tiklanish va taktik tahlil', '25 daqiqa', 48, '—'),
            ('Payshanba', 'Sprint + to‘p uzatish + darvozaga zarba', '5×5 takror', 95, '60 sek'),
            ('Juma', 'Intensiv hujum-himoya o‘tishlari', '5×5 daqiqa', 93, '2 daqiqa'),
            ('Shanba', 'Musobaqa darajasidagi sinov o‘yini', '60 daqiqa', 91, '—')
        ]
    },
    11: {
        'stage': 'III', 'title': '11-hafta — Real musobaqa yuklamasini simulyatsiya qilish',
        'goal': 'Turnir rejimiga to‘liq moslashish va tiklanish tezligini cho‘qqiga chiqarish',
        'intensity': '92–98% YUQSmax',
        'days': [
            ('Dushanba', 'Maksimal qisqa sprintlar seriyasi', '5×6 takror', 96, '45 sek'),
            ('Seshanba', 'Yuqori tempdagi to‘liq o‘yin modeli', '5×6 daqiqa', 94, '2 daqiqa'),
            ('Chorshanba', 'Faol tiklanish va neuromuskulyar bo‘shashish', '25 daqiqa', 50, '—'),
            ('Payshanba', 'Qarshi hujumlar va qisqa interval', '6×3 daqiqa', 95, '90 sek'),
            ('Juma', 'O‘yin simulatsiyasi (taymlar kesimida)', '3×15 daqiqa', 93, '5 daqiqa'),
            ('Shanba', 'To‘liq formatdagi musobaqa oldi o‘yini', '60 daqiqa', 92, '—')
        ]
    },
    12: {
        'stage': 'III', 'title': '12-hafta — Optimal sport formasini ushlash (Tapering)',
        'goal': 'Yuklamani kamaytirish, to‘liq tiklanish va musobaqaga 100% tayyor holda kelish',
        'intensity': '75–90% YUQSmax',
        'days': [
            ('Dushanba', 'Qisqartirilgan tezkor HIIT', '3×4 daqiqa', 88, '3 daqiqa'),
            ('Seshanba', 'Tezkor hujum kombinatsiyalari va otishlar', '5×4 takror', 85, '60 sek'),
            ('Chorshanba', 'Mutlaq yengil faollik va cho‘zilish', '20 daqiqa', 45, '—'),
            ('Payshanba', 'Taktik qisqa o‘yin holatlari', '4×4 daqiqa', 85, '2 daqiqa'),
            ('Juma', 'O‘yin oldidan yengil qizg‘in mashg‘ulot', '2×15 daqiqa', 80, '5 daqiqa'),
            ('Shanba', '⭐️ MUSOBAQAGA TAYYORLIK (Optimal forma)', '30 daqiqa', 70, '—')
        ]
    }
}

WEEKS = []
for num, data in WEEKS_DATA.items():
    WEEKS.append(_week(num, data['stage'], data['title'], data['goal'], data['intensity'], data['days']))


# ------------------------------------------------------------------
# AUTH ROUTES
# ------------------------------------------------------------------

@app.route("/")
def index():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    return redirect(url_for("coach_dashboard") if u.role == "coach" else url_for("athlete_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        u = User.query.filter_by(username=username).first()
        if u and u.check_password(password):
            session["user_id"] = u.id
            session["role"] = u.role
            return redirect(url_for("index"))
        flash("Login yoki parol noto'g'ri.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------
# COACH ROUTES
# ------------------------------------------------------------------

@app.route("/coach")
@login_required(role="coach")
def coach_dashboard():
    players = Player.query.all()
    n = len(players)
    vo2_vals = [p.post_vo2 or p.pre_vo2 for p in players if (p.post_vo2 or p.pre_vo2)]
    rsa_vals = [p.post_rsa or p.pre_rsa for p in players if (p.post_rsa or p.pre_rsa)]
    avg_vo2 = round(sum(vo2_vals) / len(vo2_vals), 1) if vo2_vals else None
    avg_rsa = round(sum(rsa_vals) / len(rsa_vals), 2) if rsa_vals else None
    recent = Result.query.order_by(Result.created_at.desc()).limit(8).all()
    return render_template("coach_dashboard.html", players=players, n=n,
                           avg_vo2=avg_vo2, avg_rsa=avg_rsa, recent=recent,
                           phase=get_phase(), active="dashboard")


@app.route("/coach/program")
@login_required(role="coach")
def coach_program():
    return render_template("coach_program.html", weeks=WEEKS, phase=get_phase(), active="program")


@app.route("/coach/phase/<phase>")
@login_required(role="coach")
def coach_set_phase(phase):
    if phase in ("pretest", "posttest"):
        set_phase(phase)
    return redirect(request.referrer or url_for("coach_dashboard"))


@app.route("/coach/players", methods=["GET", "POST"])
@login_required(role="coach")
def coach_players():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Ism kiriting!", "error")
            return redirect(url_for("coach_players"))
        age = int(request.form.get("age") or 20)
        position = request.form.get("position", "Markaziy")
        group = request.form.get("group", "tajriba")
        login_in = request.form.get("login", "").strip().lower()
        pass_in = request.form.get("password", "").strip()

        p = Player(name=name, age=age, position=position, group=group)
        db.session.add(p)
        db.session.flush()

        username = login_in or unique_login(name)
        raw_pass = pass_in or random_password()
        u = User(username=username, role="athlete", player_id=p.id)
        u.set_password(raw_pass)
        db.session.add(u)
        db.session.commit()

        flash(f"{name} qo'shildi! Login: {username} · Parol: {raw_pass}", "success")
        return redirect(url_for("coach_players"))

    players = Player.query.all()
    return render_template("coach_players.html", players=players, phase=get_phase(), active="players")


@app.route("/coach/players/<int:pid>/delete")
@login_required(role="coach")
def coach_delete_player(pid):
    p = Player.query.get_or_404(pid)
    User.query.filter_by(player_id=pid).delete()
    db.session.delete(p)
    db.session.commit()
    flash("O'yinchi o'chirildi.", "success")
    return redirect(url_for("coach_players"))


@app.route("/coach/players/<int:pid>/reset_password")
@login_required(role="coach")
def coach_reset_password(pid):
    u = User.query.filter_by(player_id=pid).first_or_404()
    new_pass = random_password()
    u.set_password(new_pass)
    db.session.commit()
    flash(f"Yangi parol: {new_pass}", "success")
    return redirect(url_for("coach_players"))


@app.route("/coach/tests", methods=["GET", "POST"])
@login_required(role="coach")
def coach_tests():
    players = Player.query.all()
    phase = get_phase()

    if request.method == "POST":
        test = request.form.get("test")
        pid = int(request.form.get("player_id") or 0)
        player = db.session.get(Player, pid) if pid else None
        note = ""
        result_text = ""

        if test == "yoyo":
            dist = float(request.form.get("dist") or 0)
            vo2 = calc_yoyo(dist)
            result_text = f"{dist:g} m"
            note = f"VO2max: {vo2} ml/kg"
            if player:
                if phase == "pretest":
                    player.pre_vo2 = vo2
                else:
                    player.post_vo2 = vo2

        elif test == "bleep":
            level = int(request.form.get("level") or 0)
            age = int(request.form.get("age") or (player.age if player else 20))
            vo2 = calc_bleep(level, age)
            result_text = f"Daraja {level}"
            note = f"VO2max: {vo2} ml/kg"
            if player:
                if phase == "pretest":
                    player.pre_vo2 = vo2
                else:
                    player.post_vo2 = vo2

        elif test == "ift":
            vift = float(request.form.get("vift") or 0)
            age = float(request.form.get("age") or (player.age if player else 20))
            weight = float(request.form.get("weight") or 80)
            gender = float(request.form.get("gender") or 0)
            vo2 = calc_ift(vift, age, weight, gender)
            result_text = f"VIFT {vift:g} km/soat"
            note = f"VO2max: {vo2} ml/kg"
            if player:
                if phase == "pretest":
                    player.pre_vo2 = vo2
                else:
                    player.post_vo2 = vo2

        elif test == "hgbpt":
            times = [float(request.form.get(f"t{i}") or 0) for i in range(1, 7)]
            hits = int(request.form.get("hits") or 0)
            total = int(request.form.get("total") or 6)
            avg, best, fi, acc, fitness = calc_hgbpt(times, hits, total)
            result_text = f"Ort: {avg} sek"
            note = f"Aniqlik: {acc}% | FI: {fi}%"
            if player:
                if phase == "pretest":
                    player.pre_rsa = avg
                    player.pre_fitness = fitness
                else:
                    player.post_rsa = avg
                    player.post_fitness = fitness

        elif test == "rpe":
            rpe = int(request.form.get("rpe") or 0)
            result_text = f"{rpe}/20"
            if player:
                current_fit = player.post_fitness if phase == "posttest" else player.pre_fitness
                new_fit = apply_rpe(current_fit, rpe)
                if phase == "pretest":
                    player.pre_fitness = new_fit
                else:
                    player.post_fitness = new_fit
                note = f"Jismoniy shakl: {new_fit}%"

        if player:
            r = Result(player_id=player.id, test_name=test.upper(), phase=phase,
                       result_text=result_text, note=note)
            db.session.add(r)
            db.session.commit()
            flash(f"{player.name} — natija saqlandi ({phase}).", "success")
        else:
            flash("O'yinchi tanlanmadi — natija saqlanmadi.", "error")
        return redirect(url_for("coach_tests"))

    return render_template("coach_tests.html", players=players, phase=phase, active="tests")


@app.route("/coach/results")
@login_required(role="coach")
def coach_results():
    results = Result.query.order_by(Result.created_at.desc()).all()
    return render_template("coach_results.html", results=results, active="results")


@app.route("/coach/results/<int:rid>/delete")
@login_required(role="coach")
def coach_delete_result(rid):
    r = Result.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for("coach_results"))


@app.route("/coach/stats")
@login_required(role="coach")
def coach_stats():
    players = Player.query.all()
    return render_template("coach_stats.html", players=players, phase=get_phase(), active="stats")


@app.route("/coach/science")
@login_required(role="coach")
def coach_science():
    return render_template("coach_science.html", phase=get_phase(), active="science")


# ------------------------------------------------------------------
# ATHLETE ROUTES
# ------------------------------------------------------------------

@app.route("/athlete")
@login_required(role="athlete")
def athlete_dashboard():
    u = current_user()
    player = db.session.get(Player, u.player_id) if u.player_id else None
    return render_template("athlete_dashboard.html", player=player)


# ------------------------------------------------------------------
# CLI / BOOTSTRAP
# ------------------------------------------------------------------

@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not User.query.filter_by(role="coach").first():
        coach = User(username="coach", role="coach")
        coach.set_password("coach123")
        db.session.add(coach)
    if not db.session.get(Settings, "phase"):
        db.session.add(Settings(key="phase", value="pretest"))
    db.session.commit()
    print("Baza tayyor. Murabbiy login: coach / parol: coach123")


with app.app_context():
    db.create_all()
    if not User.query.filter_by(role="coach").first():
        coach = User(username="coach", role="coach")
        coach.set_password("coach123")
        db.session.add(coach)
    if not db.session.get(Settings, "phase"):
        db.session.add(Settings(key="phase", value="pretest"))
    db.session.commit()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

# GandbolPro — to'liq backend versiyasi

Bu versiya avvalgi (faqat HTML/JavaScript, bitta havolaga bog'liq) versiyadan farqli o'laroq
**haqiqiy Flask backend + SQLite baza** bilan ishlaydi. Endi:

- Murabbiy va sportchi uchun **alohida login/parol** bilan haqiqiy kirish tizimi (HEMIS kabi).
- Murabbiy o'yinchi qo'shganda tizim **avtomatik login/parol** yaratadi (yoki o'zingiz belgilaysiz).
- Sportchi o'z login/parolini kiritib, **faqat o'zining** natijalarini ko'radi.
- Parollar **hash qilingan** holda saqlanadi (xavfsiz).
- **12 haftalik** mashg'ulot dasturi hafta-hafta bo'yicha ko'rsatiladi.
- Kompyuterdan ham, telefondan ham ochiladi (responsive dizayn).
- Ma'lumotlar bitta umumiy SQLite bazada saqlanadi — barcha foydalanuvchilar bir xil ma'lumotni ko'radi.

## Muhim: GitHub Pages BU YERDA ISHLAMAYDI

Oldingi loyihangiz GitHub Pages'da turgan edi — bu faqat statik HTML fayllarni ko'rsatadi,
Python/Flask kodini ishga tushira olmaydi. Shuning uchun bu versiyani **haqiqiy serverga**
joylashtirish kerak. Quyida eng oson (bepul) yo'llar:

### 1-variant: Render.com (tavsiya etiladi, bepul)
1. https://render.com da ro'yxatdan o'ting (GitHub akkountingiz bilan kirsangiz bo'ladi).
2. Bu papkani (yoki uni GitHub repo qilib yuklaganingizni) Render'da "New Web Service" orqali ulang.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Deploy tugmasini bosing — bir necha daqiqada `https://sizning-nomingiz.onrender.com` manzili tayyor bo'ladi.
6. Shu havolani istalgan kishi (kompyuter yoki telefondan) ochib, kirish mumkin.

### 2-variant: PythonAnywhere (bepul, oddiy)
1. https://www.pythonanywhere.com da ro'yxatdan o'ting.
2. Fayllarni yuklang (Files bo'limidan yoki git clone orqali).
3. "Web" bo'limidan yangi Flask ilova yarating, WSGI faylida `app.py`ni ko'rsating.
4. Reload tugmasini bosing.

### 3-variant: O'zingizning kompyuteringizda sinab ko'rish
```bash
pip install -r requirements.txt
python app.py
```
Keyin brauzerda `http://localhost:5000` ni oching.

## Birinchi kirish

- **Murabbiy:** login `coach`, parol `coach123` — birinchi kirgandan so'ng buni xohlasangiz
  bazadan o'zgartirish mumkin (hozircha kod orqali; xohlasangiz shu funksiyani ham qo'shib beraman).
- **Sportchi:** murabbiy "O'yinchilar" bo'limidan yangi o'yinchi qo'shganda, tizim avtomatik
  login (masalan `aliyev`) va 4 xonali parol yaratadi — shuni sportchiga ayting. Sportchi shu
  login/parol bilan bosh sahifadan kirsa, **faqat o'zining** profiliga tushadi.

## Papka tuzilishi
```
gandbolpro/
├── app.py                  # Flask backend — barcha yo'nalishlar, hisob-kitob formulalari
├── requirements.txt        # Python kutubxonalari
├── static/style.css        # Dizayn (dark theme, mobil-moslashuvchan)
└── templates/
    ├── login.html
    ├── _coach_base.html    # Murabbiy sahifalari uchun umumiy shablon (sidebar)
    ├── coach_dashboard.html
    ├── coach_program.html  # 12 haftalik dastur (hafta tablari bilan)
    ├── coach_players.html
    ├── coach_tests.html
    ├── coach_results.html
    └── athlete_dashboard.html   # Sportchining mobil-uslub shaxsiy kabineti
```

## Keyingi qadamlar (agar xohlasangiz)
- Murabbiy o'z parolini o'zgartirishi uchun sahifa
- Statistika/grafik sahifasi (t-test, Cohen's d) — avvalgi HTML versiyada bor edi, backend'ga
  ko'chirish mumkin
- Excel eksport (natijalarni .xlsx qilib yuklab olish)

Shularning birortasi kerak bo'lsa, ayting — qo'shib beraman.

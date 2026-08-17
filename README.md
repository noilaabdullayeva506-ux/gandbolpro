
# GandbolPro — To'liq Backend Versiyasi (Flask + SQLite)

Ushbu loyiha avvalgi statik (faqat HTML/JavaScript) versiyadan farqli o'laroq, **haqiqiy Flask backend va SQLite ma'lumotlar bazasi** asosida ishlaydi. 

## 🚀 Yangi Imkoniyatlar va Afzalliklar

- **Xavfsiz Autentifikatsiya:** Murabbiy va sportchilar uchun HEMIS tizimiga o'xshash alohida login va parollar orqali kirish imkoniyati.
- **Avtomatlashtirilgan Hisoblar:** Murabbiy yangi o'yinchi qo'shganda, tizim ularga avtomatik tarzda login va 4 xonali parol yaratadi.
- **Shaxsiy Kabinet:** Sportchilar o'zlarining login va parollari bilan kirib, **faqat o'zlarining** shaxsiy natijalari va ko'rsatkichlarini ko'radilar.
- **Xavfsizlik:** Barcha parollar bazada maxsus xesh (hashed) ko'rinishida himoyalangan holda saqlanadi.
- **12 Haftalik Dastur:** Ilmiy asoslangan 3 bosqichli periodizatsiyaga asoslangan 12 haftalik mashg'ulot dasturi hafta-hafta bo'yicha batafsil taqdim etiladi.
- **Responsive Dizayn:** Ilova kompyuterlar, planshetlar va mobil telefonlarda birdek mukammal ishlaydi.
- **Umumiy Ma'lumotlar Bazasi:** Barcha ma'lumotlar bitta markaziy SQLite bazasida saqlangani uchun barcha foydalanuvchilar bir xil dolzarb ma'lumotlarni ko'rishadi.

---

## ⚠️ Muhim Eslatma: GitHub Pages bu yerda ishlamaydi

Avvalgi versiyangiz GitHub Pages'da joylashgan edi. GitHub Pages faqat statik HTML/JS fayllarni ochadi va Python/Flask kodlarini o'qiy olmaydi. Shu sababli, ushbu versiyani ishga tushirish uchun uni **haqiqiy serverga** joylashtirish lozim. 

Quyida ilovani bepul va oson joylashtirish yo'llari ko'rsatilgan:

### 1-variant: Render.com (Tavsiya etiladi — Bepul)
1. [Render.com](https://render.com) saytida o'z GitHub akkountingiz orqali ro'yxatdan o'ting.
2. Ushbu loyiha papkasini GitHub repository sifatida yuklang va Render'da **"New Web Service"** tugmasini bosing.
3. Kerakli sozlamalarni kiriting:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. **Deploy** tugmasini bosing. Bir necha daqiqada `https://sizning-nomingiz.onrender.com` havolasi tayyor bo'ladi va undan istalgan qurilmada foydalanishingiz mumkin.

### 2-variant: PythonAnywhere (Bepul va sodda)
1. [PythonAnywhere](https://www.pythonanywhere.com) saytida ro'yxatdan o'ting.
2. Fayllarni **Files** bo'limi orqali yuklang.
3. **Web** bo'limidan yangi Flask ilovasini tanlab, WSGI faylida `app.py` ni ko'rsating.
4. **Reload** tugmasini bosing.

### 3-variant: Mahalliy kompyuterda sinab ko'rish (Localhost)
Terminal yoki buyruq satrida quyidagi buyruqlarni bajaring:
```bash
pip install -r requirements.txt
python app.py

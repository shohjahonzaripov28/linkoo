# Linko - 1-bosqich (Login/Register)

## Ishga tushirish (Windows, cmd orqali)

1. Bu papkani kompyuteringizga ko'chiring (masalan Ish stoliga)
2. Kerakli kutubxonani o'rnating:
   ```
   pip install -r requirements.txt
   ```
3. Ilovani ishga tushiring:
   ```
   python app.py
   ```
4. Brauzerda oching: **http://127.0.0.1:5000**

## Nima ishlaydi?

- Ro'yxatdan o'tish (username + parol)
- Tizimga kirish
- Har bir foydalanuvchining SQLite bazasida saqlanishi (`linko.db` fayli avtomatik yaratiladi)
- Kirgandan keyin "Bosh sahifa" — bu yerda 4 ta bo'lim ko'rinadi: Chat (faol), Feed, Do'kon, To'lov (bular keyingi bosqichlarda qo'shiladi)
- Liquid Glass uslubidagi (shaffof, blur effektli) dizayn

## Keyingi qadam

Bu asos tayyor bo'lgach, ustiga **Chat** funksiyasini ulaymiz — sening avvalgi terminal chat prototipingni shu login tizimiga bog'laymiz, shunda har kim o'z nomi bilan kirib gaplasha oladi.

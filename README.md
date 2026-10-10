# 🎩 Mafia Telegram Boti (@mafioznikiuzbot) & Web Admin Paneli

Professional, TrueMafia (@TrueMafiaBot) va Black Mafia uslubidagi to'liq avtomatlashtirilgan ko'p o'yinchili Telegram Mafia boti.

---

## 🌟 Asosiy Imkoniyatlar va O'yin Mexanikasi

### 1. 🎮 Real Vaqtda Guruh O'yini (Group Gameplay)
- **Lobi va Ro'yxatdan o'tish:** `/game` buyrug'i orqali yangi o'yin ochiladi, xabar avtomatik **Pin** qilinadi va jonli yangilanib boradi.
- **🤖 AI Botlar integratsiyasi:** Ishtirokchilar kam bo'lsa, `🤖 Bot qo'shish` tugmasi yoki `/addbot` orqali sun'iy intellekt o'yinchilari qo'shiladi.
- **🤫 "Мертвые молчат" qoidasi:** Halok bo'lgan o'yinchilar faol o'yin davomida guruhda gapira olmaydi — bot ularning xabarlarini darhol avtomatik o'chiradi.
- **⚡ Smart Night & Smart Vote (Tezkor vaqt):** Barcha maxsus rollar yoki tirik o'yinchilar o'z tanlovini amalga oshirishi bilanoq, taymer kutmasdan darhol keyingi bosqichga o'tiladi.
- **📊 Jonli Ovoz Berish:** Sud jarayonida tugmalarda ovozlar soni real vaqtda yangilanadi (masalan: `⚖️ Alex (2)`).
- **⚖️ 10 soniyalik Oqlanish Nutqi:** Ko'pchilik ovoz olgan gumondor dorga osilishidan oldin unga 10 soniya himoya so'zi beriladi.
- **📜 So'nggi Vasiyatnoma (Last Will):** `/will` yoki `/vasiyat` orqali yozilgan xat o'yinchi halok bo'lganda butun guruhga e'lon qilinadi.

---

### 2. 🎭 Rollar Tizimi

| Rol | Emoji | Jamoa | Vazifasi va Xususiyati |
| :--- | :---: | :---: | :--- |
| **Don** | 🎩 | Mafiya | Mafiya yetakchisi, har kecha qurbonni tanlaydi va Komissarni qidiradi. |
| **Mafiya** | 👱‍♂️ | Mafiya | Donning yordamchisi, suiqasdda qatnashadi. |
| **Komissar** | 🕵️‍♂️ | Shahar | Har kecha gumonlanuvchini tekshiradi (Mafiya/Maniak/Tinch). |
| **Serjant** | 👮‍♂️ | Shahar | Komissarning yordamchisi. Komissar tekshiruvlarini ko'radi va u o'lsa o'rnini egallaydi. |
| **Laborant (Shifokor)**| 🔬 | Shahar | Har kecha bitta odamni o'limdan yoki zahardan qutqaradi (o'zini max 1 marta). |
| **Qotil (Maniak)** | 🔪 | Maniak | Yakka o'zi harakatlanuvchi qonxo'r qotil. Maqsadi — hammadan omon qolish. |
| **Rais (Mэр)** | 🏛️ | Shahar | Kunduzgi sudda uning ovozi 2 barobar (2x) hisoblanadi. |
| **Kazanova** | 💃 | Shahar | Kechasi bir o'yinchini o'ziga rom etib, uning tungi harakatini bloklaydi. |
| **Konchi (Kamikadze)** | 💣 | Shahar | Tunda o'ldirilsa yoki sudda osilsa, hujumchini ham o'zi bilan portlatadi. |
| **Ximik** | 🧪 | Neytral | Kechasi o'yinchiga zahar beradi, zahar ertasi kuni kunduz oxirida o'ldiradi. |
| **Advokat** | 🦹 | Mafiya | Mafiyani Komissar tekshiruvidan himoya qiladi (toza qilib ko'rsatadi). |
| **Kupidon** | 💘 | Shahar | 1-tunda ikki o'yinchini sevishganlarga aylantiradi (biri o'lsa, ikkinchisi ham o'ladi). |
| **Ayg'oqchi (Shpion)**| 🕶️ | Shahar | Bir o'yinchini kuzatib, uning uyiga kechasi kimlar kelganini aniqlaydi. |
| **Qaroqchi (O'g'ri)** | 🥷 | Neytral | Kechasi o'yinchini tunab, qobiliyatini o'g'irlaydi. |
| **Terrorist** | 🧨 | Neytral | Sudda osilish oldidan o'ziga ovoz berganlardan birini portlatadi. |
| **Tinch Fuqaro** | 👱‍♂️ | Shahar | Oddiy shahar aholisi, kunduzgi ovoz berishda mafiyani fosh qiladi. |

---

### 3. 🎒 TrueMafia Inventar va Himoya Buyumlari

O'yinda TrueMafia nusxasidagi barcha 9 ta himoya vositasi to'liq ishlaydi:
- 🛡️ **Qalqon (Защита):** Tungi suiqasddan 1 marta asraydi.
- ⚖️ **Osilishdan himoya (Защита от повешения):** Sudda dorning arqoni uzilib ketadi, o'yinchi tirik qoladi.
- ⛑️ **Qotilga qarshi himoya (Защита от убийцы):** Maniak tungi hujum qilganda asrab qoladi.
- 💊 **Zardob (Защита от зелья):** Ximik zaharlaganida zaharni zararsizlantiradi.
- 🎭 **Niqob (Маска):** Komissar tekshirganida Mafiyani tinch fuqaro qilib ko'rsatadi.
- 🎲 **Omadli tanga:** Har qanday suiqasddan 35% ehtimol bilan qutqaradi.
- 📁 **Hujjatlar**, 🔫 **Vintovka**, 🪤 **Qopqon**, 🔰 **Qahramon himoyasi**.

---

### 4. 🏁 O'yin Natijalar Kartasi (End Game Card)
O'yin tugaganda guruhga va shaxsiy xabarga quyidagi standart TrueMafia kartasi chiqadi:
```
🏁 Игра окончена.
Вам начислено 💵 500 и 🎯 150!

👤 a🎸 (@tomkaulitzw)

💵 Доллары: 1200
💎 Алмазы: 5
💰 Золото: 0

🛡 Защита: 1
📁 Документы: 0
⚖️ Защита от повешения: 1
⛑️ Защита от убийцы: 0
🔫 Винтовка: 0
💊 Защита от зелья: 0
🎭 Маска: 0
🪤 Защита от скольжения: 0
🔰 Защита от героя: 0

🎯 Победы: 12
🎲 Всего игр: 35

🃏 Активные роли: Нет

Если вы подпишетесь на канал , вы получите награду x2!
[Перейти в группу]
```

---

### 5. 💰 Iqtisodiyot va Qo'shimcha Funksiyalar
- 🏦 **Bank va O'tkazmalar:** `/bank dep <summa>`, `/bank with <summa>`, `/pay <summa>`.
- 💍 **Oila va Nikoh:** `/marry`, `/divorce` (Nikoh uzugi bilan).
- ⭐ **Obro' (Reputatsiya):** `/rep +` yoki `/rep -`.
- 🚘 **Avtopark (Garaj):** `/garage` (Mercedes W140 Kaban, BMW M5).
- 🎰 **Kazino va O'yinlar:** `/spin`, `/dice`, `/darts`, `/slot`, `/casino`.
- 🥷 **O'g'rilik (Rob):** `/rob` (Signalizatsiya bilan himoyalanish).

---

### 6. 📋 Buyruqlar Ro'yxati

#### O'yin buyruqlari:
- `/game` yoki `/mafia` — Yangi o'yin ochish
- `/addbot` — AI bot qo'shish
- `/stop` — O'yinni to'xtatish (Admin)
- `/vote` yoki `/sud` — Muhokamani to'xtatib darhol ovoz berishga o'tish
- `/role` yoki `/myrole` — O'z rolingizni shaxsiy xabarda eslatish
- `/alive` yoki `/players` — Tiriklar va halok bo'lganlar holati
- `/rules` — O'yin qoidalari
- `/will` yoki `/vasiyat` — So'nggi vasiyatnoma qoldirish

#### Profil va Moliya:
- `/start` — Asosiy menyu
- `/profile` — Profil, balans, daraja, oila va mashina
- `/bonus` — Kunlik bonus
- `/quests` — Missiyalar
- `/achievements` — Yutuqlar
- `/top` — TOP o'yinchilar

---

### 7. 🚀 O'rnatish va Ishga Tushirish

1. **Repozitoriyani klonlash:**
   ```bash
   git clone https://github.com/username/mafia_bot.git
   cd mafia_bot
   ```

2. **Virtual muhit va kutubxonalarni o'rnatish:**
   ```bash
   uv sync
   # yoki
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **.env faylini sozlash:**
   `.env.example` faylidan nusxa olib `.env` yarating:
   ```env
   BOT_TOKEN=your_bot_token
   ADMIN_IDS=8055412146
   SOFPAY_SHOP_KEY=your_key
   SPONSOR_CHANNEL=@your_channel
   ```

4. **Ishga tushirish:**
   ```bash
   python main.py
   ```
   Web Admin Panel: `http://localhost:8080`

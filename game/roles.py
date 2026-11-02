from enum import Enum
from typing import Dict, Any, List
import random

class Team(str, Enum):
    CITIZEN = "citizen"      # Tinch kuchlar / Shahar
    MAFIA = "mafia"          # Mafiya to'dasi
    MANIAC = "maniac"        # Qotil / Yovuzlar (Yakka o'zi)
    VAMPIRE = "vampire"      # Vampir / Okkultizm
    NEUTRAL = "neutral"      # Neytral / Mustaqil

class RoleInfo:
    def __init__(
        self,
        code: str,
        name: str,
        emoji: str,
        team: Team,
        description: str,
        night_prompt: str = "",
        action_type: str = "none",
        ru_name: str = "",
        ru_description: str = ""
    ):
        self.code = code
        self.name = name
        self.emoji = emoji
        self.team = team
        self.description = description
        self.night_prompt = night_prompt
        self.action_type = action_type
        self.ru_name = ru_name
        self.ru_description = ru_description

ROLES: Dict[str, RoleInfo] = {
    # ==========================================
    # 1. BOSH ROLLLAR (ASOSIY O'ZAK)
    # ==========================================
    "don": RoleInfo(
        code="don",
        name="Don (Mafiya Bossi)",
        ru_name="Дон",
        emoji="🎩",
        team=Team.MAFIA,
        description="Mafiyaning boshlig'i. Har kecha qurbonni belgilaydi va o'yinchilarni Komissar deb tekshirishi mumkin.",
        ru_description="Вы Дон, лидер мафии. Каждую ночь вы выбираете жертву и можете проверять жителей, чтобы найти Комиссара.",
        night_prompt="O'ldirish uchun nishonni tanlang yoki Komissarni qidiring:",
        action_type="mafia_kill"
    ),
    "mafia": RoleInfo(
        code="mafia",
        name="Mafiya",
        ru_name="Мафия",
        emoji="👱‍♂️",
        team=Team.MAFIA,
        description="Donning sodiq yordamchisi. Don bilan birgalikda shahar fuqarolarini yo'q qiladi.",
        ru_description="Вы Мафия, подчиняетесь Дону и убиваете тех, кто вам противостоит. Если Дон умрет, вы можете стать новым Доном.",
        night_prompt="Don buyrug'ini bajaring yoki suiqasd nishonini tanlang:",
        action_type="mafia_kill"
    ),
    "komissar": RoleInfo(
        code="komissar",
        name="Komissar (Sherif)",
        ru_name="Комиссар",
        emoji="🕵️‍♂️",
        team=Team.CITIZEN,
        description="Qonun posboni. Har kecha bir o'yinchining shaxsini tekshiradi yoki shubhali kimsani otadi.",
        ru_description="Вы Комиссар, блюститель порядка. Каждую ночь вы проверяете игроков или стреляете в подозреваемого.",
        night_prompt="Tekshirish yoki otish uchun o'yinchini tanlang:",
        action_type="check_or_shoot"
    ),
    "serjant": RoleInfo(
        code="serjant",
        name="Serjant",
        ru_name="Сержант",
        emoji="👮‍♂️",
        team=Team.CITIZEN,
        description="Komissarning o'ng qo'li. Komissar halok bo'lganda, uning o'rnini egallab yangi Komissar bo'ladi.",
        ru_description="Вы Сержант, помощник Комиссара. Если Комиссар погибнет, вы займете его пост и продолжите расследование.",
        night_prompt="Kechasi shahar ko'chalarini kuzating:",
        action_type="patrol"
    ),
    "kotil": RoleInfo(
        code="kotil",
        name="Qotil (Maniak)",
        ru_name="Маньяк",
        emoji="🔪",
        team=Team.MANIAC,
        description="Qonxo'r yakka qotil. Har kecha bitta odamni shafqatsizlarcha o'ldiradi. Maqsadi — hammadan omon qolish.",
        ru_description="Вы Маньяк, жестокий убийца-одиночка. Каждую ночь вы убиваете одного жителя города. Ваша цель — остаться последним выжившим.",
        night_prompt="Tungi qurboningizni tanlang:",
        action_type="kill"
    ),
    "rais": RoleInfo(
        code="rais",
        name="Rais (Hokim)",
        ru_name="Мэр",
        emoji="🏛️",
        team=Team.CITIZEN,
        description="Shahar rahbari. Kunduzgi ovoz berishda uning ovozi 2 barobar (2x) hisoblanadi!",
        ru_description="Вы Мэр города. Вы мирный житель, но ваш голос на дневном суде имеет двойную силу (2x)!",
        night_prompt="",
        action_type="none"
    ),
    "ximik": RoleInfo(
        code="ximik",
        name="Ximik (Kimyogar)",
        ru_name="Химик",
        emoji="🧪",
        team=Team.NEUTRAL,
        description="Zahar ustasi. Kechasi o'yinchini zaharlaydi (zahar ertasi kuni kunduz oxirida o'ldiradi).",
        ru_description="Вы безумный Химик. Каждую ночь вы отравляете одного жителя ядом замедленного действия.",
        night_prompt="Zaharlash uchun o'yinchini tanlang:",
        action_type="poison"
    ),
    "laborant": RoleInfo(
        code="laborant",
        name="Laborant (Shifokor)",
        ru_name="Доктор",
        emoji="🔬",
        team=Team.CITIZEN,
        description="Ilmiy xodim va shifokor. Zardob yordamida o'yinchini tungi hujum yoki zahardan davolaydi.",
        ru_description="Вы Доктор. Каждую ночь вы можете спасти одного жителя от ночного нападения или вылечить от яда.",
        night_prompt="Davolash / qutqarish uchun o'yinchini tanlang:",
        action_type="heal"
    ),
    "vampir": RoleInfo(
        code="vampir",
        name="Vampir",
        ru_name="Вампир",
        emoji="🧛‍♂️",
        team=Team.VAMPIRE,
        description="Zulmat maxluqi. Kechasi o'yinchilarning qonini ichadi va ularning kuchi susayadi.",
        ru_description="Вы Вампир. Вы охотитесь по ночам и выпиваете кровь мирных жителей.",
        night_prompt="Qonini ichish uchun qurbonni tanlang:",
        action_type="bite"
    ),
    "kazanova": RoleInfo(
        code="kazanova",
        name="Kazanova (Kez)",
        ru_name="Красотка",
        emoji="💃",
        team=Team.CITIZEN,
        description="Sehrli maftunkor. Kechasi bir o'yinchini o'ziga rom etadi va uning tungi harakatini butunlay bloklaydi.",
        ru_description="Вы Красотка (Казанова). Каждую ночь вы очаровываете игрока, полностью блокируя его действия на эту ночь.",
        night_prompt="Tungi harakatini to'xtatish uchun o'yinchini tanlang:",
        action_type="distract"
    ),
    "konchi": RoleInfo(
        code="konchi",
        name="Konchi (Kamikadze)",
        ru_name="Камикадзе",
        emoji="💣",
        team=Team.CITIZEN,
        description="Portlovchi moddalar ustasi. Agar uni tunda o'ldirishsa yoki kunduzi osishsa, unga hujum qilganni ham portlatadi!",
        ru_description="Вы Камикадзе. Если вас убьют ночью или казнят на суде, ваша взрывчатка заберет с собой вашего убийцу!",
        night_prompt="",
        action_type="none"
    ),
    "advokat": RoleInfo(
        code="advokat",
        name="Advokat (Mafiya Himoyasi)",
        ru_name="Адвокат",
        emoji="🦹",
        team=Team.MAFIA,
        description="Mafiya himoyachisi. Kechasi bitta o'yinchini himoyaga oladi (Komissar tekshiruvida toza aholi bo'lib ko'rinadi).",
        ru_description="Вы Адвокат. Каждую ночь вы защищаете одного из членов мафии от проверок Комиссара.",
        night_prompt="Himoya qilish uchun o'yinchini tanlang:",
        action_type="protect_mafia"
    ),
    "sehrgar": RoleInfo(
        code="sehrgar",
        name="Sehrgar (Nekromant)",
        ru_name="Колдун",
        emoji="🧙‍♂️",
        team=Team.CITIZEN,
        description="Tirilish mo'jizasi. O'yinda 1 marta halok bo'lgan o'yinchini tiriltirib hayotga qaytaradi!",
        ru_description="Вы Колдун. Один раз за всю игру вы можете воскресить погибшего игрока и вернуть его к жизни.",
        night_prompt="Tiriltirish uchun qurbonni tanlang:",
        action_type="revive"
    ),
    "citizen": RoleInfo(
        code="citizen",
        name="Tinch Fuqaro",
        ru_name="Мирный житель",
        emoji="👱‍♂️",
        team=Team.CITIZEN,
        description="Oddiy shahar fuqarosi.",
        ru_description="Вы обычный мирный житель. Ваша задача — вычислить мафию и казнить её на дневном голосовании.",
        night_prompt="",
        action_type="none"
    ),
    "kupidon": RoleInfo(
        code="kupidon",
        name="Kupidon",
        ru_name="Купидон",
        emoji="💘",
        team=Team.CITIZEN,
        description="Muhabbat elchisi. Birinchi kechada ikki o'yinchini sevishganlarga aylantiradi. Biri o'lsa, ikkinchisi ham qayg'udan vafot etadi!",
        ru_description="Вы Купидон. В первую ночь вы выбираете двух влюбленных. Если один из них погибает, второй умирает от горя!",
        night_prompt="Sevishganlar qilib bog'lash uchun o'yinchini tanlang:",
        action_type="cupid"
    ),
    "terrorist": RoleInfo(
        code="terrorist",
        name="Terrorist (Shahid)",
        ru_name="Террорист",
        emoji="🧨",
        team=Team.NEUTRAL,
        description="Portlovchi xudkush. Kunduzgi sudda osilish oldidan o'zi bilan birga istalgan o'yinchini ham portlatib yuboradi!",
        ru_description="Вы Террорист. На дневном суде перед казнью вы забираете с собой любого игрока!",
        night_prompt="",
        action_type="none"
    ),
    "shpion": RoleInfo(
        code="shpion",
        name="Ayg'oqchi (Shpion)",
        ru_name="Шпион",
        emoji="🕶️",
        team=Team.CITIZEN,
        description="Maxfiy razvedkachi. Har kecha bir o'yinchini kuzatib, uning qoshiga kimlar kelganini biladi.",
        ru_description="Вы Шпион. Каждую ночь вы следите за домом одного игрока и узнаете гостей.",
        night_prompt="Kuzatish uchun o'yinchini tanlang:",
        action_type="spy"
    ),
    "ogri": RoleInfo(
        code="ogri",
        name="Qaroqchi (O'g'ri)",
        ru_name="Вор",
        emoji="🥷",
        team=Team.NEUTRAL,
        description="Tungi talonchi. Har kecha bir o'yinchini tunab, uning tungi harakatini to'xtatadi va o'ziga oladi.",
        ru_description="Вы Вор. Каждую ночь вы крадете ночную способность у игрока.",
        night_prompt="Tunash uchun o'yinchini tanlang:",
        action_type="steal"
    ),

    # ==========================================
    # 2. YANGI SHAHAR (CITIZEN) ROLLARI (20 TA)
    # ==========================================
    "snayper": RoleInfo(
        code="snayper",
        name="Snayper (Merganshovvoz)",
        ru_name="Снайпер",
        emoji="🎯",
        team=Team.CITIZEN,
        description="Shaharning maxfiy mergani. Tunda o'zi gumon qilgan har qanday o'yinchini ota oladi.",
        ru_description="Городской снайпер. Каждую ночь может сделать выстрел в любого подозреваемого жителя.",
        night_prompt="Otish uchun nishonni tanlang:",
        action_type="sniper_shot"
    ),
    "detektiv": RoleInfo(
        code="detektiv",
        name="Detektiv (Izquvar)",
        ru_name="Детектив",
        emoji="🕵️",
        team=Team.CITIZEN,
        description="Professional izquvar. Tunda tanlangan shaxs kimning uyiga borganini aniqlaydi.",
        ru_description="Следопыт и сыщик. Узнает, к кому ночью ходил выбранный игрок.",
        night_prompt="Kuzatish uchun o'yinchini tanlang:",
        action_type="track"
    ),
    "tansoqchi": RoleInfo(
        code="tansoqchi",
        name="Tansoqchi (Bodyguard)",
        ru_name="Телохранитель",
        emoji="💂",
        team=Team.CITIZEN,
        description="Sodiq qo'riqchi. Tanlagan odamini o'z hayoti evaziga tungi hujumlardan himoya qiladi.",
        ru_description="Преданный защитник. Защищает выбранного игрока ценой собственной жизни.",
        night_prompt="Himoya qilish uchun o'yinchini tanlang:",
        action_type="guard"
    ),
    "psixolog": RoleInfo(
        code="psixolog",
        name="Psixolog (Miyashunos)",
        ru_name="Психолог",
        emoji="🛋️",
        team=Team.CITIZEN,
        description="Ruhiyat mutaxassisi. O'yinchining qo'li qonga belangan yoki yo'qligini aniqlaydi.",
        ru_description="Специалист по поведению. Определяет, совершал ли игрок убийства.",
        night_prompt="Ruhiy holatini tekshirish uchun o'yinchini tanlang:",
        action_type="psycho_check"
    ),
    "patolog": RoleInfo(
        code="patolog",
        name="Patologanatom (Ekspert)",
        ru_name="Патологоанатом",
        emoji="🔬",
        team=Team.CITIZEN,
        description="Tibbiy ekspert. O'lgan o'yinchining kim tomonidan o'ldirilganini fosh qiladi.",
        ru_description="Судмедэксперт. Выясняет истинную причину и виновника гибели жертвы.",
        night_prompt="Ekspertiza qilish uchun marhumni tanlang:",
        action_type="autopsy"
    ),
    "jurnalist": RoleInfo(
        code="jurnalist",
        name="Jurnalist (Muxbir)",
        ru_name="Журналист",
        emoji="📰",
        team=Team.CITIZEN,
        description="Mustaqil jurnalist. Har kecha bir o'yinchining jamoasini (Shahar yoki Yovuz) surishtiradi.",
        ru_description="Журналист расследований. Узнает команду проверяемого игрока.",
        night_prompt="Surishtiruv o'tkazish uchun o'yinchini tanlang:",
        action_type="investigate_player"
    ),
    "veteran": RoleInfo(
        code="veteran",
        name="Urush Veterani",
        ru_name="Ветеран",
        emoji="🎖️",
        team=Team.CITIZEN,
        description="Tajribali jangchi. Tunda o'z uyini mudofaaga oladi — unga kelgan dushman otib tashlanadi!",
        ru_description="Ветеран войны. На боевом дежурстве убивает любого, кто осмелится проникнуть в его дом ночью.",
        night_prompt="Tungi ogohlik rejimini faollashtirish uchun o'zingizni tanlang:",
        action_type="veteran_alert"
    ),
    "uchastkovoy": RoleInfo(
        code="uchastkovoy",
        name="Uchastka Noziri (Inspektor)",
        ru_name="Участковый",
        emoji="👮",
        team=Team.CITIZEN,
        description="Shahar posboni. Bir o'yinchini uy qamog'ida ushlab, uning harakatini to'xtatadi va hujumdan saqlaydi.",
        ru_description="Участковый милиционер. Сажает игрока под домашний арест, блокируя его действия и защищая от пуль.",
        night_prompt="Uy qamog'iga olish uchun o'yinchini tanlang:",
        action_type="jail"
    ),
    "hakim": RoleInfo(
        code="hakim",
        name="Bosh Hakim (Sudya)",
        ru_name="Судья",
        emoji="👨‍⚖️",
        team=Team.CITIZEN,
        description="Shahar bosh sudyasi. Kunduzgi sudda ovozlar teng bo'lib qolsa, uning tanlovi yakuniy hal qiluvchi bo'ladi!",
        ru_description="Верховный судья. При равенстве голосов на дневном суде его решение является решающим!",
        night_prompt="",
        action_type="none"
    ),
    "shahar_soqchisi": RoleInfo(
        code="shahar_soqchisi",
        name="Shahar Soqchisi",
        ru_name="Городской Страж",
        emoji="🛡️",
        team=Team.CITIZEN,
        description="Tungi patrul. Har kecha bir fuqaroni qo'riqlab, uni mafiya yoki qotil hujumidan asraydi.",
        ru_description="Ночной патрульный. Охраняет выбранного мирного жителя от нападения.",
        night_prompt="Qo'riqlash uchun o'yinchini tanlang:",
        action_type="protect_citizen"
    ),
    "ruhoniy": RoleInfo(
        code="ruhoniy",
        name="Ruhoniy (Padre)",
        ru_name="Священник",
        emoji="⛪",
        team=Team.CITIZEN,
        description="Muqaddas ruhoniy. O'yinchining gunohlarini eshitadi — yovuz shaxs bo'lsa, ertasi kuni ovoz berishdan mahrum bo'ladi.",
        ru_description="Священник. Исповедует игрока — если тот грешен (злодей), лишает его права голоса на день.",
        night_prompt="Tavba qildirish uchun o'yinchini tanlang:",
        action_type="confess"
    ),
    "tez_yordam": RoleInfo(
        code="tez_yordam",
        name="Tez Yordam Feldsheri",
        ru_name="Фельдшер",
        emoji="🚑",
        team=Team.CITIZEN,
        description="Shoshilinch tibbiy yordam. Tunda og'ir yaralangan odamni qayta hayotga qaytaradi.",
        ru_description="Скорая помощь. Реанимирует тяжелораненого игрока этой ночью.",
        night_prompt="Qutqarish uchun o'yinchini tanlang:",
        action_type="paramedic"
    ),
    "mantiqchi": RoleInfo(
        code="mantiqchi",
        name="Mantiqchi Analitik",
        ru_name="Аналитик",
        emoji="🧠",
        team=Team.CITIZEN,
        description="Kuchli intellekt sohibi. O'zi tanlagan o'yinchining kunduzgi ovozini 2 barobarga oshiradi.",
        ru_description="Гениальный аналитик. Удваивает силу голоса выбранного игрока на дневном суде.",
        night_prompt="Ovozini 2x qilish uchun o'yinchini tanlang:",
        action_type="empower_vote"
    ),
    "qariya": RoleInfo(
        code="qariya",
        name="Oqsoqol (Qariya)",
        ru_name="Старейшина",
        emoji="👴",
        team=Team.CITIZEN,
        description="Donishmand qariya. O'zining hayotiy tajribasi tufayli birinchi marta tungi hujumga uchraganida omon qoladi.",
        ru_description="Мудрый старец. Обладает стойкостью и переживает первое ночное нападение.",
        night_prompt="",
        action_type="none"
    ),
    "advokat_shahar": RoleInfo(
        code="advokat_shahar",
        name="Himoyachi Advokat (Shahar)",
        ru_name="Адвокат Города",
        emoji="⚖️",
        team=Team.CITIZEN,
        description="Adolat himoyachisi. Tanlagan fuqarosini ertangi kungi shahar sudida dorga osilishdan himoya qiladi.",
        ru_description="Городской адвокат. Защищает выбранного жителя от казни на дневном суде.",
        night_prompt="Sudda himoya qilish uchun o'yinchini tanlang:",
        action_type="acquit"
    ),
    "xabarchi": RoleInfo(
        code="xabarchi",
        name="Xabarchi (Pochtalon)",
        ru_name="Почтальон",
        emoji="🕊️",
        team=Team.CITIZEN,
        description="Shahar xabarchisi. O'yinchiga tunda xavfdan ogohlantiruvchi maxfiy xat yetkazadi.",
        ru_description="Почтальон. Передает секретное предупреждение об угрозе выбранному игроку.",
        night_prompt="Xat yuborish uchun o'yinchini tanlang:",
        action_type="deliver_letter"
    ),
    "ovchi": RoleInfo(
        code="ovchi",
        name="Mergan Ovchi",
        ru_name="Охотник",
        emoji="🏹",
        team=Team.CITIZEN,
        description="Mergan ovchi. Agar u kunduzi osilsa yoki tunda o'ldirilsa, so'nggi o'qi bilan dushmanni ham otib ketadi!",
        ru_description="Охотник. Погибая днем или ночью, делает последний смертельный выстрел в любого игрока!",
        night_prompt="",
        action_type="none"
    ),
    "inspektor": RoleInfo(
        code="inspektor",
        name="Soliq Inspektori",
        ru_name="Инспектор",
        emoji="🧐",
        team=Team.CITIZEN,
        description="Moliyaviy taftishchi. O'yinchining noqonuniy boyliklarini tekshirib, mafiya ekanligini fosh etadi.",
        ru_description="Налоговый инспектор. Проверяет доходы и выявляет мафиозные связи игрока.",
        night_prompt="Audit qilish uchun o'yinchini tanlang:",
        action_type="audit"
    ),
    "qo_riqchi": RoleInfo(
        code="qo_riqchi",
        name="Maxsus Qo'riqchi",
        ru_name="Охранник",
        emoji="🥋",
        team=Team.CITIZEN,
        description="Sport ustasi. Kechasi o'zini yoki boshqa fuqaroni jismoniy hujumdan himoya qiladi.",
        ru_description="Мастер единоборств. Защищает себя или жителя от физического нападения.",
        night_prompt="Himoya qilish uchun o'yinchini tanlang:",
        action_type="body_guard_lite"
    ),
    "qutqaruvchi": RoleInfo(
        code="qutqaruvchi",
        name="Qutqaruvchi (FVV)",
        ru_name="Спасатель МЧС",
        emoji="🦺",
        team=Team.CITIZEN,
        description="Qutqaruv xizmati. Zahar ta'siridagi yoki qopqonga tushgan fuqaroni zudlik bilan qutqaradi.",
        ru_description="Спасатель МЧС. Спасает жителя от яда или ловушки.",
        night_prompt="Qutqarish uchun o'yinchini tanlang:",
        action_type="rescue"
    ),

    # ==========================================
    # 3. YANGI MAFIYA (MAFIA) ROLLARI (12 TA)
    # ==========================================
    "kadr": RoleInfo(
        code="kadr",
        name="Mafiya Kadri (Konsilyere)",
        ru_name="Консильере",
        emoji="🕶️",
        team=Team.MAFIA,
        description="Donning o'ng qo'li. Don o'lsa, avtomatik ravishda to'daning yangi Donga aylanadi.",
        ru_description="Советник Дона. Если Дон погибает, занимает его место и возглавляет мафию.",
        night_prompt="Qurbonni nishonga oling:",
        action_type="mafia_kill"
    ),
    "xaker": RoleInfo(
        code="xaker",
        name="Kiber Xaker (Mafiya)",
        ru_name="Хакер Мафии",
        emoji="💻",
        team=Team.MAFIA,
        description="Kiber jinoyatchi. Komissar serverlarini buzib, soxta tekshiruv natijalarini uzatadi.",
        ru_description="Киберпреступник. Взламывает связь и подделывает отчеты Комиссара.",
        night_prompt="Tizimini buzish uchun o'yinchini tanlang:",
        action_type="hack"
    ),
    "qora_shifokor": RoleInfo(
        code="qora_shifokor",
        name="Qora Shifokor (Jarroh)",
        ru_name="Черный Доктор",
        emoji="💉",
        team=Team.MAFIA,
        description="Yashirin jarroh. Mafiya a'zolarini tungi hujum va Komissar o'qidan davolab qoladi.",
        ru_description="Подпольный хирург. Лечит раненых сообщников мафии.",
        night_prompt="Davolash uchun mafiozni tanlang:",
        action_type="mafia_heal"
    ),
    "suqasdqor": RoleInfo(
        code="suqasdqor",
        name="Yollanma Qotil (Hitman)",
        ru_name="Наемный Киллер",
        emoji="🗡️",
        team=Team.MAFIA,
        description="Elita qotili. Uning maxsus o'qi har qanday oddiy qalqon va himoyalarni teshib o'tadi!",
        ru_description="Профессиональный киллер. Его выстрел пробивает любые щиты и защиты!",
        night_prompt="Maxsus o'q bilan nishonga olish:",
        action_type="piercing_shot"
    ),
    "bandit": RoleInfo(
        code="bandit",
        name="Qurolli Bandit",
        ru_name="Бандит",
        emoji="🦹‍♂️",
        team=Team.MAFIA,
        description="Zo'ravon bandit. Kechasi o'yinchini qo'rqitadi — ertasi kuni u ovoz bera olmaydi.",
        ru_description="Головорез. Запугивает жертву ночью, лишая ее права голоса на следующий день.",
        night_prompt="Qo'rqitish uchun o'yinchini tanlang:",
        action_type="intimidate"
    ),
    "provokator": RoleInfo(
        code="provokator",
        name="Provokator (Ig'vogar)",
        ru_name="Провокатор",
        emoji="🗣️",
        team=Team.MAFIA,
        description="Tuhmat ustasi. Tinch fuqaroni nishonga oladi — Komissar tekshirsa, u mafiyadek ko'rinadi!",
        ru_description="Мастер провокаций. Подставляет мирного жителя, делая его похожим на мафию для Комиссара.",
        night_prompt="Tuhmat qilish uchun shahar vakilini tanlang:",
        action_type="frame"
    ),
    "kontrabandist": RoleInfo(
        code="kontrabandist",
        name="Kontrabandist",
        ru_name="Контрабандист",
        emoji="📦",
        team=Team.MAFIA,
        description="Qora bozor savdogari. Mafiyaga maxsus tungi anjomlar va qurollar yetkazib beradi.",
        ru_description="Контрабандист. Снабжает мафию оружием и полезной контрабандой.",
        night_prompt="Anjom yetkazish uchun mafiozni tanlang:",
        action_type="smuggle"
    ),
    "soxta_guvoh": RoleInfo(
        code="soxta_guvoh",
        name="Soxta Guvoh (Poraxo'r)",
        ru_name="Лжесвидетель",
        emoji="🎭",
        team=Team.MAFIA,
        description="Yolg'onchi guvoh. Kunduzgi sudda o'z yolg'onlari bilan tinch aholini dorga qaratadi.",
        ru_description="Лжесвидетель. Своими показаниями подставляет мирных жителей на суде.",
        night_prompt="Guvohlik to'qish uchun nishonni tanlang:",
        action_type="false_witness"
    ),
    "shantajchi": RoleInfo(
        code="shantajchi",
        name="Shantajchi (Kompromat)",
        ru_name="Шантажист",
        emoji="📁",
        team=Team.MAFIA,
        description="Kompromat ustasi. Bir o'yinchining sirini topib, uning tungi harakatini bloklaydi.",
        ru_description="Шантажист. Находит компромат на игрока и блокирует его действия.",
        night_prompt="Shantaj qilish uchun o'yinchini tanlang:",
        action_type="blackmail"
    ),
    "snayper_mafiya": RoleInfo(
        code="snayper_mafiya",
        name="Mafiya Mergani",
        ru_name="Снайпер Мафии",
        emoji="🔭",
        team=Team.MAFIA,
        description="Mafiyaning pinhona mergani. Shaharning faol rollarini uzoqdan poylab yo'q qiladi.",
        ru_description="Снайпер клана. Выслеживает и метко уничтожает ключевых жителей города.",
        night_prompt="Nishonga olish uchun o'yinchini tanlang:",
        action_type="mafia_snipe"
    ),
    "ayg_oqchi_mafiya": RoleInfo(
        code="ayg_oqchi_mafiya",
        name="Mafiya Josusi",
        ru_name="Шпион Мафии",
        emoji="🥷",
        team=Team.MAFIA,
        description="Mafiya razvedkachisi. Har kecha bir fuqaroning haqiqiy rolini bilib olib, to'daga aytadi.",
        ru_description="Разведчик мафии. Узнает точную роль выбранного игрока и докладывает Дону.",
        night_prompt="Rolini bilish uchun o'yinchini tanlang:",
        action_type="mafia_scout"
    ),
    "mina_koyuvchi": RoleInfo(
        code="mina_koyuvchi",
        name="Mina Qo'yuvchi (Sabotajchi)",
        ru_name="Подрывник Мафии",
        emoji="🧨",
        team=Team.MAFIA,
        description="Mina ustasi. O'yinchining eshigiga mina qo'yadi — uning uyiga tashrif buyurgan mehmon portlaydi!",
        ru_description="Минер мафии. Минирует дом жителя — любой ночной гость взорвется на мине!",
        night_prompt="Uyiga mina qo'yish uchun o'yinchini tanlang:",
        action_type="plant_bomb"
    ),

    # ==========================================
    # 4. YANGI MANIAKLAR VA YOVUZLAR (8 TA)
    # ==========================================
    "qonxor": RoleInfo(
        code="qonxor",
        name="Shafqatsiz Qassob (Butcher)",
        ru_name="Мясник",
        emoji="🪓",
        team=Team.MANIAC,
        description="Shafqatsiz qassob. Har kecha bir odamni tanlaydi, uning zarbasidan oddiy qalqon qutqarolmaydi.",
        ru_description="Кровожадный Мясник. Его удар топором сокрушает даже крепкую броню.",
        night_prompt="Chopib tashlash uchun qurbonni tanlang:",
        action_type="butcher_kill"
    ),
    "zaharlovchi": RoleInfo(
        code="zaharlovchi",
        name="Qora Zaharlovchi",
        ru_name="Отравитель",
        emoji="🧪",
        team=Team.MANIAC,
        description="Sekin ta'sir qiluvchi qora zahar sohibi. Zaharlangan odam keyingi tunda halok bo'ladi.",
        ru_description="Коварный отравитель. Поражает жертву ядом замедленного действия.",
        night_prompt="Zaharlash uchun qurbonni tanlang:",
        action_type="poison"
    ),
    "piroman": RoleInfo(
        code="piroman",
        name="Piroman (O't Qo'yuvchi)",
        ru_name="Пироман",
        emoji="🔥",
        team=Team.MANIAC,
        description="Olov shaydosi. Kechalari uylarga benzin sepadi va istagan paytda hammasini bittada yoqib yuboradi!",
        ru_description="Безумный Пироман. Обливает дома бензином и может сжечь все цели одновременно!",
        night_prompt="Benzin quyish / yoqish uchun nishonni tanlang:",
        action_type="arson"
    ),
    "illuzionist": RoleInfo(
        code="illuzionist",
        name="Illuzionist (Fokuschi)",
        ru_name="Иллюзионист",
        emoji="🤹",
        team=Team.MANIAC,
        description="Ko'zboyloqchi. O'yinchilarning tungi harakat nishonlarini o'zaro almashtirib yuboradi!",
        ru_description="Иллюзионист. Подменяет цели ночных действий игроков, создавая путаницу.",
        night_prompt="Nishonini almashtirish uchun o'yinchini tanlang:",
        action_type="trick"
    ),
    "arvoh": RoleInfo(
        code="arvoh",
        name="Qasoskor Arvoh",
        ru_name="Призрак",
        emoji="👻",
        team=Team.MANIAC,
        description="Qasoskor ruh. O'yinda o'lgandan keyin ham keyingi tunda qabridan bir qotilni o'zi bilan olib ketadi!",
        ru_description="Мстительный Призрак. После смерти восстает из могилы и уносит с собой своего убийцу!",
        night_prompt="Qasos olish uchun o'yinchini tanlang:",
        action_type="haunt"
    ),
    "jallod": RoleInfo(
        code="jallod",
        name="Qonli Jallod (Executioner)",
        ru_name="Палач",
        emoji="⛓️",
        team=Team.MANIAC,
        description="Zanjirlar ustasi. Bir kishini zanjirband qiladi — u ertasi kuni ovoz berolmaydi va gapira olmaydi.",
        ru_description="Кровавый Палач. Сковывает цепями жертву, лишая ее голоса и слова.",
        night_prompt="Zanjirband qilish uchun o'yinchini tanlang:",
        action_type="shackle"
    ),
    "bori": RoleInfo(
        code="bori",
        name="Bo'riodam (Werewolf)",
        ru_name="Оборотень",
        emoji="🐺",
        team=Team.MANIAC,
        description="To'lin oy yirtqichi. Kechalari vahshiyona quturib, yo'lida uchragan har qanday nishonni yanchib tashlaydi.",
        ru_description="Свирепый Оборотень. Рвет когтями жертву, игнорируя защиту телохранителей.",
        night_prompt="G'ajib tashlash uchun qurbonni tanlang:",
        action_type="werewolf_tear"
    ),
    "yirtqich": RoleInfo(
        code="yirtqich",
        name="Yirtqich (Chupakabra)",
        ru_name="Хищник",
        emoji="🦁",
        team=Team.MANIAC,
        description="Yovvoyi qonxo'r maxluq. Ko'chalarda yolg'iz qolgan har qanday o'yinchini ovlaydi.",
        ru_description="Ночной Хищник. Охотится на одиноких жителей и пожирает их во тьме.",
        night_prompt="Ov qilish uchun qurbonni tanlang:",
        action_type="beast_hunt"
    ),

    # ==========================================
    # 5. YANGI VAMPIRLAR VA OKKULTIZM (5 TA)
    # ==========================================
    "vampir_graf": RoleInfo(
        code="vampir_graf",
        name="Graf Drakula (Vampir Boshlig'i)",
        ru_name="Граф Дракула",
        emoji="🧛",
        team=Team.VAMPIRE,
        description="Oliy vampir. Tunda fuqaroni chaqib, uni o'z vampirlar to'dasiga aylantiradi!",
        ru_description="Высший вампир. Обращает укушенного мирного жителя в клан вампиров!",
        night_prompt="Chaqib to'daga qo'shish uchun o'yinchini tanlang:",
        action_type="convert_vampire"
    ),
    "gipnozchi": RoleInfo(
        code="gipnozchi",
        name="Gipnozchi (Sehrgar)",
        ru_name="Гипнотизер",
        emoji="🌀",
        team=Team.VAMPIRE,
        description="Ruhiyat hukmdori. O'yinchini gipnoz qilib, uning kunduzgi ovozini o'ziga buysundiradi.",
        ru_description="Мастер гипноза. Заставляет загипнотизированного игрока голосовать по своей воле.",
        night_prompt="Gipnoz qilish uchun o'yinchini tanlang:",
        action_type="hypnosis"
    ),
    "jodugar": RoleInfo(
        code="jodugar",
        name="Qora Jodugar (Vitch)",
        ru_name="Черная Ведьма",
        emoji="🧙‍♀️",
        team=Team.VAMPIRE,
        description="Sehrli eliksirlar ustasi. Bir marta qutqaruvchi va bir marta zaharlovchi eliksirga ega.",
        ru_description="Ведьма. Обладает зельем спасения и зельем мгновенной смерти.",
        night_prompt="Sehrli eliksir ichirish uchun o'yinchini tanlang:",
        action_type="witch_curse"
    ),
    "nekromant": RoleInfo(
        code="nekromant",
        name="Qora Nekromant",
        ru_name="Некромант",
        emoji="💀",
        team=Team.VAMPIRE,
        description="O'liklar bilan so'zlashuvchi. O'lgan kishining ruhidan uning qotili haqida ma'lumot oladi.",
        ru_description="Некромант. Вызывает дух погибшего жителя и узнает его убийц.",
        night_prompt="Ruhini chaqirish uchun marhumni tanlang:",
        action_type="summon_dead"
    ),
    "qiyofa_ugrisi": RoleInfo(
        code="qiyofa_ugrisi",
        name="Qiyofa O'g'risi (Doppelganger)",
        ru_name="Перевертыш",
        emoji="🦎",
        team=Team.VAMPIRE,
        description="Qiyofa o'g'risi. O'ldirilgan o'yinchining qiyofasini olib, uning nomidan yashaydi.",
        ru_description="Оборотень-двойник. Принимает облик и способности павшего игрока.",
        night_prompt="Qiyofasini olish uchun o'yinchini tanlang:",
        action_type="shapeshift"
    ),

    # ==========================================
    # 6. YANGI NEYTRAL VA MUSTAQIL ROLLAR (5 TA)
    # ==========================================
    "masxaraboz": RoleInfo(
        code="masxaraboz",
        name="Masxaraboz (Jester / Kloun)",
        ru_name="Шут (Клоун)",
        emoji="🤡",
        team=Team.NEUTRAL,
        description="Aqlsiz masxaraboz. Maqsadi — kunduzgi sudda o'zini ostirish! Agar osilsa, u yakka g'olib bo'ladi!",
        ru_description="Шут. Его единственная цель — чтобы его повесили на дневном суде! Если его казнят — он побеждает в одиночку!",
        night_prompt="",
        action_type="none"
    ),
    "omadli_darvesh": RoleInfo(
        code="omadli_darvesh",
        name="Omadli Darvesh (Baxtiyor)",
        ru_name="Счастливчик",
        emoji="🧙",
        team=Team.NEUTRAL,
        description="Omadli zohid. Har qanday o'lim yoki tungi suiqasddan 50% ehtimollik bilan mo'jizaviy qutuladi.",
        ru_description="Счастливчик. С вероятностью 50% чудесным образом избегает любой смерти ночью.",
        night_prompt="",
        action_type="none"
    ),
    "yurist": RoleInfo(
        code="yurist",
        name="Xolis Hakam (Ombudsman)",
        ru_name="Омбудсмен",
        emoji="💼",
        team=Team.NEUTRAL,
        description="Xolis huquqshunos. Shahar va mafiya o'rtasida tenglikni saqlashga harakat qiladi.",
        ru_description="Независимый юрист. Сохраняет баланс между городом и мафией.",
        night_prompt="Himoyalash uchun o'yinchini tanlang:",
        action_type="neutral_judge"
    ),
    "anarxist": RoleInfo(
        code="anarxist",
        name="Anarxist (Tartibsizlik Ustasi)",
        ru_name="Анархист",
        emoji="🏴",
        team=Team.NEUTRAL,
        description="Qonunsizlik tarafdori. Kunduzgi yoki tungi qoidalarni buzib, kutilmagan xaos yaratadi.",
        ru_description="Анархист. Сеет хаос и путает результаты голосования.",
        night_prompt="Xaos yaratish uchun o'yinchini tanlang:",
        action_type="anarchy_disrupt"
    ),
    "omon_koluvchi": RoleInfo(
        code="omon_koluvchi",
        name="Omon Qoluvchi (Survivor)",
        ru_name="Выживший",
        emoji="⛺",
        team=Team.NEUTRAL,
        description="Yagona maqsadi o'yin oxirigacha har qanday yo'l bilan tirik qolish. O'yinda 2 marta o'zini bunkerda yashira oladi.",
        ru_description="Выживший. Его цель — дожить до конца игры с любой победившей командой.",
        night_prompt="Bunkerga yashirinish uchun o'zingizni tanlang:",
        action_type="survivor_bunker"
    ),
}

# Role distribution dynamically based on player count
def get_role_distribution(player_count: int) -> List[str]:
    """
    Distributes active roles dynamically based on player count.
    Never assigns boring plain citizens. Balanced and exciting for all game sizes.
    """
    if player_count <= 3:
        # Minimal lobby: 1 mafia, 1 cop, 1 town doctor
        return ["don", "komissar", "laborant"][:player_count]

    elif player_count == 4:
        # 4 players: 1 mafia, 1 cop, 1 doctor, 1 mayor
        return ["don", "komissar", "laborant", "rais"]

    elif player_count == 5:
        # 5 players: 1 mafia only! (With 2 mafias, 1 death = 2v2 = instant game over)
        return ["don", "komissar", "laborant", "rais", "kazanova"]

    elif player_count == 6:
        # 6 players: 2 mafia vs 4 town
        return ["don", "mafia", "komissar", "laborant", "kazanova", "snayper"]

    elif player_count == 7:
        # 7 players: 2 mafia vs 5 town (or 1 neutral)
        return ["don", "mafia", "komissar", "laborant", "rais", "kazanova", "tansoqchi"]

    elif player_count == 8:
        # 8 players: 2 mafia, 1 maniac, 5 town
        return ["don", "mafia", "komissar", "serjant", "laborant", "rais", "kazanova", "kotil"]

    elif player_count == 9:
        # 9 players: 2 mafia, 1 maniac, 6 town/special
        return ["don", "mafia", "komissar", "serjant", "laborant", "rais", "kazanova", "advokat", "kotil"]

    elif player_count == 10:
        # 10 players: 2 mafia, 1 maniac, 1 neutral/vampire, 6 town
        return ["don", "mafia", "komissar", "serjant", "laborant", "rais", "kazanova", "ximik", "advokat", "kotil"]

    # For 11+ players: dynamic sampling from rich pools
    # Base mandatory setup:
    base = [
        "don", "mafia", "komissar", "serjant", "laborant", "rais",
        "kazanova", "kotil", "advokat", "snayper", "tansoqchi"
    ]
    pool = list(base)

    town_pool = [
        "detektiv", "psixolog", "veteran", "uchastkovoy", "hakim", "shahar_soqchisi",
        "ruhoniy", "tez_yordam", "mantiqchi", "qariya", "advokat_shahar", "ovchi",
        "inspektor", "qo_riqchi", "qutqaruvchi", "shpion", "sehrgar", "konchi", "kupidon"
    ]
    mafia_pool = [
        "kadr", "xaker", "qora_shifokor", "suqasdqor", "bandit", "provokator",
        "kontrabandist", "soxta_guvoh", "shantajchi", "snayper_mafiya",
        "ayg_oqchi_mafiya", "mina_koyuvchi"
    ]
    evil_neutral_pool = [
        "qonxor", "zaharlovchi", "piroman", "illuzionist", "arvoh", "jallod", "bori", "yirtqich",
        "vampir_graf", "vampir", "gipnozchi", "jodugar", "nekromant", "qiyofa_ugrisi",
        "masxaraboz", "omadli_darvesh", "yurist", "anarxist", "omon_koluvchi", "ogri", "terrorist"
    ]

    # Shuffle extra pools
    r_town = list(town_pool)
    r_mafia = list(mafia_pool)
    r_evil = list(evil_neutral_pool)
    random.seed(player_count * 37)
    random.shuffle(r_town)
    random.shuffle(r_mafia)
    random.shuffle(r_evil)

    t_idx = 0
    m_idx = 0
    e_idx = 0

    while len(pool) < player_count:
        # Proportion: 3 town, 1 mafia, 1 evil/neutral
        cycle = len(pool) % 5
        if cycle in [0, 1, 2]:
            if t_idx < len(r_town):
                pool.append(r_town[t_idx])
                t_idx += 1
            else:
                pool.append("laborant")
        elif cycle == 3:
            if m_idx < len(r_mafia):
                pool.append(r_mafia[m_idx])
                m_idx += 1
            else:
                pool.append("mafia")
        else:
            if e_idx < len(r_evil):
                pool.append(r_evil[e_idx])
                e_idx += 1
            else:
                pool.append("kotil")

    return pool[:player_count]

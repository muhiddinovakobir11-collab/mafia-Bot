from enum import Enum
from typing import Dict, Any

class Team(str, Enum):
    CITIZEN = "citizen"      # Tinch kuchlar / Shahar
    MAFIA = "mafia"          # Mafiya to'dasi
    MANIAC = "maniac"        # Qotil (Yakka o'zi)
    VAMPIRE = "vampire"      # Vampir
    NEUTRAL = "neutral"      # Neytral

class RoleInfo:
    def __init__(
        self,
        code: str,
        name: str,
        emoji: str,
        team: Team,
        description: str,
        night_prompt: str = "",
        action_type: str = "none", # 'kill', 'check', 'heal', 'poison', 'distract', 'bite', 'none'
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
}

# Role distribution based on player count
def get_role_distribution(player_count: int) -> list[str]:
    """
    Distributes active roles dynamically based on player count.
    Balanced for small and large lobbies.
    """
    if player_count <= 3:
        # Minimal setup: 1 mafia, 1 cop, 1 citizen
        pool = ["don", "komissar", "citizen"]
    elif player_count == 4:
        pool = ["don", "komissar", "laborant", "citizen"]
    elif player_count == 5:
        pool = ["don", "mafia", "komissar", "laborant", "citizen"]
    elif player_count == 6:
        pool = ["don", "mafia", "komissar", "laborant", "kazanova", "citizen"]
    elif player_count == 7:
        pool = ["don", "mafia", "komissar", "laborant", "rais", "kazanova", "kotil"]
    elif player_count == 8:
        pool = ["don", "mafia", "komissar", "serjant", "laborant", "rais", "kazanova", "kotil"]
    elif player_count == 9:
        pool = ["don", "mafia", "komissar", "serjant", "laborant", "rais", "kazanova", "advokat", "kotil"]
    elif player_count == 10:
        pool = ["don", "mafia", "komissar", "serjant", "laborant", "rais", "kazanova", "ximik", "advokat", "kotil"]
    elif player_count >= 11:
        pool = ["don", "mafia", "komissar", "serjant", "laborant", "rais", "kazanova", "ximik", "vampir", "konchi", "kotil"]
        extra_roles = ["advokat", "sehrgar", "mafia", "laborant", "konchi", "rais", "vampir", "shpion", "kupidon", "terrorist"]
        idx = 0
        while len(pool) < player_count:
            pool.append(extra_roles[idx % len(extra_roles)])
            idx += 1
    return pool[:player_count]

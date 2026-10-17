# Linko Sayohat: mashhur shaharlar (IATA shahar kodi) - aviachipta qidiruvi uchun.
# Ro'yxatda yo'q shahar uchun foydalanuvchi 3 harfli IATA kodini o'zi yozishi mumkin (masalan, NKG).
# Har bir yozuv: (kod, mamlakat, {til: nom})

CITIES = [
    # O'zbekiston
    ("TAS", "UZ", {"uz": "Toshkent", "ru": "Ташкент", "en": "Tashkent", "zh": "塔什干"}),
    ("SKD", "UZ", {"uz": "Samarqand", "ru": "Самарканд", "en": "Samarkand", "zh": "撒马尔罕"}),
    ("BHK", "UZ", {"uz": "Buxoro", "ru": "Бухара", "en": "Bukhara", "zh": "布哈拉"}),
    ("FEG", "UZ", {"uz": "Farg'ona", "ru": "Фергана", "en": "Fergana", "zh": "费尔干纳"}),
    ("NMA", "UZ", {"uz": "Namangan", "ru": "Наманган", "en": "Namangan", "zh": "纳曼干"}),
    ("AZN", "UZ", {"uz": "Andijon", "ru": "Андижан", "en": "Andijan", "zh": "安集延"}),
    ("UGC", "UZ", {"uz": "Urganch", "ru": "Ургенч", "en": "Urgench", "zh": "乌尔根奇"}),
    ("NCU", "UZ", {"uz": "Nukus", "ru": "Нукус", "en": "Nukus", "zh": "努库斯"}),
    ("TMJ", "UZ", {"uz": "Termiz", "ru": "Термез", "en": "Termez", "zh": "铁尔梅兹"}),
    ("KSQ", "UZ", {"uz": "Qarshi", "ru": "Карши", "en": "Karshi", "zh": "卡尔希"}),
    ("NVI", "UZ", {"uz": "Navoiy", "ru": "Навои", "en": "Navoi", "zh": "纳沃伊"}),
    # Xitoy
    ("BJS", "CN", {"uz": "Pekin", "ru": "Пекин", "en": "Beijing", "zh": "北京"}),
    ("SHA", "CN", {"uz": "Shanxay", "ru": "Шанхай", "en": "Shanghai", "zh": "上海"}),
    ("NKG", "CN", {"uz": "Nankin", "ru": "Нанкин", "en": "Nanjing", "zh": "南京"}),
    ("CAN", "CN", {"uz": "Guanchjou", "ru": "Гуанчжоу", "en": "Guangzhou", "zh": "广州"}),
    ("SZX", "CN", {"uz": "Shenchjen", "ru": "Шэньчжэнь", "en": "Shenzhen", "zh": "深圳"}),
    ("URC", "CN", {"uz": "Urumchi", "ru": "Урумчи", "en": "Urumqi", "zh": "乌鲁木齐"}),
    ("HGH", "CN", {"uz": "Xanchjou", "ru": "Ханчжоу", "en": "Hangzhou", "zh": "杭州"}),
    ("CTU", "CN", {"uz": "Chengdu", "ru": "Чэнду", "en": "Chengdu", "zh": "成都"}),
    ("XIY", "CN", {"uz": "Sian", "ru": "Сиань", "en": "Xi'an", "zh": "西安"}),
    ("HKG", "HK", {"uz": "Gonkong", "ru": "Гонконг", "en": "Hong Kong", "zh": "香港"}),
    # Rossiya va MDH
    ("MOW", "RU", {"uz": "Moskva", "ru": "Москва", "en": "Moscow", "zh": "莫斯科"}),
    ("LED", "RU", {"uz": "Sankt-Peterburg", "ru": "Санкт-Петербург", "en": "Saint Petersburg", "zh": "圣彼得堡"}),
    ("KZN", "RU", {"uz": "Qozon", "ru": "Казань", "en": "Kazan", "zh": "喀山"}),
    ("SVX", "RU", {"uz": "Yekaterinburg", "ru": "Екатеринбург", "en": "Yekaterinburg", "zh": "叶卡捷琳堡"}),
    ("OVB", "RU", {"uz": "Novosibirsk", "ru": "Новосибирск", "en": "Novosibirsk", "zh": "新西伯利亚"}),
    ("KRR", "RU", {"uz": "Krasnodar", "ru": "Краснодар", "en": "Krasnodar", "zh": "克拉斯诺达尔"}),
    ("ALA", "KZ", {"uz": "Olmaota", "ru": "Алматы", "en": "Almaty", "zh": "阿拉木图"}),
    ("NQZ", "KZ", {"uz": "Astana", "ru": "Астана", "en": "Astana", "zh": "阿斯塔纳"}),
    ("FRU", "KG", {"uz": "Bishkek", "ru": "Бишкек", "en": "Bishkek", "zh": "比什凯克"}),
    ("DYU", "TJ", {"uz": "Dushanbe", "ru": "Душанбе", "en": "Dushanbe", "zh": "杜尚别"}),
    ("BAK", "AZ", {"uz": "Boku", "ru": "Баку", "en": "Baku", "zh": "巴库"}),
    ("TBS", "GE", {"uz": "Tbilisi", "ru": "Тбилиси", "en": "Tbilisi", "zh": "第比利斯"}),
    # Turkiya, Yaqin Sharq
    ("IST", "TR", {"uz": "Istanbul", "ru": "Стамбул", "en": "Istanbul", "zh": "伊斯坦布尔"}),
    ("AYT", "TR", {"uz": "Antalya", "ru": "Анталья", "en": "Antalya", "zh": "安塔利亚"}),
    ("DXB", "AE", {"uz": "Dubay", "ru": "Дубай", "en": "Dubai", "zh": "迪拜"}),
    ("JED", "SA", {"uz": "Jidda", "ru": "Джидда", "en": "Jeddah", "zh": "吉达"}),
    ("MED", "SA", {"uz": "Madina", "ru": "Медина", "en": "Medina", "zh": "麦地那"}),
    # Osiyo
    ("SEL", "KR", {"uz": "Seul", "ru": "Сеул", "en": "Seoul", "zh": "首尔"}),
    ("TYO", "JP", {"uz": "Tokio", "ru": "Токио", "en": "Tokyo", "zh": "东京"}),
    ("BKK", "TH", {"uz": "Bangkok", "ru": "Бангкок", "en": "Bangkok", "zh": "曼谷"}),
    ("KUL", "MY", {"uz": "Kuala-Lumpur", "ru": "Куала-Лумпур", "en": "Kuala Lumpur", "zh": "吉隆坡"}),
    ("DEL", "IN", {"uz": "Dehli", "ru": "Дели", "en": "Delhi", "zh": "德里"}),
    # Yevropa
    ("LON", "GB", {"uz": "London", "ru": "Лондон", "en": "London", "zh": "伦敦"}),
    ("PAR", "FR", {"uz": "Parij", "ru": "Париж", "en": "Paris", "zh": "巴黎"}),
    ("BER", "DE", {"uz": "Berlin", "ru": "Берлин", "en": "Berlin", "zh": "柏林"}),
    ("FRA", "DE", {"uz": "Frankfurt", "ru": "Франкфурт", "en": "Frankfurt", "zh": "法兰克福"}),
    ("MUC", "DE", {"uz": "Myunxen", "ru": "Мюнхен", "en": "Munich", "zh": "慕尼黑"}),
    ("WAW", "PL", {"uz": "Varshava", "ru": "Варшава", "en": "Warsaw", "zh": "华沙"}),
    ("RIX", "LV", {"uz": "Riga", "ru": "Рига", "en": "Riga", "zh": "里加"}),
    ("VNO", "LT", {"uz": "Vilnyus", "ru": "Вильнюс", "en": "Vilnius", "zh": "维尔纽斯"}),
    ("PRG", "CZ", {"uz": "Praga", "ru": "Прага", "en": "Prague", "zh": "布拉格"}),
    ("ROM", "IT", {"uz": "Rim", "ru": "Рим", "en": "Rome", "zh": "罗马"}),
    ("NYC", "US", {"uz": "Nyu-York", "ru": "Нью-Йорк", "en": "New York", "zh": "纽约"}),
]

CITY_CODES = {c[0] for c in CITIES}


def city_list(lang):
    """Sahifa uchun: [{code, name, alt}] - alt barcha tillardagi nomlar (qidiruv uchun)."""
    out = []
    for code, country, names in CITIES:
        out.append({
            "code": code,
            "country": country,
            "name": names.get(lang) or names["en"],
            "alt": " ".join(sorted(set(names.values()))).lower(),
        })
    return out


def city_name(code, lang):
    for c, _country, names in CITIES:
        if c == code:
            return names.get(lang) or names["en"]
    return code

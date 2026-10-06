# -*- coding: utf-8 -*-
"""Linko joylashuv katalogi: davlat -> viloyat -> tuman.
Yangi davlat, viloyat yoki tuman qo'shish uchun shu faylga yozish kifoya (boshqa joyga tegish shart emas).

COUNTRIES: [(kod, {til: nom}, [(viloyat, [tumanlar])])]
Tumanlari bo'lmagan viloyat uchun bo'sh ro'yxat qoldiring - u holda tuman tanlanmaydi.
"""

UZ_REGIONS = [
    ("Toshkent shahri", ["Bektemir", "Chilonzor", "Yashnobod", "Mirobod", "Mirzo Ulug'bek", "Sergeli",
                         "Shayxontohur", "Olmazor", "Uchtepa", "Yakkasaroy", "Yunusobod", "Yangihayot"]),
    ("Toshkent viloyati", ["Nurafshon shahri", "Chirchiq shahri", "Angren shahri", "Olmaliq shahri", "Bekobod shahri",
                           "Ohangaron shahri", "Yangiyo'l shahri", "Bekobod", "Bo'stonliq", "Bo'ka", "Chinoz", "Qibray",
                           "Ohangaron", "Oqqo'rg'on", "Parkent", "Piskent", "Quyi Chirchiq", "O'rta Chirchiq",
                           "Yangiyo'l", "Yuqori Chirchiq", "Zangiota", "Toshkent tumani"]),
    ("Andijon viloyati", ["Andijon shahri", "Xonobod shahri", "Andijon tumani", "Asaka", "Baliqchi", "Bo'z",
                          "Buloqboshi", "Izboskan", "Jalaquduq", "Xo'jaobod", "Qo'rg'ontepa", "Marhamat",
                          "Oltinko'l", "Paxtaobod", "Shahrixon", "Ulug'nor"]),
    ("Buxoro viloyati", ["Buxoro shahri", "Kogon shahri", "Buxoro tumani", "G'ijduvon", "Jondor", "Kogon", "Olot",
                         "Peshku", "Qorako'l", "Qorovulbozor", "Romitan", "Shofirkon", "Vobkent"]),
    ("Farg'ona viloyati", ["Farg'ona shahri", "Marg'ilon shahri", "Qo'qon shahri", "Quvasoy shahri", "Beshariq",
                           "Bog'dod", "Buvayda", "Dang'ara", "Farg'ona tumani", "Furqat", "Oltiariq", "O'zbekiston",
                           "Quva", "Qo'shtepa", "Rishton", "So'x", "Toshloq", "Uchko'prik", "Yozyovon"]),
    ("Jizzax viloyati", ["Jizzax shahri", "Arnasoy", "Baxmal", "Do'stlik", "Forish", "G'allaorol", "Sharof Rashidov",
                         "Mirzacho'l", "Paxtakor", "Yangiobod", "Zafarobod", "Zarbdor", "Zomin"]),
    ("Namangan viloyati", ["Namangan shahri", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Namangan tumani", "Norin",
                           "Pop", "To'raqo'rg'on", "Uchqo'rg'on", "Uychi", "Yangiqo'rg'on"]),
    ("Navoiy viloyati", ["Navoiy shahri", "Zarafshon shahri", "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa",
                         "Tomdi", "Uchquduq", "Xatirchi"]),
    ("Qashqadaryo viloyati", ["Qarshi shahri", "Shahrisabz shahri", "Chiroqchi", "Dehqonobod", "G'uzor", "Kasbi",
                              "Kitob", "Ko'kdala", "Koson", "Mirishkor", "Muborak", "Nishon", "Qamashi",
                              "Qarshi tumani", "Shahrisabz", "Yakkabog'"]),
    ("Samarqand viloyati", ["Samarqand shahri", "Kattaqo'rg'on shahri", "Bulung'ur", "Ishtixon", "Jomboy",
                            "Kattaqo'rg'on", "Narpay", "Nurobod", "Oqdaryo", "Pastdarg'om", "Paxtachi", "Payariq",
                            "Qo'shrabot", "Samarqand tumani", "Toyloq", "Urgut"]),
    ("Sirdaryo viloyati", ["Guliston shahri", "Yangiyer shahri", "Shirin shahri", "Boyovut", "Guliston", "Mirzaobod",
                           "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo", "Xovos"]),
    ("Surxondaryo viloyati", ["Termiz shahri", "Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on", "Muzrabot",
                              "Oltinsoy", "Qiziriq", "Qumqo'rg'on", "Sariosiyo", "Sherobod", "Sho'rchi",
                              "Termiz tumani", "Uzun"]),
    ("Xorazm viloyati", ["Urganch shahri", "Xiva shahri", "Bog'ot", "Gurlan", "Hazorasp", "Xonqa", "Qo'shko'pir",
                         "Shovot", "Tuproqqal'a", "Urganch tumani", "Xiva", "Yangiariq", "Yangibozor"]),
    ("Qoraqalpog'iston Respublikasi", ["Nukus shahri", "Taxiatosh shahri", "Amudaryo", "Beruniy", "Bo'zatov", "Chimboy",
                                       "Ellikqal'a", "Kegeyli", "Mo'ynoq", "Nukus tumani", "Qanliko'l", "Qo'ng'irot",
                                       "Qorao'zak", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli"]),
]

KZ_REGIONS = [
    ("Astana", []), ("Almaty", []), ("Shymkent", []),
    ("Akmola", []), ("Aktobe", []), ("Almaty region", []), ("Atyrau", []), ("East Kazakhstan", []),
    ("Jambyl", []), ("Karaganda", []), ("Kostanay", []), ("Kyzylorda", []), ("Mangystau", []),
    ("North Kazakhstan", []), ("Pavlodar", []), ("Turkistan", []), ("West Kazakhstan", []),
    ("Abai", []), ("Jetisu", []), ("Ulytau", []),
]

KG_REGIONS = [
    ("Bishkek", []), ("Osh city", []), ("Batken", []), ("Chuy", []), ("Issyk-Kul", []),
    ("Jalal-Abad", []), ("Naryn", []), ("Osh", []), ("Talas", []),
]

TJ_REGIONS = [
    ("Dushanbe", []), ("Sughd", []), ("Khatlon", []), ("Gorno-Badakhshan", []), ("Districts of Republican Subordination", []),
]

TM_REGIONS = [
    ("Ashgabat", []), ("Ahal", []), ("Balkan", []), ("Dashoguz", []), ("Lebap", []), ("Mary", []),
]

RU_REGIONS = [
    ("Moscow", []), ("Moscow Oblast", []), ("Saint Petersburg", []), ("Leningrad Oblast", []), ("Tatarstan", []),
    ("Bashkortostan", []), ("Krasnodar Krai", []), ("Sverdlovsk Oblast", []), ("Novosibirsk Oblast", []),
    ("Chelyabinsk Oblast", []), ("Samara Oblast", []), ("Nizhny Novgorod Oblast", []), ("Rostov Oblast", []),
    ("Dagestan", []), ("Chechnya", []), ("Krasnoyarsk Krai", []), ("Perm Krai", []), ("Voronezh Oblast", []),
    ("Volgograd Oblast", []), ("Saratov Oblast", []), ("Tyumen Oblast", []), ("Irkutsk Oblast", []),
    ("Orenburg Oblast", []), ("Omsk Oblast", []), ("Kemerovo Oblast", []), ("Primorsky Krai", []),
    ("Khabarovsk Krai", []), ("Kaliningrad Oblast", []), ("Stavropol Krai", []), ("Ulyanovsk Oblast", []),
]

TR_REGIONS = [
    ("Istanbul", []), ("Ankara", []), ("Izmir", []), ("Bursa", []), ("Antalya", []), ("Adana", []),
    ("Konya", []), ("Gaziantep", []), ("Kayseri", []), ("Mersin", []), ("Eskisehir", []), ("Diyarbakir", []),
    ("Samsun", []), ("Trabzon", []), ("Sakarya", []), ("Kocaeli", []), ("Manisa", []), ("Mugla", []),
]

US_REGIONS = [(n, []) for n in (
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida",
    "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
    "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska",
    "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas",
    "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "District of Columbia")]

GB_REGIONS = [("England", []), ("Scotland", []), ("Wales", []), ("Northern Ireland", [])]

DE_REGIONS = [(n, []) for n in (
    "Baden-Württemberg", "Bavaria", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hesse", "Lower Saxony",
    "Mecklenburg-Vorpommern", "North Rhine-Westphalia", "Rhineland-Palatinate", "Saarland", "Saxony",
    "Saxony-Anhalt", "Schleswig-Holstein", "Thuringia")]

CN_REGIONS = [(n, []) for n in (
    "Beijing", "Shanghai", "Tianjin", "Chongqing", "Guangdong", "Zhejiang", "Jiangsu", "Shandong", "Henan", "Sichuan",
    "Hubei", "Hunan", "Fujian", "Anhui", "Hebei", "Shaanxi", "Liaoning", "Jilin", "Heilongjiang", "Yunnan",
    "Guangxi", "Jiangxi", "Shanxi", "Guizhou", "Gansu", "Inner Mongolia", "Xinjiang", "Tibet", "Hainan",
    "Ningxia", "Qinghai", "Hong Kong", "Macau")]

KR_REGIONS = [(n, []) for n in (
    "Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Ulsan", "Sejong", "Gyeonggi", "Gangwon",
    "North Chungcheong", "South Chungcheong", "North Jeolla", "South Jeolla", "North Gyeongsang",
    "South Gyeongsang", "Jeju")]

AE_REGIONS = [(n, []) for n in ("Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah")]

COUNTRIES = [
    ("UZ", {"uz": "O'zbekiston", "ru": "Узбекистан", "en": "Uzbekistan", "zh": "乌兹别克斯坦"}, UZ_REGIONS),
    ("KZ", {"uz": "Qozog'iston", "ru": "Казахстан", "en": "Kazakhstan", "zh": "哈萨克斯坦"}, KZ_REGIONS),
    ("KG", {"uz": "Qirg'iziston", "ru": "Кыргызстан", "en": "Kyrgyzstan", "zh": "吉尔吉斯斯坦"}, KG_REGIONS),
    ("TJ", {"uz": "Tojikiston", "ru": "Таджикистан", "en": "Tajikistan", "zh": "塔吉克斯坦"}, TJ_REGIONS),
    ("TM", {"uz": "Turkmaniston", "ru": "Туркменистан", "en": "Turkmenistan", "zh": "土库曼斯坦"}, TM_REGIONS),
    ("RU", {"uz": "Rossiya", "ru": "Россия", "en": "Russia", "zh": "俄罗斯"}, RU_REGIONS),
    ("TR", {"uz": "Turkiya", "ru": "Турция", "en": "Turkey", "zh": "土耳其"}, TR_REGIONS),
    ("US", {"uz": "AQSH", "ru": "США", "en": "United States", "zh": "美国"}, US_REGIONS),
    ("GB", {"uz": "Buyuk Britaniya", "ru": "Великобритания", "en": "United Kingdom", "zh": "英国"}, GB_REGIONS),
    ("DE", {"uz": "Germaniya", "ru": "Германия", "en": "Germany", "zh": "德国"}, DE_REGIONS),
    ("CN", {"uz": "Xitoy", "ru": "Китай", "en": "China", "zh": "中国"}, CN_REGIONS),
    ("KR", {"uz": "Janubiy Koreya", "ru": "Южная Корея", "en": "South Korea", "zh": "韩国"}, KR_REGIONS),
    ("AE", {"uz": "BAA", "ru": "ОАЭ", "en": "United Arab Emirates", "zh": "阿联酋"}, AE_REGIONS),
    ("AZ", {"uz": "Ozarbayjon", "ru": "Азербайджан", "en": "Azerbaijan", "zh": "阿塞拜疆"}, []),
    ("AF", {"uz": "Afg'oniston", "ru": "Афганистан", "en": "Afghanistan", "zh": "阿富汗"}, []),
    ("UA", {"uz": "Ukraina", "ru": "Украина", "en": "Ukraine", "zh": "乌克兰"}, []),
    ("BY", {"uz": "Belarus", "ru": "Беларусь", "en": "Belarus", "zh": "白俄罗斯"}, []),
    ("GE", {"uz": "Gruziya", "ru": "Грузия", "en": "Georgia", "zh": "格鲁吉亚"}, []),
    ("AM", {"uz": "Armaniston", "ru": "Армения", "en": "Armenia", "zh": "亚美尼亚"}, []),
    ("IR", {"uz": "Eron", "ru": "Иран", "en": "Iran", "zh": "伊朗"}, []),
    ("IN", {"uz": "Hindiston", "ru": "Индия", "en": "India", "zh": "印度"}, []),
    ("JP", {"uz": "Yaponiya", "ru": "Япония", "en": "Japan", "zh": "日本"}, []),
    ("FR", {"uz": "Fransiya", "ru": "Франция", "en": "France", "zh": "法国"}, []),
    ("SA", {"uz": "Saudiya Arabistoni", "ru": "Саудовская Аравия", "en": "Saudi Arabia", "zh": "沙特阿拉伯"}, []),
    ("OTHER", {"uz": "Boshqa davlat", "ru": "Другая страна", "en": "Other country", "zh": "其他国家"}, []),
]

_BY_CODE = {c[0]: c for c in COUNTRIES}


def country_list(lang="uz"):
    """[{code, name}] - tanlov ro'yxati uchun."""
    return [{"code": code, "name": names.get(lang) or names["en"]} for code, names, _ in COUNTRIES]


def region_list(code):
    c = _BY_CODE.get(code)
    return [name for name, _ in c[2]] if c else []


def district_list(code, region):
    c = _BY_CODE.get(code)
    if not c:
        return []
    for name, districts in c[2]:
        if name == region:
            return list(districts)
    return []


def country_name(code, lang="uz"):
    c = _BY_CODE.get(code)
    if not c:
        return code or ""
    return c[1].get(lang) or c[1]["en"]


def is_valid(code, region="", district=""):
    """Tanlangan qiymatlar katalogga mos keladimi."""
    if code and code not in _BY_CODE:
        return False
    if region and region not in region_list(code):
        return False
    if district and district not in district_list(code, region):
        return False
    return True

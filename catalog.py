# -*- coding: utf-8 -*-
"""Do'kon katalogi: kategoriyalar, subkategoriyalar, ranglar va o'lcham tizimlari (uz / ru / en / zh)."""

LANGS = ("uz", "ru", "en", "zh")


def _pick(names, lang):
    idx = LANGS.index(lang) if lang in LANGS else 0
    return names[idx]


# ---------- Ranglar: (id, hex, uz, ru, en, zh) ----------
COLORS = [
    ("black", "#111111", "Qora", "Чёрный", "Black", "黑色"),
    ("white", "#f5f5f5", "Oq", "Белый", "White", "白色"),
    ("gray", "#9ca3af", "Kulrang", "Серый", "Gray", "灰色"),
    ("red", "#ef4444", "Qizil", "Красный", "Red", "红色"),
    ("burgundy", "#7f1d1d", "Bordo", "Бордовый", "Burgundy", "酒红色"),
    ("orange", "#f97316", "To'q sariq", "Оранжевый", "Orange", "橙色"),
    ("yellow", "#facc15", "Sariq", "Жёлтый", "Yellow", "黄色"),
    ("green", "#22c55e", "Yashil", "Зелёный", "Green", "绿色"),
    ("khaki", "#6b7a3a", "Xaki", "Хаки", "Khaki", "卡其绿"),
    ("turquoise", "#14b8a6", "Firuza", "Бирюзовый", "Turquoise", "青色"),
    ("lightblue", "#7dd3fc", "Havorang", "Голубой", "Light blue", "浅蓝色"),
    ("blue", "#3b82f6", "Ko'k", "Синий", "Blue", "蓝色"),
    ("navy", "#1e3a8a", "To'q ko'k", "Тёмно-синий", "Navy", "藏青色"),
    ("purple", "#8b5cf6", "Binafsha", "Фиолетовый", "Purple", "紫色"),
    ("pink", "#ec4899", "Pushti", "Розовый", "Pink", "粉色"),
    ("brown", "#92400e", "Jigarrang", "Коричневый", "Brown", "棕色"),
    ("beige", "#e7d3b0", "Bej", "Бежевый", "Beige", "米色"),
    ("gold", "#d4af37", "Oltin", "Золотой", "Gold", "金色"),
    ("silver", "#c0c0c0", "Kumush", "Серебристый", "Silver", "银色"),
    ("multi", "multi", "Rang-barang", "Разноцветный", "Multicolor", "多色"),
]
_COLOR_MAP = {c[0]: c for c in COLORS}


def color_info(token, lang="uz"):
    """Katalogdagi rang bo'lsa {id, hex, name}, aks holda None."""
    c = _COLOR_MAP.get((token or "").strip())
    if not c:
        return None
    return {"id": c[0], "hex": c[1], "name": _pick(c[2:], lang)}


def color_name(token, lang="uz"):
    info = color_info(token, lang)
    return info["name"] if info else (token or "")


def color_list(lang="uz"):
    return [{"id": c[0], "hex": c[1], "name": _pick(c[2:], lang)} for c in COLORS]


# ---------- O'lcham tizimlari ----------
SIZE_SYSTEMS = {
    "clothes": ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "ONE"],
    "shoes": [str(n) for n in range(35, 48)],
    "kids_shoes": [str(n) for n in range(18, 35)],
    "kids_clothes": ["0-3M", "3-6M", "6-12M", "1-2Y", "2-3Y", "3-4Y", "4-5Y", "5-6Y", "6-7Y", "7-8Y", "9-10Y", "11-12Y", "13-14Y"],
    "volume": ["30ml", "50ml", "100ml", "150ml", "200ml", "250ml", "500ml", "1L"],
    "weight": ["100g", "250g", "500g", "1kg", "2kg", "5kg", "10kg"],
    "storage": ["32GB", "64GB", "128GB", "256GB", "512GB", "1TB"],
    "none": [],
}
SIZE_SYSTEM_NAMES = {
    "clothes": ("Kiyim o'lchami", "Размер одежды", "Clothing size", "服装尺码"),
    "shoes": ("Poyabzal o'lchami (EU)", "Размер обуви (EU)", "Shoe size (EU)", "鞋码 (EU)"),
    "kids_shoes": ("Bolalar poyabzali (EU)", "Детская обувь (EU)", "Kids' shoe size (EU)", "童鞋码 (EU)"),
    "kids_clothes": ("Bolalar kiyimi (yosh)", "Детская одежда (возраст)", "Kids' clothing (age)", "童装 (年龄)"),
    "volume": ("Hajm", "Объём", "Volume", "容量"),
    "weight": ("Og'irlik", "Вес", "Weight", "重量"),
    "storage": ("Xotira", "Память", "Storage", "存储"),
    "none": ("O'lcham", "Размер", "Size", "尺寸"),
}
_UNIT_LABELS = {
    "M": ("oy", "мес.", "mo", "个月"),
    "Y": ("yosh", "лет", "yr", "岁"),
}
_ONE_LABEL = ("Universal", "Универсальный", "One size", "均码")


def size_label(token, lang="uz"):
    token = (token or "").strip()
    if token == "ONE":
        return _pick(_ONE_LABEL, lang)
    m = None
    import re
    m = re.match(r"^(\d+-\d+)([MY])$", token)
    if m:
        return m.group(1) + " " + _pick(_UNIT_LABELS[m.group(2)], lang)
    return token


def size_system_name(system, lang="uz"):
    return _pick(SIZE_SYSTEM_NAMES.get(system, SIZE_SYSTEM_NAMES["none"]), lang)


# ---------- Kategoriyalar ----------
# (id, emoji, uz, ru, en, zh, size_system, [subkategoriyalar: (id, uz, ru, en, zh, size_system | None)])
CATEGORIES = [
    ("fashion", "👗", "Kiyim-kechak", "Одежда", "Clothing", "服装", "clothes", [
        ("women", "Ayollar kiyimi", "Женская одежда", "Women's clothing", "女装", None),
        ("men", "Erkaklar kiyimi", "Мужская одежда", "Men's clothing", "男装", None),
        ("kids", "Bolalar kiyimi", "Детская одежда", "Kids' clothing", "童装", "kids_clothes"),
        ("outer", "Ustki kiyim", "Верхняя одежда", "Outerwear", "外套", None),
        ("underwear", "Ichki kiyim", "Бельё", "Underwear", "内衣", None),
        ("sportwear", "Sport kiyimi", "Спортивная одежда", "Sportswear", "运动服", None),
        ("traditional", "Milliy kiyim", "Национальная одежда", "Traditional wear", "民族服饰", None),
    ]),
    ("shoes", "👟", "Poyabzal", "Обувь", "Footwear", "鞋靴", "shoes", [
        ("women", "Ayollar poyabzali", "Женская обувь", "Women's shoes", "女鞋", None),
        ("men", "Erkaklar poyabzali", "Мужская обувь", "Men's shoes", "男鞋", None),
        ("kids", "Bolalar poyabzali", "Детская обувь", "Kids' shoes", "童鞋", "kids_shoes"),
        ("sport", "Krossovkalar", "Кроссовки", "Sneakers", "运动鞋", None),
        ("slippers", "Shippak va sandal", "Тапочки и сандалии", "Slippers & sandals", "拖鞋和凉鞋", None),
    ]),
    ("accessories", "👜", "Sumka va aksessuarlar", "Сумки и аксессуары", "Bags & accessories", "箱包配饰", "none", [
        ("bags", "Sumkalar", "Сумки", "Bags", "包", None),
        ("watches", "Soatlar", "Часы", "Watches", "手表", None),
        ("jewelry", "Zargarlik buyumlari", "Украшения", "Jewelry", "首饰", None),
        ("glasses", "Ko'zoynaklar", "Очки", "Glasses", "眼镜", None),
        ("other", "Boshqa aksessuarlar", "Другие аксессуары", "Other accessories", "其他配饰", None),
    ]),
    ("electronics", "📱", "Elektronika", "Электроника", "Electronics", "电子产品", "none", [
        ("phones", "Telefonlar", "Телефоны", "Phones", "手机", "storage"),
        ("laptops", "Noutbuklar", "Ноутбуки", "Laptops", "笔记本电脑", "storage"),
        ("tablets", "Planshetlar", "Планшеты", "Tablets", "平板电脑", "storage"),
        ("audio", "Quloqchin va audio", "Наушники и аудио", "Headphones & audio", "耳机音响", None),
        ("tv", "Televizorlar", "Телевизоры", "TVs", "电视", None),
        ("gadgets", "Aksessuar va gadjetlar", "Аксессуары и гаджеты", "Accessories & gadgets", "配件与小工具", None),
    ]),
    ("home", "🏠", "Uy-ro'zg'or", "Дом и быт", "Home & living", "家居", "none", [
        ("furniture", "Mebel", "Мебель", "Furniture", "家具", None),
        ("kitchen", "Oshxona", "Кухня", "Kitchen", "厨房用品", None),
        ("textile", "Uy tekstili", "Домашний текстиль", "Home textile", "家纺", None),
        ("decor", "Dekor", "Декор", "Decor", "装饰", None),
        ("appliances", "Maishiy texnika", "Бытовая техника", "Appliances", "家用电器", None),
        ("tools", "Asbob-uskunalar", "Инструменты", "Tools", "工具", None),
        ("garden", "Bog' va hovli", "Сад и двор", "Garden", "花园", None),
    ]),
    ("beauty", "💄", "Go'zallik va salomatlik", "Красота и здоровье", "Beauty & health", "美妆健康", "volume", [
        ("cosmetics", "Kosmetika", "Косметика", "Cosmetics", "化妆品", None),
        ("perfume", "Parfyumeriya", "Парфюмерия", "Perfume", "香水", None),
        ("skincare", "Teri parvarishi", "Уход за кожей", "Skincare", "护肤", None),
        ("hair", "Soch parvarishi", "Уход за волосами", "Hair care", "护发", None),
        ("health", "Salomatlik", "Здоровье", "Health", "健康", "none"),
        ("hygiene", "Gigiyena", "Гигиена", "Hygiene", "个人卫生", "none"),
    ]),
    ("kids", "🧸", "Bolalar dunyosi", "Детский мир", "Kids & baby", "母婴儿童", "none", [
        ("toys", "O'yinchoqlar", "Игрушки", "Toys", "玩具", None),
        ("strollers", "Aravachalar va o'rindiqlar", "Коляски и кресла", "Strollers & seats", "婴儿车座椅", None),
        ("babycare", "Chaqaloq parvarishi", "Уход за малышом", "Baby care", "婴儿护理", None),
        ("school", "Maktab buyumlari", "Школьные товары", "School supplies", "学习用品", None),
    ]),
    ("food", "🍎", "Oziq-ovqat", "Продукты", "Food & drinks", "食品饮料", "weight", [
        ("fruits", "Meva va sabzavot", "Фрукты и овощи", "Fruits & vegetables", "水果蔬菜", None),
        ("sweets", "Shirinliklar", "Сладости", "Sweets", "甜点", None),
        ("drinks", "Ichimliklar", "Напитки", "Drinks", "饮料", "volume"),
        ("meat", "Go'sht va sut mahsulotlari", "Мясо и молочные продукты", "Meat & dairy", "肉类乳制品", None),
        ("grocery", "Bakaleya", "Бакалея", "Grocery", "杂货", None),
    ]),
    ("sport", "⚽", "Sport va dam olish", "Спорт и отдых", "Sports & outdoors", "运动户外", "none", [
        ("fitness", "Fitnes", "Фитнес", "Fitness", "健身", None),
        ("bikes", "Velosipedlar", "Велосипеды", "Bikes", "自行车", None),
        ("outdoor", "Sayohat va kemping", "Туризм и кемпинг", "Camping & hiking", "露营徒步", None),
        ("balls", "To'p o'yinlari", "Игры с мячом", "Ball games", "球类运动", None),
    ]),
    ("auto", "🚗", "Avto", "Авто", "Auto", "汽车用品", "none", [
        ("parts", "Ehtiyot qismlar", "Запчасти", "Parts", "零配件", None),
        ("caracc", "Avto aksessuarlar", "Автоаксессуары", "Car accessories", "汽车配件", None),
        ("oils", "Moy va kimyo", "Масла и автохимия", "Oils & chemicals", "机油化学品", "volume"),
        ("tires", "Shinalar", "Шины", "Tires", "轮胎", None),
    ]),
    ("books", "📚", "Kitob va kanselyariya", "Книги и канцтовары", "Books & stationery", "图书文具", "none", [
        ("books", "Kitoblar", "Книги", "Books", "图书", None),
        ("stationery", "Kanselyariya", "Канцтовары", "Stationery", "文具", None),
        ("office", "Ofis jihozlari", "Офисные товары", "Office supplies", "办公用品", None),
    ]),
    ("other", "🛍️", "Boshqa", "Другое", "Other", "其他", "none", []),
]
_CAT_MAP = {c[0]: c for c in CATEGORIES}


def category_ids():
    return [c[0] for c in CATEGORIES]


def valid_category(cid, sid=""):
    c = _CAT_MAP.get(cid)
    if not c:
        return False
    if sid and sid not in {s[0] for s in c[7]}:
        return False
    return True


def category_name(cid, lang="uz"):
    c = _CAT_MAP.get(cid or "other") or _CAT_MAP["other"]
    return _pick(c[2:6], lang)


def category_icon(cid):
    return (_CAT_MAP.get(cid or "other") or _CAT_MAP["other"])[1]


def sub_name(cid, sid, lang="uz"):
    c = _CAT_MAP.get(cid or "")
    if not c:
        return ""
    for s in c[7]:
        if s[0] == sid:
            return _pick(s[1:5], lang)
    return ""


def size_system_for(cid, sid=""):
    c = _CAT_MAP.get(cid or "")
    if not c:
        return "none"
    for s in c[7]:
        if s[0] == sid and s[5]:
            return s[5]
    return c[6]


def category_list(lang="uz"):
    out = []
    for c in CATEGORIES:
        out.append({
            "id": c[0], "icon": c[1], "name": _pick(c[2:6], lang), "size_system": c[6],
            "subs": [{"id": s[0], "name": _pick(s[1:5], lang), "size_system": s[5] or c[6]} for s in c[7]],
        })
    return out


def clean_colors(tokens):
    out, seen = [], set()
    for t in tokens or []:
        t = (t or "").strip()
        if t in _COLOR_MAP and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def clean_sizes(system, tokens, custom=""):
    """Katalogdagi o'lchamlar (ro'yxat tartibida) + foydalanuvchi qo'shgan ixtiyoriy o'lchamlar."""
    allowed = SIZE_SYSTEMS.get(system, [])
    chosen = [v for v in allowed if v in set(tokens or [])]
    import re
    extra, seen = [], {v.lower() for v in chosen}
    for part in re.split(r"[,;\n]", custom or ""):
        v = part.strip()[:20]
        if v and v.lower() not in seen:
            seen.add(v.lower())
            extra.append(v)
    return (chosen + extra)[:24]


def catalog_payload(lang="uz"):
    """Brauzerdagi mahsulot formasi uchun to'liq katalog."""
    systems = {}
    for key, values in SIZE_SYSTEMS.items():
        systems[key] = {
            "name": size_system_name(key, lang),
            "values": [{"v": v, "label": size_label(v, lang)} for v in values],
        }
    return {"categories": category_list(lang), "colors": color_list(lang), "size_systems": systems}


def display_options(raw, kind, lang="uz"):
    """Bazadagi 'a, b, c' qatorini ko'rsatish uchun: [{value, label, hex}]."""
    import re
    out = []
    for part in re.split(r"[,;\n]", raw or ""):
        v = part.strip()
        if not v:
            continue
        if kind == "color":
            info = color_info(v, lang)
            out.append({"value": v, "label": info["name"] if info else v, "hex": info["hex"] if info else ""})
        else:
            out.append({"value": v, "label": size_label(v, lang), "hex": ""})
    return out

# Linko Kutubxona: boshlang'ich kitoblar (har tilda 6 tadan).
# Hammasi mualliflik huquqidan chiqqan (public domain) asarlar. Matnlar birinchi ishga tushishda
# Project Gutenberg va Wikisource'dan avtomatik yuklab olinadi va bazaga saqlanadi.
# Admin panelda bu kitoblarni tahrirlash, yashirish, o'chirish yoki PDF bilan almashtirish mumkin.

SEED_BOOKS = [
    # ---------------- O'zbek ----------------
    {
        "key": "uz-otkan-kunlar", "lang": "uz", "title": "O'tkan kunlar", "author": "Abdulla Qodiriy",
        "year": "1925", "genre": "novel", "colors": "#7c2d12,#f59e0b", "featured": 1,
        "source": "wikiseries:wikisource.org:O'tkan kunlar",
        "description": "O'zbek adabiyotidagi birinchi roman. Otabek va Kumushning muhabbati, XIX asr Toshkent va "
                       "Marg'ilon hayoti, oila, urf-odat va zamon fojialari haqida.",
    },
    {
        "key": "uz-kecha-va-kunduz", "lang": "uz", "title": "Kecha va kunduz", "author": "Cho'lpon",
        "year": "1936", "genre": "novel", "colors": "#1e1b4b,#6366f1", "featured": 0,
        "source": "wikiseries:wikisource.org:Kecha va kunduz",
        "description": "Cho'lponning mashhur romani. Zebi taqdiri orqali chor Turkistonidagi ayol qismati, "
                       "zulm va jamiyat illatlari ko'rsatiladi.",
    },
    {
        "key": "uz-jinlar-bazmi", "lang": "uz", "title": "Jinlar bazmi", "author": "Abdulla Qodiriy",
        "year": "1926", "genre": "story", "colors": "#14532d,#22c55e", "featured": 0,
        "source": "wiki:wikisource.org:Jinlar bazmi",
        "description": "Abdulla Qodiriyning hajviy hikoyasi: xurofot va bid'atlar ustidan kulgi.",
    },
    {
        "key": "uz-uloqda", "lang": "uz", "title": "Uloqda", "author": "Abdulla Qodiriy",
        "year": "1915", "genre": "story", "colors": "#713f12,#eab308", "featured": 0,
        "source": "wiki:wikisource.org:Uloqda",
        "description": "Yozuvchining ilk hikoyalaridan biri: uloq musobaqasi va o'sha davr odamlari hayotidan lavha.",
    },
    {
        "key": "uz-layli-va-majnun", "lang": "uz", "title": "Layli va Majnun", "author": "Abdulla Qodiriy",
        "year": "", "genre": "story", "colors": "#831843,#ec4899", "featured": 0,
        "source": "wiki:wikisource.org:Layli va Majnun (Abdulla Qodiriy)",
        "description": "Abdulla Qodiriy qalamiga mansub «Layli va Majnun» asari.",
    },
    {
        "key": "uz-tong-sirlari", "lang": "uz", "title": "Tong sirlari", "author": "Cho'lpon",
        "year": "1926", "genre": "poetry", "colors": "#0c4a6e,#38bdf8", "featured": 0,
        "source": "wiki:wikisource.org:«Tong sirlari»",
        "description": "Cho'lponning she'rlar to'plami: vatan, ozodlik va muhabbat haqida nozik lirika.",
    },

    # ---------------- Русский ----------------
    {
        "key": "ru-shinel", "lang": "ru", "title": "Шинель", "author": "Николай Гоголь",
        "year": "1842", "genre": "story", "colors": "#1f2937,#9ca3af", "featured": 1,
        "source": "wiki:ru.wikisource.org:Шинель (Гоголь)",
        "description": "Повесть о маленьком человеке Акакии Акакиевиче Башмачкине и его новой шинели.",
    },
    {
        "key": "ru-mumu", "lang": "ru", "title": "Муму", "author": "Иван Тургенев",
        "year": "1854", "genre": "story", "colors": "#3f6212,#a3e635", "featured": 0,
        "source": "wiki:ru.wikisource.org:Муму (Тургенев)",
        "description": "Рассказ о немом дворнике Герасиме и его собачке Муму.",
    },
    {
        "key": "ru-mtsyri", "lang": "ru", "title": "Мцыри", "author": "Михаил Лермонтов",
        "year": "1839", "genre": "poetry", "colors": "#164e63,#22d3ee", "featured": 0,
        "source": "wiki:ru.wikisource.org:Мцыри (Лермонтов)",
        "description": "Романтическая поэма о юном послушнике, мечтающем о свободе и родине.",
    },
    {
        "key": "ru-stantsionny-smotritel", "lang": "ru", "title": "Станционный смотритель", "author": "Александр Пушкин",
        "year": "1830", "genre": "story", "colors": "#78350f,#fbbf24", "featured": 0,
        "source": "wiki:ru.wikisource.org:Повести покойного Ивана Петровича Белкина (Пушкин)/Станционный смотритель",
        "description": "Одна из «Повестей Белкина»: история смотрителя Самсона Вырина и его дочери Дуни.",
    },
    {
        "key": "ru-belye-nochi", "lang": "ru", "title": "Белые ночи", "author": "Фёдор Достоевский",
        "year": "1848", "genre": "novel", "colors": "#312e81,#a5b4fc", "featured": 0,
        "source": "gutenberg:21183",
        "description": "Сентиментальный роман о мечтателе и Настеньке — четыре петербургские ночи.",
    },
    {
        "key": "ru-zapiski-iz-podpolya", "lang": "ru", "title": "Записки из подполья", "author": "Фёдор Достоевский",
        "year": "1864", "genre": "novel", "colors": "#450a0a,#ef4444", "featured": 0,
        "source": "gutenberg:21186",
        "description": "Исповедь «подпольного человека» — одно из самых глубоких произведений Достоевского.",
    },

    # ---------------- English ----------------
    {
        "key": "en-pride-and-prejudice", "lang": "en", "title": "Pride and Prejudice", "author": "Jane Austen",
        "year": "1813", "genre": "novel", "colors": "#831843,#f9a8d4", "featured": 1,
        "source": "gutenberg:1342",
        "description": "Elizabeth Bennet and Mr. Darcy: a witty classic about love, class and first impressions.",
    },
    {
        "key": "en-alice", "lang": "en", "title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll",
        "year": "1865", "genre": "children", "colors": "#1e3a8a,#60a5fa", "featured": 0,
        "source": "gutenberg:11",
        "description": "Alice falls down a rabbit hole into a world of curious creatures and wonderful nonsense.",
    },
    {
        "key": "en-sherlock-holmes", "lang": "en", "title": "The Adventures of Sherlock Holmes", "author": "Arthur Conan Doyle",
        "year": "1892", "genre": "detective", "colors": "#1c1917,#a8a29e", "featured": 0,
        "source": "gutenberg:1661",
        "description": "Twelve famous cases of the great detective and his friend Dr. Watson.",
    },
    {
        "key": "en-frankenstein", "lang": "en", "title": "Frankenstein", "author": "Mary Shelley",
        "year": "1818", "genre": "novel", "colors": "#052e16,#4ade80", "featured": 0,
        "source": "gutenberg:84",
        "description": "Victor Frankenstein creates life — and must face the consequences.",
    },
    {
        "key": "en-treasure-island", "lang": "en", "title": "Treasure Island", "author": "Robert Louis Stevenson",
        "year": "1883", "genre": "adventure", "colors": "#0c4a6e,#f59e0b", "featured": 0,
        "source": "gutenberg:120",
        "description": "Young Jim Hawkins, a treasure map, and the pirate Long John Silver.",
    },
    {
        "key": "en-romeo-and-juliet", "lang": "en", "title": "Romeo and Juliet", "author": "William Shakespeare",
        "year": "1597", "genre": "drama", "colors": "#7f1d1d,#fb7185", "featured": 0,
        "source": "gutenberg:1513",
        "description": "Shakespeare's tragedy of two young lovers from feuding families in Verona.",
    },

    # ---------------- 中文 ----------------
    {
        "key": "zh-xiyouji", "lang": "zh", "title": "西遊記", "author": "吳承恩",
        "year": "1592", "genre": "novel", "colors": "#7c2d12,#fb923c", "featured": 1,
        "source": "gutenberg:23962",
        "description": "孫悟空保護唐僧西天取經，一路降妖除魔的神話小說。四大名著之一。",
    },
    {
        "key": "zh-sanguo", "lang": "zh", "title": "三國演義", "author": "羅貫中",
        "year": "1522", "genre": "novel", "colors": "#14532d,#86efac", "featured": 0,
        "source": "gutenberg:23950",
        "description": "東漢末年至三國鼎立的歷史演義，劉備、曹操、孫權群雄逐鹿。四大名著之一。",
    },
    {
        "key": "zh-hongloumeng", "lang": "zh", "title": "紅樓夢", "author": "曹雪芹",
        "year": "1791", "genre": "novel", "colors": "#881337,#fda4af", "featured": 0,
        "source": "gutenberg:24264",
        "description": "賈寶玉與林黛玉的愛情，以及賈府由盛轉衰的故事。四大名著之一。",
    },
    {
        "key": "zh-shuihu", "lang": "zh", "title": "水滸傳", "author": "施耐庵",
        "year": "1589", "genre": "novel", "colors": "#1e3a8a,#93c5fd", "featured": 0,
        "source": "gutenberg:23863",
        "description": "一百零八位梁山好漢聚義的英雄傳奇。四大名著之一。",
    },
    {
        "key": "zh-daodejing", "lang": "zh", "title": "道德經", "author": "老子",
        "year": "", "genre": "philosophy", "colors": "#422006,#facc15", "featured": 0,
        "source": "gutenberg:7337",
        "description": "道家經典，五千言論道與德，影響中國思想兩千餘年。",
    },
    {
        "key": "zh-lunyu", "lang": "zh", "title": "論語", "author": "孔子弟子",
        "year": "", "genre": "philosophy", "colors": "#3b0764,#c084fc", "featured": 0,
        "source": "gutenberg:23839",
        "description": "記錄孔子及其弟子言行的儒家經典。",
    },
]

BOOK_GENRES = ("novel", "story", "poetry", "drama", "children", "detective", "adventure", "philosophy",
               "history", "science", "religion", "education", "other")
BOOK_LANGS = ("uz", "ru", "en", "zh")

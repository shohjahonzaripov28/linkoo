/* =====================================================================
   LINKO MAP — kinematik sayohat sahnalari (haqiqiy videolar)
   Videolar: Pexels (bepul litsenziya, tijoratda ham ishlatish mumkin).
   Har bir sahna:
     id      — fayl nomi ham shu (Cloudflare'da: <id>_1280.mp4, <id>_960.mp4, <id>_640.mp4)
     mode    — "scrub": video scroll bilan oldinga/orqaga yuradi
               "play" : video o'zi aylanib o'ynaydi, scroll matnni boshqaradi
     len     — sahna uzunligi (necha ekran balandligi scroll)
     from/to — videoning qaysi qismi ishlatiladi (sekund)
     hud     — ekrandagi asbob ko'rsatkichlari (tezlik, balandlik)
     pexels  — manba fayllar (1280 = kuchli kompyuter, 960 = noutbuk, 640 = telefon / sekin internet)
   ===================================================================== */
window.LINKO_STORY = [
  {
    id: "takeoff", mode: "scrub", len: 3.2, from: 0, to: 17, hud: "takeoff",
    pexels: { 640: "9512135/9512135-sd_640_360_25fps.mp4", 1280: "9512135/9512135-hd_1280_720_25fps.mp4", 960: "9512135/9512135-sd_960_540_25fps.mp4" },
    poster: "https://images.pexels.com/videos/9512135/airplane-airport-airstrip-runway-9512135.jpeg",
    tag: "LINKO AIRLINES · FLIGHT LK-001",
    title: { uz: "Uchishga tayyormisiz?", en: "Ready for takeoff?", ru: "Готовы к взлёту?", zh: "准备起飞了吗？" },
    text: {
      uz: "Kamarlarni taqing. Pastga aylantiring: samolyot yo'lak bo'ylab tezlashadi va asta havoga ko'tariladi.",
      en: "Fasten your seatbelt. Scroll down: the plane speeds up along the runway and slowly lifts into the air.",
      ru: "Пристегните ремни. Прокручивайте вниз: самолёт разгоняется по полосе и плавно поднимается в воздух.",
      zh: "请系好安全带。向下滚动：飞机沿跑道加速，缓缓升空。"
    }
  },
  {
    id: "climb", mode: "scrub", len: 2.2, from: 4, to: 30, hud: "climb",
    pexels: { 640: "4396425/4396425-sd_640_360_30fps.mp4", 1280: "4396425/4396425-sd_960_540_30fps.mp4", 960: "4396425/4396425-sd_640_360_30fps.mp4" },
    poster: "https://images.pexels.com/videos/4396425/airplane-airplane-take-off-airplane-window-airplane-wing-4396425.jpeg",
    tag: "CLIMB · 1 500 → 10 000 FT",
    title: { uz: "Ko'tarilish", en: "Climbing", ru: "Набор высоты", zh: "爬升" },
    text: {
      uz: "Yer pastda sekin kichrayib bormoqda. Bir necha daqiqadan keyin bulutlar ustidamiz.",
      en: "The ground slowly shrinks below. In a few minutes we will be above the clouds.",
      ru: "Земля внизу медленно уменьшается. Через несколько минут мы будем над облаками.",
      zh: "地面在下方慢慢变小。几分钟后，我们将飞到云层之上。"
    }
  },
  {
    id: "clouds", mode: "play", len: 1.4, from: 0, to: 19, hud: "cruise",
    pexels: { 640: "12278380/12278380-sd_360_640_30fps.mp4", 1280: "12278380/12278380-hd_720_1280_60fps.mp4", 960: "12278380/12278380-sd_540_960_30fps.mp4" },
    poster: "https://images.pexels.com/videos/12278380/pexels-photo-12278380.jpeg",
    tag: "CRUISE · 35 000 FT",
    title: { uz: "Bulutlar ustida", en: "Above the clouds", ru: "Над облаками", zh: "云层之上" },
    text: {
      uz: "Yo'lovchi samolyotlari odatda 10–12 km balandlikda uchadi. Bu Everest cho'qqisidan ham baland.",
      en: "Airliners usually cruise 10–12 km up. That is higher than the summit of Everest.",
      ru: "Пассажирские самолёты обычно летят на высоте 10–12 км. Это выше вершины Эвереста.",
      zh: "客机通常在10至12公里的高度巡航，比珠穆朗玛峰还要高。"
    }
  },
  {
    id: "everest", mode: "play", len: 1.6, from: 0, to: 12,
    pexels: { 640: "29632834/12750572_640_360_25fps.mp4", 1280: "29632834/12750574_1280_720_25fps.mp4", 960: "29632834/12750573_960_540_25fps.mp4" },
    poster: "https://images.pexels.com/videos/29632834/above-the-himalaya-abstract-clouds-amadablam-climate-change-29632834.jpeg",
    tag: "NEPAL · CHINA", stat: "8 849 m",
    title: { uz: "Everest", en: "Mount Everest", ru: "Эверест", zh: "珠穆朗玛峰" },
    text: {
      uz: "Yer yuzidagi eng baland nuqta. Cho'qqiga birinchi bo'lib 1953-yilda Edmund Xillari va Tenzing Norgey chiqqan.",
      en: "The highest point on Earth. Edmund Hillary and Tenzing Norgay first reached the summit in 1953.",
      ru: "Самая высокая точка Земли. Первыми на вершину в 1953 году поднялись Эдмунд Хиллари и Тенцинг Норгей.",
      zh: "地球最高点。1953年，埃德蒙·希拉里和丹增·诺尔盖首次登顶。"
    }
  },
  {
    id: "ocean", mode: "play", len: 1.4, from: 0, to: 20,
    pexels: { 640: "26893767/12028834_640_360_24fps.mp4", 1280: "26893767/12028836_960_540_24fps.mp4", 960: "26893767/12028834_640_360_24fps.mp4" },
    poster: "https://images.pexels.com/videos/26893767/pexels-photo-26893767.jpeg",
    tag: "OCEAN ROUTES", stat: "~80%",
    title: { uz: "Okean yo'llari", en: "Ocean highways", ru: "Океанские пути", zh: "海上航线" },
    text: {
      uz: "Dunyo savdosidagi yuklarning taxminan 80 foizi dengiz orqali, mana shunday ulkan kemalarda tashiladi.",
      en: "About 80% of the world's trade by volume travels by sea, on giant ships like this one.",
      ru: "Около 80% мировой торговли по объёму перевозится морем, на таких огромных судах.",
      zh: "全球约80%的贸易货物通过海运完成，靠的就是这样的巨轮。"
    }
  },
  {
    id: "dubai", mode: "play", len: 1.4, from: 0, to: 30,
    pexels: { 640: "10518495/10518495-sd_640_360_25fps.mp4", 1280: "10518495/10518495-sd_960_540_25fps.mp4", 960: "10518495/10518495-sd_640_360_25fps.mp4" },
    poster: "https://images.pexels.com/videos/10518495/aerial-footage-drone-dubai-dubai-marina-10518495.jpeg",
    tag: "UAE", stat: "828 m",
    title: { uz: "Dubay", en: "Dubai", ru: "Дубай", zh: "迪拜" },
    text: {
      uz: "Cho'l ustida qurilgan osmono'par binolar shahri. Dunyodagi eng baland bino, 828 metrlik Burj Xalifa ham shu yerda.",
      en: "A city of skyscrapers built on the desert. The world's tallest building, the 828-metre Burj Khalifa, is here.",
      ru: "Город небоскрёбов посреди пустыни. Здесь стоит самое высокое здание мира — 828-метровый Бурдж-Халифа.",
      zh: "建在沙漠上的摩天大楼之城，世界最高建筑、高828米的哈利法塔就在这里。"
    }
  },
  {
    id: "pyramids", mode: "play", len: 1.4, from: 0, to: 21,
    pexels: { 640: "32537704/13876130_640_360_24fps.mp4", 1280: "32537704/13876133_1280_720_24fps.mp4", 960: "32537704/13876132_960_540_24fps.mp4" },
    poster: "https://images.pexels.com/videos/32537704/pexels-photo-32537704.jpeg",
    tag: "EGYPT · GIZA", stat: "~4 500",
    title: { uz: "Giza ehromlari", en: "Pyramids of Giza", ru: "Пирамиды Гизы", zh: "吉萨金字塔" },
    text: {
      uz: "Buyuk ehromning yoshi taxminan 4 500 yil. U 3 800 yil davomida dunyodagi eng baland inshoot bo'lgan.",
      en: "The Great Pyramid is about 4,500 years old. For 3,800 years it was the tallest structure on Earth.",
      ru: "Великой пирамиде около 4 500 лет. 3 800 лет она была самым высоким сооружением на Земле.",
      zh: "大金字塔约有4500年历史，曾在3800年间保持世界最高建筑的纪录。"
    }
  },
  {
    id: "newyork", mode: "play", len: 1.4, from: 0, to: 8.5,
    pexels: { 640: "36244245/15370500_640_360_30fps.mp4", 1280: "36244245/15370507_1280_720_30fps.mp4", 960: "36244245/15370503_960_540_30fps.mp4" },
    poster: "https://images.pexels.com/videos/36244245/pexels-photo-36244245.jpeg",
    tag: "USA · MANHATTAN", stat: "NYC",
    title: { uz: "Nyu-York", en: "New York", ru: "Нью-Йорк", zh: "纽约" },
    text: {
      uz: "Dunyoning eng mashhur osmono'par binolar oroli Manxetten. Kechqurun minglab derazalar birdaniga yonadi.",
      en: "Manhattan, the world's most famous island of skyscrapers. At dusk thousands of windows light up at once.",
      ru: "Манхэттен — самый известный остров небоскрёбов. В сумерках одновременно загораются тысячи окон.",
      zh: "曼哈顿是世界上最著名的摩天大楼之岛，黄昏时成千上万扇窗户同时亮起。"
    }
  },
  {
    id: "greatwall", mode: "scrub", len: 2.8, from: 0, to: 25,
    pexels: { 640: "30897424/13209582_640_360_60fps.mp4", 1280: "30897424/13209584_1280_720_60fps.mp4", 960: "30897424/13209583_960_540_60fps.mp4" },
    poster: "https://images.pexels.com/videos/30897424/above-aerial-ancient-architecture-30897424.jpeg",
    tag: "CHINA · 中国", stat: "21 196 km",
    title: { uz: "Buyuk Xitoy devori", en: "The Great Wall of China", ru: "Великая Китайская стена", zh: "万里长城" },
    text: {
      uz: "Dron devor bo'ylab uchmoqda: scroll qilsangiz, oldinga uchadi. Barcha qismlari jamlansa, devor uzunligi 21 000 km dan oshadi.",
      en: "A drone is flying along the wall: scroll and it flies forward. All sections together run more than 21,000 km.",
      ru: "Дрон летит вдоль стены: прокручивайте, и он полетит вперёд. Общая длина всех участков — более 21 000 км.",
      zh: "无人机正沿着长城飞行：向下滚动，它就向前飞。长城各段总长超过2.1万公里。"
    }
  },
  {
    id: "shanghai", mode: "play", len: 1.4, from: 0, to: 25,
    pexels: { 640: "39410944/16781499_640_360_25fps.mp4", 1280: "39410944/16781502_1280_720_25fps.mp4", 960: "39410944/16781500_960_540_25fps.mp4" },
    poster: "https://images.pexels.com/videos/39410944/china-tourism-china-travel-vlog-lujiazui-shanghai-pudong-shanghai-39410944.jpeg",
    tag: "CHINA · 上海", stat: "632 m",
    title: { uz: "Shanxay", en: "Shanghai", ru: "Шанхай", zh: "上海" },
    text: {
      uz: "Xitoyning moliya poytaxti. Lujiatszuy tumanidagi Shanxay minorasining balandligi 632 metr, bu Xitoydagi eng baland bino.",
      en: "China's financial capital. The Shanghai Tower in Lujiazui rises 632 metres, the tallest building in China.",
      ru: "Финансовая столица Китая. Шанхайская башня в районе Луцзяцзуй высотой 632 метра — самое высокое здание страны.",
      zh: "中国的金融之都。陆家嘴的上海中心大厦高632米，是中国第一高楼。"
    }
  },
  {
    id: "hongkong", mode: "play", len: 1.4, from: 0, to: 25,
    pexels: { 640: "37760048/16016725_640_360_25fps.mp4", 1280: "37760048/16016728_1280_720_25fps.mp4", 960: "37760048/16016727_960_540_25fps.mp4" },
    poster: "https://images.pexels.com/videos/37760048/aerial-city-drone-hong-kong-37760048.jpeg",
    tag: "CHINA · 香港", stat: "HK",
    title: { uz: "Gonkong", en: "Hong Kong", ru: "Гонконг", zh: "香港" },
    text: {
      uz: "Tog'lar va dengiz orasiga qisilgan shahar. Kechasi Viktoriya ko'rfazi bo'ylab binolar chiroqlar shousini boshlaydi.",
      en: "A city squeezed between mountains and the sea. At night the buildings along Victoria Harbour put on a light show.",
      ru: "Город, зажатый между горами и морем. Ночью здания вдоль бухты Виктория устраивают световое шоу.",
      zh: "夹在群山与大海之间的城市。夜晚，维多利亚港两岸的建筑会上演灯光秀。"
    }
  },
  {
    id: "space", mode: "play", len: 1.8, from: 0, to: 8.2, hud: "space",
    pexels: { 640: "33430410/14227680_640_360_30fps.mp4", 1280: "33430410/14227688_1280_720_30fps.mp4", 960: "33430410/14227686_960_540_30fps.mp4" },
    poster: "https://images.pexels.com/videos/33430410/pexels-photo-33430410.jpeg",
    tag: "ORBIT · 400 KM", stat: "71%",
    title: { uz: "Kosmosdan Yer", en: "Earth from space", ru: "Земля из космоса", zh: "从太空看地球" },
    text: {
      uz: "Biz shunchalik baland ko'tarildikki, endi butun sayyora ko'rinadi. Yer yuzasining 71 foizi suv bilan qoplangan.",
      en: "We have climbed so high that the whole planet is in view. 71% of the Earth's surface is covered by water.",
      ru: "Мы поднялись так высоко, что видна вся планета. 71% поверхности Земли покрыто водой.",
      zh: "我们已经飞得足够高，可以看到整个星球。地球表面71%被水覆盖。"
    }
  }
];

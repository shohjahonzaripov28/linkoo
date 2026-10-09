/* =====================================================================
   LINKO MAP — 3D sayohat bekatlari
   Har bir bekat: koordinata, kamera burchagi va 4 tildagi matn (uz, en, ru, zh).
   Yangi joy qo'shish uchun shu ro'yxatga yana bitta { ... } qo'shing.
     lat/lon  — kenglik / uzunlik
     zoom     — yaqinlik (2 = butun Yer, 16 = bino)
     pitch    — kamera qiyaligi (0 = tepadan, 75 = deyarli gorizontal)
     bearing  — kamera yo'nalishi (gradus)
     planes   — shu yerda jonli samolyotlarni ko'rsatish
     space    — kosmos rejimi (Yer shari, sun'iy yo'ldoshlar, XKS)
   ===================================================================== */
window.LINKO_TOUR = [
  {
    id: "everest", icon: "🏔️", lat: 27.9881, lon: 86.925, zoom: 12.2, pitch: 72, bearing: 200, stat: "8 849 m",
    name: { uz: "Everest cho'qqisi", en: "Mount Everest", ru: "Эверест", zh: "珠穆朗玛峰" },
    text: {
      uz: "Yer yuzidagi eng baland nuqta. Nepal va Xitoy chegarasida joylashgan. Cho'qqiga birinchi bo'lib 1953-yilda Edmund Xillari va Tenzing Norgey chiqqan.",
      en: "The highest point on Earth, on the border of Nepal and China. Edmund Hillary and Tenzing Norgay were the first to reach the summit in 1953.",
      ru: "Самая высокая точка Земли на границе Непала и Китая. Первыми на вершину в 1953 году поднялись Эдмунд Хиллари и Тенцинг Норгей.",
      zh: "地球最高点，位于尼泊尔与中国边境。1953年，埃德蒙·希拉里和丹增·诺尔盖首次登顶。"
    }
  },
  {
    id: "himalaya", icon: "⛰️", lat: 28.05, lon: 86.62, zoom: 9.2, pitch: 65, bearing: 120, stat: "2 400 km",
    name: { uz: "Himolay tog'lari", en: "The Himalayas", ru: "Гималаи", zh: "喜马拉雅山脉" },
    text: {
      uz: "Taxminan 2 400 km cho'zilgan tog' tizmasi. Dunyodagi balandligi 8 000 metrdan oshadigan 14 ta cho'qqining 10 tasi shu yerda.",
      en: "A mountain range about 2,400 km long. Ten of the world's fourteen peaks above 8,000 metres are here.",
      ru: "Горная система длиной около 2 400 км. Здесь находятся 10 из 14 вершин мира выше 8 000 метров.",
      zh: "绵延约2400公里的山脉。世界上14座海拔8000米以上的高峰中有10座在这里。"
    }
  },
  {
    id: "maldives", icon: "🏝️", lat: 4.17, lon: 73.5, zoom: 10.3, pitch: 50, bearing: 0, stat: "~1 190",
    name: { uz: "Maldiv orollari", en: "Maldives", ru: "Мальдивы", zh: "马尔代夫" },
    text: {
      uz: "Hind okeanidagi 1 190 ga yaqin marjon oroli. Dunyodagi eng past davlat: o'rtacha balandligi dengiz sathidan atigi 1,5 metr.",
      en: "Around 1,190 coral islands in the Indian Ocean. The lowest country on Earth, averaging only about 1.5 metres above sea level.",
      ru: "Около 1 190 коралловых островов в Индийском океане. Самая низкая страна мира: в среднем всего 1,5 метра над уровнем моря.",
      zh: "印度洋上约1190个珊瑚岛。世界上地势最低的国家，平均海拔仅约1.5米。"
    }
  },
  {
    id: "singapore-port", icon: "🚢", lat: 1.255, lon: 103.79, zoom: 12.3, pitch: 60, bearing: 30, stat: "PORT",
    name: { uz: "Singapur porti", en: "Port of Singapore", ru: "Порт Сингапура", zh: "新加坡港" },
    text: {
      uz: "Dunyodagi eng gavjum portlardan biri. Malakka bo'g'ozida joylashgan, har kuni yuzlab yuk kemalari shu yerdan o'tadi.",
      en: "One of the busiest ports in the world. It sits on the Strait of Malacca, where hundreds of cargo ships pass every day.",
      ru: "Один из самых загруженных портов мира. Находится у Малаккского пролива, через который ежедневно проходят сотни судов.",
      zh: "世界上最繁忙的港口之一，位于马六甲海峡，每天有数百艘货船经过。"
    }
  },
  {
    id: "changi", icon: "✈️", lat: 1.3644, lon: 103.9915, zoom: 12.6, pitch: 55, bearing: 310, planes: true, stat: "SIN",
    name: { uz: "Changi aeroporti", en: "Changi Airport", ru: "Аэропорт Чанги", zh: "樟宜机场" },
    text: {
      uz: "Ko'p yillar dunyoning eng yaxshi aeroporti deb tan olingan. Ichida 40 metrlik yopiq sharshara bor. Hozir ekranda jonli samolyotlar ko'rinmoqda.",
      en: "Voted the world's best airport many times, with a 40-metre indoor waterfall. The planes you see now are live.",
      ru: "Много раз признавался лучшим аэропортом мира, внутри есть 40-метровый водопад. Самолёты на экране — в реальном времени.",
      zh: "多次被评为世界最佳机场，内有40米高的室内瀑布。屏幕上的飞机是实时数据。"
    }
  },
  {
    id: "burj", icon: "🏙️", lat: 25.1972, lon: 55.2744, zoom: 15.6, pitch: 70, bearing: 140, stat: "828 m",
    name: { uz: "Burj Xalifa, Dubay", en: "Burj Khalifa, Dubai", ru: "Бурдж-Халифа, Дубай", zh: "迪拜哈利法塔" },
    text: {
      uz: "Dunyodagi eng baland bino: 828 metr va 163 qavat. 2010-yilda ochilgan.",
      en: "The tallest building in the world: 828 metres and 163 floors. It opened in 2010.",
      ru: "Самое высокое здание в мире: 828 метров и 163 этажа. Открыто в 2010 году.",
      zh: "世界最高建筑：高828米，共163层，2010年落成。"
    }
  },
  {
    id: "dxb", icon: "✈️", lat: 25.2532, lon: 55.3657, zoom: 12.4, pitch: 55, bearing: 300, planes: true, stat: "DXB",
    name: { uz: "Dubay xalqaro aeroporti", en: "Dubai International Airport", ru: "Аэропорт Дубая", zh: "迪拜国际机场" },
    text: {
      uz: "Xalqaro yo'lovchilar soni bo'yicha dunyodagi eng gavjum aeroport. Samolyotlar jonli ko'rsatilmoqda.",
      en: "The world's busiest airport for international passengers. The planes are shown live.",
      ru: "Самый загруженный аэропорт мира по числу международных пассажиров. Самолёты показаны в реальном времени.",
      zh: "国际旅客吞吐量全球第一的机场。飞机为实时显示。"
    }
  },
  {
    id: "suez", icon: "⚓", lat: 30.6, lon: 32.33, zoom: 10.2, pitch: 55, bearing: 0, stat: "193 km",
    name: { uz: "Suvaysh kanali", en: "Suez Canal", ru: "Суэцкий канал", zh: "苏伊士运河" },
    text: {
      uz: "O'rta yer dengizini Qizil dengiz bilan bog'laydi. 1869-yilda ochilgan, kemalar Afrikani aylanib o'tmasdan Osiyo va Yevropa orasida suzadi.",
      en: "It links the Mediterranean with the Red Sea. Opened in 1869, it lets ships sail between Asia and Europe without going around Africa.",
      ru: "Соединяет Средиземное и Красное моря. Открыт в 1869 году, позволяет судам ходить между Азией и Европой, не огибая Африку.",
      zh: "连接地中海与红海，1869年通航，使船只无需绕行非洲即可往返亚欧。"
    }
  },
  {
    id: "giza", icon: "🔺", lat: 29.9792, lon: 31.1342, zoom: 15.3, pitch: 62, bearing: 220, stat: "~4 500",
    name: { uz: "Giza ehromlari", en: "Pyramids of Giza", ru: "Пирамиды Гизы", zh: "吉萨金字塔" },
    text: {
      uz: "Buyuk ehromning yoshi taxminan 4 500 yil. Dastlabki balandligi 146 metr bo'lgan va 3 800 yil davomida dunyodagi eng baland inshoot bo'lib qolgan.",
      en: "The Great Pyramid is about 4,500 years old. Originally 146 metres tall, it was the tallest structure on Earth for about 3,800 years.",
      ru: "Великой пирамиде около 4 500 лет. Изначально её высота была 146 метров, и около 3 800 лет она оставалась самым высоким сооружением.",
      zh: "大金字塔约有4500年历史，原高146米，约3800年间一直是世界最高建筑。"
    }
  },
  {
    id: "matterhorn", icon: "🗻", lat: 45.9763, lon: 7.6586, zoom: 12.6, pitch: 74, bearing: 250, stat: "4 478 m",
    name: { uz: "Matterxorn, Alp tog'lari", en: "Matterhorn, the Alps", ru: "Маттерхорн, Альпы", zh: "阿尔卑斯山马特洪峰" },
    text: {
      uz: "Shveysariya va Italiya chegarasidagi piramida shaklidagi mashhur cho'qqi. Balandligi 4 478 metr.",
      en: "A famous pyramid-shaped peak on the border of Switzerland and Italy, 4,478 metres high.",
      ru: "Знаменитая вершина в форме пирамиды на границе Швейцарии и Италии высотой 4 478 метров.",
      zh: "位于瑞士和意大利边境的著名金字塔形山峰，海拔4478米。"
    }
  },
  {
    id: "geiranger", icon: "🌊", lat: 62.105, lon: 7.07, zoom: 11.6, pitch: 70, bearing: 280, stat: "UNESCO",
    name: { uz: "Geyranger fyordi, Norvegiya", en: "Geirangerfjord, Norway", ru: "Гейрангер-фьорд, Норвегия", zh: "挪威盖朗厄尔峡湾" },
    text: {
      uz: "Muzliklar o'yib yasagan tor dengiz qo'ltig'i, atrofi tik qoyalar va sharsharalar. YuNESKO merosi ro'yxatiga kiritilgan.",
      en: "A narrow sea inlet carved by glaciers, framed by steep cliffs and waterfalls. It is a UNESCO World Heritage site.",
      ru: "Узкий морской залив, выточенный ледниками, с отвесными скалами и водопадами. Объект Всемирного наследия ЮНЕСКО.",
      zh: "由冰川雕刻而成的狭长海湾，两侧是陡峭的悬崖和瀑布，已列入联合国教科文组织世界遗产。"
    }
  },
  {
    id: "manhattan", icon: "🗽", lat: 40.7484, lon: -73.9857, zoom: 14.4, pitch: 65, bearing: 30, stat: "NYC",
    name: { uz: "Manxetten, Nyu-York", en: "Manhattan, New York", ru: "Манхэттен, Нью-Йорк", zh: "纽约曼哈顿" },
    text: {
      uz: "Dunyoning eng mashhur osmono'par binolar oroli. Markazdagi Empire State Building 1931-yilda qurilgan.",
      en: "The world's most famous island of skyscrapers. The Empire State Building in the middle was completed in 1931.",
      ru: "Самый известный в мире остров небоскрёбов. Эмпайр-стейт-билдинг в центре построен в 1931 году.",
      zh: "世界上最著名的摩天大楼之岛，中间的帝国大厦建成于1931年。"
    }
  },
  {
    id: "jfk", icon: "✈️", lat: 40.6413, lon: -73.7781, zoom: 12.4, pitch: 55, bearing: 30, planes: true, stat: "JFK",
    name: { uz: "JFK aeroporti", en: "JFK Airport", ru: "Аэропорт JFK", zh: "肯尼迪国际机场" },
    text: {
      uz: "Nyu-Yorkning asosiy xalqaro aeroporti. Okean ustidan qo'nayotgan samolyotlar jonli ko'rinmoqda.",
      en: "New York's main international airport. Watch the live planes landing over the ocean.",
      ru: "Главный международный аэропорт Нью-Йорка. Самолёты, заходящие на посадку над океаном, показаны вживую.",
      zh: "纽约主要的国际机场。可以实时看到飞越海面降落的飞机。"
    }
  },
  {
    id: "grand-canyon", icon: "🏜️", lat: 36.1069, lon: -112.1129, zoom: 11.8, pitch: 70, bearing: 20, stat: "1 800 m",
    name: { uz: "Katta Kanyon", en: "Grand Canyon", ru: "Гранд-Каньон", zh: "科罗拉多大峡谷" },
    text: {
      uz: "Kolorado daryosi millionlab yillar davomida o'yib yasagan kanyon. Uzunligi 446 km, chuqurligi 1 800 metrdan oshadi.",
      en: "Carved by the Colorado River over millions of years. It is 446 km long and more than 1,800 metres deep.",
      ru: "Выточен рекой Колорадо за миллионы лет. Длина 446 км, глубина более 1 800 метров.",
      zh: "由科罗拉多河历经数百万年冲刷而成，长446公里，深逾1800米。"
    }
  },
  {
    id: "kilauea", icon: "🌋", lat: 19.4069, lon: -155.2834, zoom: 11.6, pitch: 60, bearing: 330, stat: "1 247 m",
    name: { uz: "Kilauea vulqoni, Gavayi", en: "Kilauea, Hawaii", ru: "Вулкан Килауэа, Гавайи", zh: "夏威夷基拉韦厄火山" },
    text: {
      uz: "Dunyodagi eng faol vulqonlardan biri. Uning lavasi Gavayi orolini hanuzgacha kattalashtirib bormoqda.",
      en: "One of the most active volcanoes on Earth. Its lava is still making the island of Hawaii bigger.",
      ru: "Один из самых активных вулканов Земли. Его лава до сих пор увеличивает остров Гавайи.",
      zh: "世界上最活跃的火山之一，它的熔岩至今仍在使夏威夷岛不断扩大。"
    }
  },
  {
    id: "mariana", icon: "🌊", lat: 11.35, lon: 142.2, zoom: 6.6, pitch: 55, bearing: 340, stat: "−10 935 m",
    name: { uz: "Mariana botig'i", en: "Mariana Trench", ru: "Марианская впадина", zh: "马里亚纳海沟" },
    text: {
      uz: "Okeanning eng chuqur joyi: deyarli 11 km. Everestni bu yerga qo'ysangiz ham, cho'qqisi suv ostida 2 km chuqurlikda qoladi.",
      en: "The deepest point of the ocean, almost 11 km down. If you dropped Everest here, its summit would still be 2 km under water.",
      ru: "Самая глубокая точка океана, почти 11 км. Если опустить сюда Эверест, его вершина окажется на 2 км под водой.",
      zh: "海洋最深处，深近11公里。即使把珠穆朗玛峰放进去，峰顶仍在水下2公里。"
    }
  },
  {
    id: "great-wall", icon: "🧱", lat: 40.4319, lon: 116.5704, zoom: 14.2, pitch: 68, bearing: 300, stat: "21 196 km",
    name: { uz: "Buyuk Xitoy devori", en: "Great Wall of China", ru: "Великая Китайская стена", zh: "长城（慕田峪）" },
    text: {
      uz: "Barcha qismlari jamlansa uzunligi 21 000 km dan oshadi. Bu Mutianyu qismi, tog' tizmalari bo'ylab ilondek cho'zilgan.",
      en: "All its sections together run more than 21,000 km. This is the Mutianyu section, winding along the mountain ridges.",
      ru: "Общая длина всех участков превышает 21 000 км. Это участок Мутяньюй, извивающийся по горным хребтам.",
      zh: "长城各段总长超过2.1万公里。这里是慕田峪段，沿山脊蜿蜒起伏。"
    }
  },
  {
    id: "forbidden-city", icon: "🏯", lat: 39.9163, lon: 116.3972, zoom: 15.4, pitch: 55, bearing: 0, stat: "1420",
    name: { uz: "Taqiqlangan shahar, Pekin", en: "Forbidden City, Beijing", ru: "Запретный город, Пекин", zh: "北京故宫" },
    text: {
      uz: "1420-yilda qurib bitkazilgan imperator saroyi. Min va Sin sulolalarining 24 ta imperatori shu yerda yashagan.",
      en: "The imperial palace completed in 1420. Twenty-four emperors of the Ming and Qing dynasties lived here.",
      ru: "Императорский дворец, построенный к 1420 году. Здесь жили 24 императора династий Мин и Цин.",
      zh: "建成于1420年的皇宫，明清两代共有24位皇帝在此居住。"
    }
  },
  {
    id: "daxing", icon: "✈️", lat: 39.5098, lon: 116.4105, zoom: 12.8, pitch: 50, bearing: 0, planes: true, stat: "PKX",
    name: { uz: "Pekin Daxing aeroporti", en: "Beijing Daxing Airport", ru: "Аэропорт Пекин-Дасин", zh: "北京大兴国际机场" },
    text: {
      uz: "2019-yilda ochilgan, dengiz yulduzi shaklidagi ulkan terminal. Uni mashhur me'mor Zaha Hadid loyihalagan.",
      en: "Opened in 2019, its giant terminal is shaped like a starfish. It was designed by the famous architect Zaha Hadid.",
      ru: "Открыт в 2019 году, огромный терминал в форме морской звезды спроектировала архитектор Заха Хадид.",
      zh: "2019年启用，巨大的航站楼形似海星，由著名建筑师扎哈·哈迪德设计。"
    }
  },
  {
    id: "shanghai", icon: "🌃", lat: 31.2355, lon: 121.5055, zoom: 14.6, pitch: 66, bearing: 250, stat: "632 m",
    name: { uz: "Shanxay, Lujiatszuy", en: "Shanghai, Lujiazui", ru: "Шанхай, Луцзяцзуй", zh: "上海陆家嘴" },
    text: {
      uz: "Xitoyning moliya markazi. Shanxay minorasining balandligi 632 metr, bu Xitoydagi eng baland bino.",
      en: "China's financial centre. The Shanghai Tower rises 632 metres, the tallest building in China.",
      ru: "Финансовый центр Китая. Высота Шанхайской башни 632 метра — это самое высокое здание Китая.",
      zh: "中国的金融中心。上海中心大厦高632米，是中国第一高楼。"
    }
  },
  {
    id: "yangshan", icon: "🚢", lat: 30.62, lon: 122.07, zoom: 12.2, pitch: 55, bearing: 40, stat: "PORT",
    name: { uz: "Shanxay porti (Yanshan)", en: "Port of Shanghai (Yangshan)", ru: "Порт Шанхая (Яншань)", zh: "上海港洋山深水港" },
    text: {
      uz: "Konteyner aylanmasi bo'yicha dunyodagi eng gavjum port. Yanshan terminali dengiz ichidagi orollarda qurilgan va avtomatlashtirilgan.",
      en: "The world's busiest container port. The Yangshan terminal is built on islands out at sea and is highly automated.",
      ru: "Самый загруженный контейнерный порт мира. Терминал Яншань построен на островах в море и почти полностью автоматизирован.",
      zh: "全球集装箱吞吐量最大的港口。洋山港建在海上岛屿，是高度自动化的码头。"
    }
  },
  {
    id: "zhangjiajie", icon: "🌄", lat: 29.3249, lon: 110.4343, zoom: 13.4, pitch: 74, bearing: 160, stat: "3 000+",
    name: { uz: "Chjanszyatszye", en: "Zhangjiajie", ru: "Чжанцзяцзе", zh: "张家界" },
    text: {
      uz: "3 000 dan ortiq qumtosh ustunlari bor tog'lar. Ular \"Avatar\" filmidagi uchib yuruvchi tog'larga ilhom bergan.",
      en: "Mountains with more than 3,000 sandstone pillars. They inspired the floating mountains in the film Avatar.",
      ru: "Горы с более чем 3 000 песчаниковых столбов. Они вдохновили создателей летающих гор в фильме «Аватар».",
      zh: "拥有3000多座石英砂岩峰柱，是电影《阿凡达》中悬浮山的灵感来源。"
    }
  },
  {
    id: "hongkong", icon: "🌉", lat: 22.2855, lon: 114.1577, zoom: 13.6, pitch: 62, bearing: 330, stat: "HK",
    name: { uz: "Gonkong, Viktoriya ko'rfazi", en: "Hong Kong, Victoria Harbour", ru: "Гонконг, бухта Виктория", zh: "香港维多利亚港" },
    text: {
      uz: "Tog'lar va osmono'par binolar orasidagi mashhur ko'rfaz. Har kecha binolarda chiroqlar shousi bo'ladi.",
      en: "A famous harbour between mountains and skyscrapers. Every night the buildings put on a light show.",
      ru: "Знаменитая бухта между горами и небоскрёбами. Каждый вечер здания устраивают световое шоу.",
      zh: "群山与摩天大楼环绕的著名海港，每晚都有灯光秀。"
    }
  },
  {
    id: "chimgan", icon: "🏔️", lat: 41.55, lon: 70.03, zoom: 12.3, pitch: 70, bearing: 40, stat: "3 309 m",
    name: { uz: "Katta Chimyon", en: "Greater Chimgan", ru: "Большой Чимган", zh: "大奇姆干山" },
    text: {
      uz: "Toshkentdan 80 km uzoqlikdagi tog'. Qishda chang'i, yozda sayohatchilar uchun sevimli joy.",
      en: "A mountain about 80 km from Tashkent, loved by skiers in winter and hikers in summer.",
      ru: "Гора примерно в 80 км от Ташкента. Зимой здесь катаются на лыжах, летом ходят в походы.",
      zh: "距塔什干约80公里的山峰，冬季滑雪、夏季徒步的热门去处。"
    }
  },
  {
    id: "tashkent-airport", icon: "✈️", lat: 41.2579, lon: 69.2812, zoom: 12.6, pitch: 55, bearing: 80, planes: true, stat: "TAS",
    name: { uz: "Toshkent xalqaro aeroporti", en: "Tashkent International Airport", ru: "Аэропорт Ташкент", zh: "塔什干国际机场" },
    text: {
      uz: "O'zbekistonning eng katta aeroporti. Ekranda hozir uchayotgan samolyotlar jonli ko'rinmoqda.",
      en: "Uzbekistan's largest airport. The planes on screen are flying right now.",
      ru: "Крупнейший аэропорт Узбекистана. Самолёты на экране летят прямо сейчас.",
      zh: "乌兹别克斯坦最大的机场。屏幕上的飞机正在实时飞行。"
    }
  },
  {
    id: "tashkent-tower", icon: "🗼", lat: 41.3456, lon: 69.2846, zoom: 15.5, pitch: 66, bearing: 200, stat: "375 m",
    name: { uz: "Toshkent teleminorasi", en: "Tashkent TV Tower", ru: "Ташкентская телебашня", zh: "塔什干电视塔" },
    text: {
      uz: "Balandligi 375 metr, 1985-yilda qurilgan. Markaziy Osiyodagi eng baland inshoot.",
      en: "375 metres tall and built in 1985, it is the tallest structure in Central Asia.",
      ru: "Высота 375 метров, построена в 1985 году. Самое высокое сооружение Центральной Азии.",
      zh: "高375米，建于1985年，是中亚最高的建筑。"
    }
  },
  {
    id: "registan", icon: "🕌", lat: 39.6547, lon: 66.9758, zoom: 16.4, pitch: 62, bearing: 180, stat: "XV–XVII",
    name: { uz: "Registon, Samarqand", en: "Registan, Samarkand", ru: "Регистан, Самарканд", zh: "撒马尔罕雷吉斯坦广场" },
    text: {
      uz: "Uchta madrasa: Ulug'bek, Sherdor va Tillakori. XV–XVII asrlarda qurilgan, Buyuk Ipak yo'lining durdonasi.",
      en: "Three madrasas: Ulugh Beg, Sher-Dor and Tilya-Kori, built in the 15th to 17th centuries. A jewel of the Great Silk Road.",
      ru: "Три медресе: Улугбека, Шердор и Тилля-Кари, построенные в XV–XVII веках. Жемчужина Великого шёлкового пути.",
      zh: "由兀鲁伯、希尔多尔和提拉卡里三座经学院组成，建于15至17世纪，是丝绸之路上的明珠。"
    }
  },
  {
    id: "bukhara-ark", icon: "🏰", lat: 39.7779, lon: 64.4106, zoom: 16.5, pitch: 60, bearing: 90, stat: "2 500+",
    name: { uz: "Buxoro, Ark qal'asi", en: "Bukhara, the Ark Fortress", ru: "Бухара, крепость Арк", zh: "布哈拉方舟城堡" },
    text: {
      uz: "Buxoro 2 500 yildan ortiq tarixga ega shahar. Ark qal'asi asrlar davomida Buxoro hukmdorlarining qarorgohi bo'lgan.",
      en: "Bukhara is more than 2,500 years old. For centuries the Ark fortress was the residence of Bukhara's rulers.",
      ru: "Бухаре более 2 500 лет. Крепость Арк веками была резиденцией правителей Бухары.",
      zh: "布哈拉拥有2500多年历史。几个世纪以来，方舟城堡一直是布哈拉统治者的居所。"
    }
  },
  {
    id: "bukhara-kalon", icon: "🕌", lat: 39.7759, lon: 64.4146, zoom: 17, pitch: 66, bearing: 30, stat: "1127",
    name: { uz: "Buxoro, Poyi Kalon va Minorai Kalon", en: "Bukhara, Po-i-Kalyan and Kalyan Minaret", ru: "Бухара, Пои-Калян и минарет Калян", zh: "布哈拉卡良宣礼塔" },
    text: {
      uz: "Minorai Kalon 1127-yilda qurilgan, balandligi 46 metrga yaqin. Rivoyatlarga ko'ra, Chingizxon shaharni vayron qilganda ham bu minoraga tegmagan.",
      en: "The Kalyan Minaret was built in 1127 and is about 46 metres tall. Legend says Genghis Khan spared it when he destroyed the city.",
      ru: "Минарет Калян построен в 1127 году, его высота около 46 метров. По легенде, Чингисхан пощадил его, разрушив город.",
      zh: "卡良宣礼塔建于1127年，高约46米。传说成吉思汗摧毁全城时唯独保留了它。"
    }
  },
  {
    id: "bukhara-lyabi", icon: "💧", lat: 39.7738, lon: 64.4202, zoom: 17, pitch: 60, bearing: 300, stat: "1620",
    name: { uz: "Buxoro, Labi Hovuz", en: "Bukhara, Lyabi-Hauz", ru: "Бухара, Ляби-Хауз", zh: "布哈拉莱比哈乌斯" },
    text: {
      uz: "1620-yilda qurilgan hovuz atrofidagi ansambl. Qadimiy tut daraxtlari, choyxonalar va Xo'ja Nasriddin haykali bilan mashhur.",
      en: "An ensemble around a pool built in 1620, famous for its old mulberry trees, teahouses and the statue of Khoja Nasreddin.",
      ru: "Ансамбль вокруг пруда 1620 года, известный старыми тутовыми деревьями, чайханами и памятником Ходже Насреддину.",
      zh: "围绕1620年修建的水池而建的建筑群，以古桑树、茶馆和纳斯尔丁·阿凡提雕像闻名。"
    }
  },
  {
    id: "khiva", icon: "🧱", lat: 41.3783, lon: 60.3594, zoom: 16.2, pitch: 58, bearing: 90, stat: "UNESCO 1990",
    name: { uz: "Xiva, Ichan qal'a", en: "Khiva, Itchan Kala", ru: "Хива, Ичан-Кала", zh: "希瓦伊钦卡拉内城" },
    text: {
      uz: "Devor bilan o'ralgan ochiq osmon ostidagi muzey-shahar. 1990-yilda O'zbekistondan birinchi bo'lib YuNESKO ro'yxatiga kiritilgan.",
      en: "A walled open-air museum city. In 1990 it became the first site in Uzbekistan on the UNESCO World Heritage List.",
      ru: "Город-музей под открытым небом за крепостной стеной. В 1990 году первым в Узбекистане вошёл в список ЮНЕСКО.",
      zh: "被城墙环绕的露天博物馆之城，1990年成为乌兹别克斯坦首个世界遗产。"
    }
  },
  {
    id: "aral", icon: "🏜️", lat: 45.0, lon: 59.8, zoom: 6.6, pitch: 35, bearing: 0, stat: "−90%",
    name: { uz: "Orol dengizi", en: "Aral Sea", ru: "Аральское море", zh: "咸海" },
    text: {
      uz: "Bir paytlar dunyodagi to'rtinchi eng katta ko'l edi. 1960-yillardan beri daryo suvlari sug'orishga olinib, dengiz 90 foizga qisqardi.",
      en: "Once the fourth-largest lake in the world. Since the 1960s, rivers were diverted for irrigation and the sea has lost about 90% of its area.",
      ru: "Когда-то четвёртое по величине озеро мира. С 1960-х реки отвели на орошение, и море сократилось примерно на 90%.",
      zh: "曾是世界第四大湖。自20世纪60年代河水被引去灌溉后，湖面缩小了约90%。"
    }
  },
  {
    id: "space", icon: "🛰️", lat: 30, lon: 65, zoom: 1.6, pitch: 0, bearing: 0, space: true, stat: "400 km",
    name: { uz: "Kosmos: Yer orbitasi", en: "Space: Earth orbit", ru: "Космос: орбита Земли", zh: "太空：地球轨道" },
    text: {
      uz: "Har bir nuqta haqiqiy sun'iy yo'ldosh. Xalqaro kosmik stansiya 400 km balandlikda soatiga 28 000 km tezlikda uchadi va Yerni har 90 daqiqada aylanib chiqadi.",
      en: "Every dot is a real satellite. The International Space Station flies 400 km up at 28,000 km/h and circles the Earth every 90 minutes.",
      ru: "Каждая точка — настоящий спутник. МКС летит на высоте 400 км со скоростью 28 000 км/ч и облетает Землю каждые 90 минут.",
      zh: "每个光点都是真实的卫星。国际空间站在400公里高空以每小时2.8万公里的速度飞行，每90分钟绕地球一圈。"
    }
  }
];

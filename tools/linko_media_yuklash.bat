@echo off
chcp 65001 >nul
rem Linko Map videolarini Cloudflare uchun yuklab oladi (Pexels, bepul litsenziya)
set OUT=%USERPROFILE%\Documents\linko-media
mkdir "%OUT%" 2>nul
cd /d "%OUT%"
echo Videolar shu papkaga yuklanmoqda: %OUT%
echo.
echo [takeoff]
curl -L --fail -o takeoff_1280.mp4 "https://videos.pexels.com/video-files/9512135/9512135-hd_1280_720_25fps.mp4"
curl -L --fail -o takeoff_960.mp4 "https://videos.pexels.com/video-files/9512135/9512135-sd_960_540_25fps.mp4"
curl -L --fail -o takeoff.jpg "https://images.pexels.com/videos/9512135/airplane-airport-airstrip-runway-9512135.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [climb]
curl -L --fail -o climb_1280.mp4 "https://videos.pexels.com/video-files/4396425/4396425-sd_960_540_30fps.mp4"
curl -L --fail -o climb_960.mp4 "https://videos.pexels.com/video-files/4396425/4396425-sd_640_360_30fps.mp4"
curl -L --fail -o climb.jpg "https://images.pexels.com/videos/4396425/airplane-airplane-take-off-airplane-window-airplane-wing-4396425.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [clouds]
curl -L --fail -o clouds_1280.mp4 "https://videos.pexels.com/video-files/12278380/12278380-hd_720_1280_60fps.mp4"
curl -L --fail -o clouds_960.mp4 "https://videos.pexels.com/video-files/12278380/12278380-sd_540_960_30fps.mp4"
curl -L --fail -o clouds.jpg "https://images.pexels.com/videos/12278380/pexels-photo-12278380.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [everest]
curl -L --fail -o everest_1280.mp4 "https://videos.pexels.com/video-files/29632834/12750574_1280_720_25fps.mp4"
curl -L --fail -o everest_960.mp4 "https://videos.pexels.com/video-files/29632834/12750573_960_540_25fps.mp4"
curl -L --fail -o everest.jpg "https://images.pexels.com/videos/29632834/above-the-himalaya-abstract-clouds-amadablam-climate-change-29632834.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [ocean]
curl -L --fail -o ocean_1280.mp4 "https://videos.pexels.com/video-files/26893767/12028836_960_540_24fps.mp4"
curl -L --fail -o ocean_960.mp4 "https://videos.pexels.com/video-files/26893767/12028834_640_360_24fps.mp4"
curl -L --fail -o ocean.jpg "https://images.pexels.com/videos/26893767/pexels-photo-26893767.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [dubai]
curl -L --fail -o dubai_1280.mp4 "https://videos.pexels.com/video-files/10518495/10518495-sd_960_540_25fps.mp4"
curl -L --fail -o dubai_960.mp4 "https://videos.pexels.com/video-files/10518495/10518495-sd_640_360_25fps.mp4"
curl -L --fail -o dubai.jpg "https://images.pexels.com/videos/10518495/aerial-footage-drone-dubai-dubai-marina-10518495.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [pyramids]
curl -L --fail -o pyramids_1280.mp4 "https://videos.pexels.com/video-files/32537704/13876133_1280_720_24fps.mp4"
curl -L --fail -o pyramids_960.mp4 "https://videos.pexels.com/video-files/32537704/13876132_960_540_24fps.mp4"
curl -L --fail -o pyramids.jpg "https://images.pexels.com/videos/32537704/pexels-photo-32537704.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [newyork]
curl -L --fail -o newyork_1280.mp4 "https://videos.pexels.com/video-files/36244245/15370507_1280_720_30fps.mp4"
curl -L --fail -o newyork_960.mp4 "https://videos.pexels.com/video-files/36244245/15370503_960_540_30fps.mp4"
curl -L --fail -o newyork.jpg "https://images.pexels.com/videos/36244245/pexels-photo-36244245.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [greatwall]
curl -L --fail -o greatwall_1280.mp4 "https://videos.pexels.com/video-files/30897424/13209584_1280_720_60fps.mp4"
curl -L --fail -o greatwall_960.mp4 "https://videos.pexels.com/video-files/30897424/13209583_960_540_60fps.mp4"
curl -L --fail -o greatwall.jpg "https://images.pexels.com/videos/30897424/above-aerial-ancient-architecture-30897424.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [shanghai]
curl -L --fail -o shanghai_1280.mp4 "https://videos.pexels.com/video-files/39410944/16781502_1280_720_25fps.mp4"
curl -L --fail -o shanghai_960.mp4 "https://videos.pexels.com/video-files/39410944/16781500_960_540_25fps.mp4"
curl -L --fail -o shanghai.jpg "https://images.pexels.com/videos/39410944/china-tourism-china-travel-vlog-lujiazui-shanghai-pudong-shanghai-39410944.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [hongkong]
curl -L --fail -o hongkong_1280.mp4 "https://videos.pexels.com/video-files/37760048/16016728_1280_720_25fps.mp4"
curl -L --fail -o hongkong_960.mp4 "https://videos.pexels.com/video-files/37760048/16016727_960_540_25fps.mp4"
curl -L --fail -o hongkong.jpg "https://images.pexels.com/videos/37760048/aerial-city-drone-hong-kong-37760048.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo [space]
curl -L --fail -o space_1280.mp4 "https://videos.pexels.com/video-files/33430410/14227688_1280_720_30fps.mp4"
curl -L --fail -o space_960.mp4 "https://videos.pexels.com/video-files/33430410/14227686_960_540_30fps.mp4"
curl -L --fail -o space.jpg "https://images.pexels.com/videos/33430410/pexels-photo-33430410.jpeg?auto=compress&cs=tinysrgb&w=1280"
echo.
echo Tayyor! Endi shu papkani Cloudflare Pages ga yuklang.
explorer "%OUT%"
pause

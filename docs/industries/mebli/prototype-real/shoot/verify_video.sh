#!/usr/bin/env bash
# Перевірка відео: параметри, статичні кадри >2 с (freezedetect) і порожні (майже білі) кадри. Використання: verify_video.sh video/x.mp4
f="$1"
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate:format=duration -of csv=p=0 "$f"
echo "--- нерухомі фрагменти >2 с (кінець відео — заставка, допустимо):"
ffmpeg -v info -i "$f" -vf "freezedetect=n=-55dB:d=2" -an -f null - 2>&1 | grep -E "freeze_(start|duration)" | paste - - | head -20
echo "--- майже білі кадри (YAVG>235), по 2 кадри/с:"
ffmpeg -v error -i "$f" -vf "fps=2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -an -f null - 2>/dev/null | paste - - | awk -F'[ =:]' '{ if ($NF+0>235) print $0 }' | head

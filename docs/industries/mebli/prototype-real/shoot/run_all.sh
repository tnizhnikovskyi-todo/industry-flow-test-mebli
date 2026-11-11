#!/usr/bin/env bash
# Повний прогін зйомки з ОДНОГО стану бази (щоб цифри дашборда збігались у скриншотах, мобільних кадрах, відео й SHOW.md).
# Прохід 1 — усе, що створює/підтверджує/запускає замовлення; прохід 2 — лише читання: усі кадри, що показують підсумки, і дашборд.
# Використання: run_all.sh [port]   (потрібні: build_db.sh уже виконано, serve.sh mebli_demo <port> запущено)
set -uo pipefail
cd "$(dirname "$0")"
rm -f ../video/rec/cookies.json
PORT="${1:-19071}"; export BASE="http://127.0.0.1:$PORT"
# прохід 1 (змінює базу)
node scenario.mjs "$PORT"
ONLY=m1 node scenario-mobile.mjs "$PORT"
node rec_clips.mjs D_sale M_sale D_board
./fix_dates.sh mebli_demo
# прохід 2 (лише читання; одна й та сама база -> однакові цифри всюди)
ONLY=7,8,9,10,13,14,15,16,17 node scenario.mjs "$PORT"
ONLY=m2,m3,m4,m5 node scenario-mobile.mjs "$PORT"
node rec_clips.mjs D_dash M_dash D_prod D_cut D_store D_margin M_prod M_store M_margin
node rec_cards.mjs

bash check_english.sh || exit 1

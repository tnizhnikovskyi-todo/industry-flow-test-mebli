#!/usr/bin/env bash
# Підйом демо-стенда пакета «меблі» з нуля (A-15) — тонка обгортка скриптів C-00 (tools/odoo/, README там).
# Використання: package/demo/up.sh <instance> <edition: ce|ee> [--profile <answers-файл>] [--tag <тег пакета>] [--no-demo]
#   <instance> — лише demo-mebli-pkg-<суфікс> (allow-list демо-баз стенда; demo-mebli-full / demo-mebli-sample не чіпаються);
#   --profile — за замовчуванням package/demo/answers.yaml (ключ edition у файлі має дорівнювати <edition>);
#   --tag — тег пакета (HEAD репо має збігатися: перевіряють clean_db.sh/install.sh C-00; A-18: git checkout <тег> -- package/demo/);
#   --no-demo — без демо-шару td_mebli_demo (лише модулі + конфіг + шаблони A-13).
# Адреса сервера стенда для PDF — змінна DEMO_REPORT_URL (D-17; напр. http://127.0.0.1:8079), без неї report.url порожній (web.base.url).
# Паролі демо-ролей — змінна DEMO_USERS_PASSWORD (В-4); не задано — локальний тестовий дефолт «demo-local» (WARN; лише localhost).
# Коди: 0 готово; 2 запуск/захист; 10 чиста база; 20 модулі; 30 конфіг (preflight, apply, read-back); 40 майстер-дані;
#       50 демо-дані/ролі/smoke; 60 знімок; 70 EE недоступна. Лог — package/demo/.logs/up-<instance>.log (не в git).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
T=tools/odoo; D=package/demo
INST="${1:-}"; ED="${2:-}"; shift 2 || true
PROFILE="$D/answers.yaml"; TAG=(); DEMO=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:?--profile потребує файл}"; shift 2 ;;
    --tag) TAG=(--tag "${2:?--tag потребує значення}"); shift 2 ;;
    --no-demo) DEMO=0; shift ;;
    *) echo "FLOW_STOP: невідомий аргумент '$1'" >&2; exit 2 ;;
  esac
done
[[ "$INST" =~ ^demo-mebli-pkg-[a-z0-9-]+$ ]] || { echo "FLOW_STOP: instance має бути demo-mebli-pkg-<суфікс> (отримано '$INST')" >&2; exit 2; }
[[ "$ED" == ce || "$ED" == ee ]] || { echo "FLOW_STOP: edition має бути ce|ee" >&2; exit 2; }
[[ -f "$PROFILE" ]] || { echo "FLOW_STOP: немає профілю $PROFILE" >&2; exit 2; }
PED="$(python3 -I -c 'import sys,yaml; print((yaml.safe_load(open(sys.argv[1])) or {}).get("edition",""))' "$PROFILE")"
[[ "$PED" == "$ED" ]] || { echo "FLOW_STOP: edition у $PROFILE = '$PED', аргумент '$ED'" >&2; exit 2; }
export ODOO_EDITION="$ED"
mkdir -p "$D/.logs"; LOG="$D/.logs/up-$INST.log"; : >"$LOG"
step() { # <код> <назва> <команда...>
  local code="$1" name="$2"; shift 2
  echo "---- $name: $*" >>"$LOG"
  set +e; "$@" >>"$LOG" 2>&1; local rc=$?; set -e
  if [[ $rc -eq 3 && "$ED" == ee ]]; then echo "FAIL $name: EE недоступна (WARN ee-unavailable) — стенд ee «не перевірено»"; exit 70; fi
  if [[ $rc -ne 0 ]]; then echo "FAIL $name (код $rc; лог $LOG)"; tail -n 15 "$LOG"; exit "$code"; fi
  echo "OK $name"
}
if [[ "$ED" == ee ]]; then  # EE: без ODOO_EE_ADDONS_PATH далі не йдемо (check_edition C-00 -> код 3)
  step 70 "редакція ee" bash -c 'source tools/odoo/_common.sh; check_edition'
fi
# 0. preflight конфігу і список модулів профілю (manifest.yaml `when`), до будь-яких змін
set +e; MODS="$(python3 -I $T/apply.py plan --config package/config --answers "$PROFILE" 2>>"$LOG")"; rc=$?; set -e
[[ $rc -eq 0 && -n "$MODS" ]] || { echo "FAIL preflight конфігу (PREFLIGHT STOP; лог $LOG)"; grep PREFLIGHT "$LOG" | tail -n 5; exit 30; }
echo "OK preflight: модулів $(tr ',' '\n' <<<"$MODS" | wc -l)"
# 1. чиста база
step 10 "чиста база $INST" $T/clean_db.sh "$INST" ${TAG[@]+"${TAG[@]}"}
# 2. модулі package/addons (доставка в ODOO_DELIVERY_DIR) + «Модулі до установки», мова uk_UA, потім перезапис перекладів
step 20 "модулі профілю" $T/install.sh "$INST" "$MODS" --addons-src package/addons --lang uk_UA ${TAG[@]+"${TAG[@]}"}
step 20 "переклади uk_UA" $T/install.sh "$INST" "$MODS" --update --lang uk_UA --i18n-overwrite
# 3. конфіг A-12 (apply-semantics: прохід, повтор = ідемпотентність, read-back)
step 30 "конфіг A-12" python3 -I $T/apply.py config --db "$INST" --config package/config --answers "$PROFILE"
step 30 "конфіг A-12, повтор" python3 -I $T/apply.py config --db "$INST" --config package/config --answers "$PROFILE" --mode compare
step 30 "конфіг A-12, read-back" python3 -I $T/apply.py config --db "$INST" --config package/config --answers "$PROFILE" --mode readback
# 4. шаблони майстер-даних A-13 (порядок package/master-data/README.md; без td_mebli_bas — без td/19b…21b)
EXCL=""
[[ ",$MODS," == *",td_mebli_bas,"* ]] || EXCL="td/19b_res.partner.csv,td/20b_product.product.csv,td/21b_hr.employee.csv"
step 40 "майстер-дані A-13" $T/import.sh "$INST" --dir package/master-data ${EXCL:+--exclude "$EXCL"}
# 5–6. демо-шар td_mebli_demo (каталог, склад, документи, демо-ролі) — потребує td_mebli_bas (залежність модуля)
ALL="$MODS"
if (( DEMO )) && [[ ",$MODS," == *",td_mebli_bas,"* ]]; then
  step 50 "модуль демо-даних td_mebli_demo" $T/install.sh "$INST" td_mebli_demo --lang uk_UA
  # D-17: адреса сервера стенда для PDF (report.url); без змінної report.url порожній — Odoo друкує з web.base.url
  if [[ -n "${DEMO_REPORT_URL:-}" ]]; then echo "OK report.url = $DEMO_REPORT_URL (DEMO_REPORT_URL)"; export DEMO_REPORT_URL
  else echo "WARN DEMO_REPORT_URL не задано: report.url порожній, PDF — з web.base.url (задайте адресу сервера стенда, напр. http://127.0.0.1:8079)"; fi
  step 50 "демо-документи (seed)" python3 -I $T/apply.py shell --db "$INST" --script $D/data/seed_demo.py
  if [[ -z "${DEMO_USERS_PASSWORD:-}" ]]; then
    # дефолт лише для локального тесту (стенд на localhost); для хостингу B-01 пароль задає Тімлід через змінну (В-4)
    export DEMO_USERS_PASSWORD="demo-local"
    echo "WARN паролі демо-ролей: DEMO_USERS_PASSWORD не задано — локальний тестовий дефолт (не для хостингу)"
  fi
  step 50 "паролі демо-ролей" python3 -I $T/apply.py shell --db "$INST" --script $D/data/set_passwords.py
  ALL="$MODS,td_mebli_demo"
  step 50 "smoke стенда" $T/smoke.sh "$INST" "$ALL" --script $D/data/verify_demo.py
  # демо-шар (td_mebli_demo/data/settings_data.xml) вмикає коробку B — конфіг після нього має й далі = answers.yaml
  step 50 "конфіг після демо-шару, read-back" python3 -I $T/apply.py config --db "$INST" --config package/config --answers "$PROFILE" --mode readback
else
  if (( DEMO )); then WHY="профіль без td_mebli_bas — td_mebli_demo від нього залежить"; else WHY="--no-demo"; fi
  echo "WARN демо-шар пропущено ($WHY): лише шаблони A-13"
  step 50 "smoke стенда" $T/smoke.sh "$INST" "$ALL"
fi
# 7. знімок для reset.sh (C-00 snapshot.sh: createdb -T + filestore)
step 60 "знімок $INST-snap" $T/snapshot.sh "$INST"
echo "OK up: $INST ($ED, профіль $(basename "$PROFILE"), SHA $(git rev-parse --short HEAD))"

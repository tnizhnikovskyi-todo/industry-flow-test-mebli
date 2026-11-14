#!/usr/bin/env bash
# Імпорт CSV майстер-даних у тестову/демо-базу (C-00, тест «меблі»). Використання:
#   import.sh <db> <model> <file.csv>                                  один файл (модель задано явно)
#   import.sh <db> --dir <package/master-data> [--exclude f1,f2] [--out res.json]
#        усі шаблони в порядку README A-13: спершу <dir>/*.csv за іменем (01…15), потім <dir>/td/*.csv за іменем
#        (= «Порядок імпорту» package/master-data/README.md); модель -- з імені файла `NN_<model>.csv`;
#        --exclude -- шляхи відносно <dir> (напр. td/19b_res.partner.csv для профілю без td_mebli_bas).
# Канал: odoo-bin shell + ORM load() (= base_import) -- import_shell.py; кожен файл комітиться окремо, перша помилка -> стоп.
# Вивід: рядок на файл «OK|FAIL <файл> <модель> rows=N ids=M» і підсумок; код 0 -- усе OK, 1 -- помилка імпорту, 2 -- FLOW_STOP.
source "$(dirname "$0")/_common.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"
DB="${1:-}"; shift || true
guard_db "$DB"
check_edition
FILES=(); MODEL=""; DIR=""; EXCL=""; OUT=""
if [[ "${1:-}" == "--dir" ]]; then
  DIR="${2:?--dir потребує каталог}"; shift 2
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --exclude) EXCL="${2:?}"; shift 2 ;;
      --out) OUT="${2:?}"; shift 2 ;;
      *) echo "FLOW_STOP: невідомий аргумент '$1'" >&2; exit 2 ;;
    esac
  done
  [[ -d "$DIR" ]] || { echo "FLOW_STOP: немає каталогу $DIR" >&2; exit 2; }
  DIR="$(cd "$DIR" && pwd)"
  while IFS= read -r f; do
    rel="${f#"$DIR"/}"
    case ",$EXCL," in *",$rel,"*) echo "SKIP $rel (--exclude)"; continue ;; esac
    FILES+=("$f")
  done < <(LC_ALL=C ls -1 "$DIR"/*.csv 2>/dev/null; [[ -d "$DIR/td" ]] && LC_ALL=C ls -1 "$DIR"/td/*.csv 2>/dev/null)
else
  MODEL="${1:-}"; FILE="${2:-}"
  [[ "$MODEL" =~ ^[a-z0-9_.]+$ && -f "$FILE" ]] || { echo "Потрібні <model> і існуючий <file.csv> (або --dir <каталог>)" >&2; exit 2; }
  FILES=("$(cd "$(dirname "$FILE")" && pwd)/$(basename "$FILE")")
fi
(( ${#FILES[@]} )) || { echo "FLOW_STOP: немає CSV для імпорту" >&2; exit 2; }
for f in "${FILES[@]}"; do
  [[ -n "$MODEL" || "$(basename "$f")" =~ ^[0-9]+[a-z]?_[a-z0-9_.]+\.csv$ ]] || { echo "FLOW_STOP: ім'я '$f' не NN_<model>.csv" >&2; exit 2; }
done
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
RES="${OUT:-$TMP/res.json}"
odoo_args
set +e
IMP_FILES="$(printf '%s\n' "${FILES[@]}")" IMP_MODEL="$MODEL" IMP_OUT="$RES" \
  "$ODOO_BIN" shell ${ODOO_ARGS[@]+"${ODOO_ARGS[@]}"} -d "$DB" --no-http --log-level=warn <"$HERE/import_shell.py" >"$TMP/log" 2>&1
RC=$?
set -e
grep -E " (ERROR|CRITICAL) |Traceback" -A 15 "$TMP/log" | head -40 || true
[[ -s "$RES" ]] || { echo "FAIL import: результату немає (odoo-bin код $RC)"; exit 1; }
python3 -I - "$RES" "${DIR:-}" "${#FILES[@]}" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))['results']; base = sys.argv[2]; want = int(sys.argv[3])
rows = ids = 0
for x in r:
    f = x['file'][len(base) + 1:] if base and x['file'].startswith(base) else x['file']
    print('%s %s %s rows=%d ids=%d%s' % ('OK' if x['ok'] else 'FAIL', f, x['model'], x['rows'], x['ids'],
                                         '' if x['ok'] else ' errors=' + json.dumps(x['errors'], ensure_ascii=False)[:400]))
    rows += x['rows']; ids += x['ids']
ok = len(r) == want and all(x['ok'] for x in r)
print('%s import: файлів %d/%d, рядків %d, записів %d' % ('OK' if ok else 'FAIL', sum(1 for x in r if x['ok']), want, rows, ids))
sys.exit(0 if ok else 1)
PY

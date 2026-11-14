#!/usr/bin/env bash
# Мінімальний smoke: база існує, модулі завантажуються без ERROR. Використання:
#   smoke.sh <db> <module1,module2,...> [--script <smoke.py>]
# --script (C-00): бізнес-smoke пакета -- скрипт `odoo-bin shell` (змінна env); PASS лише якщо в його виводі є рядок «SMOKE OK»
#   (скрипт сам робить env.cr.rollback(), якщо створює записи; напр. package/demo/smoke_demo.py).
source "$(dirname "$0")/_common.sh"
DB="${1:-}"; MODS="${2:-}"; SCRIPT=""
if [[ "${3:-}" == "--script" ]]; then SCRIPT="${4:?--script потребує файл}"; [[ -f "$SCRIPT" ]] || { echo "FLOW_STOP: немає $SCRIPT" >&2; exit 2; }; fi
guard_db "$DB"
check_edition
[[ -n "$MODS" ]] || { echo "Не задано модулі" >&2; exit 2; }
psql -d "$DB" -Atc "select 1" >/dev/null || { echo "FAIL smoke: немає доступу до бази $DB"; exit 1; }
require_installed "$DB" "$MODS" || { echo "FAIL smoke: модулі не installed у $DB"; exit 1; }
odoo_args
LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT
set +e
"$ODOO_BIN" ${ODOO_ARGS[@]+"${ODOO_ARGS[@]}"} -d "$DB" -u "$MODS" --stop-after-init --log-level=warn >"$LOG" 2>&1
RC=$?
set -e
grep -E " (ERROR|CRITICAL) |Traceback" -A 15 "$LOG" | head -60 || true
if [[ $RC -ne 0 ]] || grep -qE " (ERROR|CRITICAL) " "$LOG"; then echo "FAIL smoke: $DB"; exit 1; fi
require_installed "$DB" "$MODS" || { echo "FAIL smoke: $DB (не installed)"; exit 1; }
if [[ -n "$SCRIPT" ]]; then
  set +e
  "$ODOO_BIN" shell ${ODOO_ARGS[@]+"${ODOO_ARGS[@]}"} -d "$DB" --no-http --log-level=warn <"$SCRIPT" >"$LOG" 2>&1
  set -e
  grep -E "^SMOKE|Traceback" -A 10 "$LOG" | head -40 || true
  grep -qx "SMOKE OK" "$LOG" || { echo "FAIL smoke: бізнес-smoke $SCRIPT"; exit 1; }
fi
echo "OK smoke: $DB ($MODS${SCRIPT:+; бізнес-smoke $(basename "$SCRIPT")})"

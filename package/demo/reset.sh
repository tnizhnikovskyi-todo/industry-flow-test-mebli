#!/usr/bin/env bash
# Скидання демо-стенда пакета «меблі» до початкового стану (A-15) — обгортка C-00.
# Використання: package/demo/reset.sh <instance> <edition: ce|ee> [аргументи up.sh: --profile <файл> --tag <тег> --no-demo]
# Є знімок <instance>-snap (його робить up.sh, крок 7) — tools/odoo/restore.sh (createdb -T + filestore, секунди);
# знімка немає — повний up.sh <instance> <edition> (fallback). Коди — як up.sh; restore без знімка — fallback, не помилка.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
INST="${1:-}"; ED="${2:-}"
[[ "$INST" =~ ^demo-mebli-pkg-[a-z0-9-]+$ ]] || { echo "FLOW_STOP: instance має бути demo-mebli-pkg-<суфікс>" >&2; exit 2; }
[[ "$ED" == ce || "$ED" == ee ]] || { echo "FLOW_STOP: edition має бути ce|ee" >&2; exit 2; }
if [[ "$ED" == ce ]]; then
  set +e; ODOO_EDITION=ce tools/odoo/restore.sh "$INST"; rc=$?; set -e
  [[ $rc -eq 0 ]] && { echo "OK reset: $INST зі знімка"; exit 0; }
  [[ $rc -eq 4 ]] || { echo "FAIL reset: restore.sh код $rc"; exit 60; }
fi
echo "WARN reset: знімка немає — повний підйом up.sh"
exec package/demo/up.sh "$@"

#!/usr/bin/env bash
# Id записів демо-бази для кроків зйомки (seed td_mebli_demo: wave2.py пише параметр td_mebli_demo.shot_ids).
# Використання: eval "$(./ids.sh demo-mebli-full)"  -> export SHOT_IDS=… і змінні кроків A1–A4 (NOPAY_ORDER_ID, …)
set -euo pipefail
DB="${1:?потрібна база}"
J="$(psql -d "$DB" -Atc "SELECT value FROM ir_config_parameter WHERE key = 'td_mebli_demo.shot_ids'")"
[[ -n "$J" ]] || { echo "FLOW_STOP: у $DB немає td_mebli_demo.shot_ids (seed не дійшов до хвилі 2)" >&2; exit 2; }
printf "export SHOT_IDS='%s'\n" "$J"
python3 -c '
import json, sys
ids = json.loads(sys.argv[1])
for key, env in (("nopay_order", "NOPAY_ORDER_ID"), ("nopay_task", "NOPAY_TASK_ID"), ("paid_order", "PAID_ORDER_ID"),
                 ("cut_order", "CUT_ORDER_ID"), ("cut_job", "CUT_JOB_ID"), ("act", "PDF_ACT_ID"), ("kit_order", "KIT_ORDER_ID"),
                 ("show", "ORDER_ID")):
    if ids.get(key):
        print(f"export {env}={ids[key]}")
' "$J"

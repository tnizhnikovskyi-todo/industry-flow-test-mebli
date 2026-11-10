#!/usr/bin/env bash
# Нові замовлення зйомки мають робочий час (а не нічний час запуску зйомки): 09:00–15:xx за Києвом, сьогодні (або вчора, якщо ще рано).
set -euo pipefail
DB="${1:-mebli_demo}"
psql -q -d "$DB" <<'SQL'
WITH n AS (SELECT id, row_number() OVER (ORDER BY id) AS rn FROM sale_order WHERE create_date > now() - interval '2 days' AND date_order > now() - interval '1 day')
UPDATE sale_order s SET date_order = (CASE WHEN extract(hour from now()) < 14 THEN date_trunc('day', now()) - interval '1 day' ELSE date_trunc('day', now()) END)
        + interval '7 hours 5 minutes' + (n.rn * interval '37 minutes') FROM n WHERE s.id = n.id;
SQL

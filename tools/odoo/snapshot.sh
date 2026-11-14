#!/usr/bin/env bash
# Знімок тестової/демо-бази (C-00, тест «меблі»): <db> -> <db>-snap (createdb -T) + копія filestore.
# Використання: snapshot.sh <db>      Відновлення: restore.sh <db>. Обидві бази проходять guard_db (allow-list імен і хостів).
# filestore: $ODOO_DATA_DIR/filestore/<db> (data_dir конфігу tools; ODOO_DATA_DIR задає env.local.sh). Код 0 -- готово.
source "$(dirname "$0")/_common.sh"
DB="${1:-}"; SNAP="${DB}-snap"
guard_db "$DB"; guard_db "$SNAP"
psql -d "$DB" -Atc "select 1" >/dev/null 2>&1 || { echo "FAIL snapshot: бази $DB немає"; exit 1; }
dropdb --if-exists --force "$SNAP"
createdb -T "$DB" "$SNAP"
FS="${ODOO_DATA_DIR:?задайте ODOO_DATA_DIR}/filestore"
rm -rf -- "${FS:?}/$SNAP"
[[ ! -d "$FS/$DB" ]] || cp -a "$FS/$DB" "$FS/$SNAP"
echo "OK snapshot: $DB -> $SNAP"

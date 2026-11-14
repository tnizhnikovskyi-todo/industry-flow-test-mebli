#!/usr/bin/env bash
# Відновлення бази зі знімка snapshot.sh (C-00, тест «меблі»): <db>-snap -> <db> (dropdb --force, createdb -T) + filestore.
# Використання: restore.sh <db>. Немає знімка -- код 4 (викликач робить повний підйом). Код 0 -- відновлено.
source "$(dirname "$0")/_common.sh"
DB="${1:-}"; SNAP="${DB}-snap"
guard_db "$DB"; guard_db "$SNAP"
psql -d "$SNAP" -Atc "select 1" >/dev/null 2>&1 || { echo "NO-SNAPSHOT restore: знімка $SNAP немає" >&2; exit 4; }
dropdb --if-exists --force "$DB"
createdb -T "$SNAP" "$DB"
FS="${ODOO_DATA_DIR:?задайте ODOO_DATA_DIR}/filestore"
rm -rf -- "${FS:?}/$DB"
[[ ! -d "$FS/$SNAP" ]] || cp -a "$FS/$SNAP" "$FS/$DB"
echo "OK restore: $SNAP -> $DB"

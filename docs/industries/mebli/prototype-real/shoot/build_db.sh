#!/usr/bin/env bash
# Створює базу показу: модулі td_mebli_*, українська мова, насичені демо-дані. Використання: build_db.sh [ім'я_бази]
set -euo pipefail
DB="${1:-mebli_demo}"
ROOT="$(cd "$(dirname "$0")/../../../../.." && pwd)"
export F3D_ADDONS_DIR="$ROOT/package/addons"
T="${F3D_TOOLS:-/home/user/f3d/factory3d/tools/odoo}"
$T/drop_db.sh "$DB" >/dev/null 2>&1 || true
$T/new_db.sh "$DB"
F3D_TEST_INSTALL=td_mebli_demo $T/update.sh "$DB" -- --load-language=uk_UA
# повторне оновлення вже встановлених модулів з перезаписом перекладів: терміни view-ів потрапляють у uk_UA
F3D_TEST_INSTALL=td_mebli_mrp,td_mebli_sale,td_mebli_cutting,td_mebli_dashboard,td_mebli_demo $T/update.sh "$DB" -- --i18n-overwrite --load-language=uk_UA
source "$T/env.sh"
$ODOO_PY $ODOO_BIN shell -c "$ODOO_CONF" --addons-path="$ODOO_ADDONS_PATH" -d "$DB" --no-http \
    < "$F3D_ADDONS_DIR/td_mebli_demo/scripts/seed_showcase.py" 2>&1 | grep -v " INFO \| WARNING " | tail -15

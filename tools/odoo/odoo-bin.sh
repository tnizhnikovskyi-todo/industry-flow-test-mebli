#!/usr/bin/env bash
# Обгортка ODOO_BIN: odoo-bin з venv Odoo (shebang odoo-bin — системний python3 без залежностей Odoo). C-00, тест «меблі».
exec "${ODOO_PY:?задайте ODOO_PY (tools/odoo/env.local.sh)}" "${ODOO_SRC_BIN:?задайте ODOO_SRC_BIN}" "$@"

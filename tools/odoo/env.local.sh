#!/usr/bin/env bash
# Локальне середовище тестового репо «меблі» (C-00, адаптація шаблонів). Підключається автоматично з _common.sh
# (вимкнути: FLOW_ENV_LOCAL=0) або вручну: `source tools/odoo/env.local.sh` (потрібно для apply.py/validate.py/preflight.sh).
# Лише ЗНАЧЕННЯ ЗА ЗАМОВЧУВАННЯМ: змінна, задана раніше (CI, інша машина), не перезаписується.
# Секретів тут немає: PostgreSQL — локальний unix-сокет (peer), ODOO_API_KEY не задається.
_ODOO_HOME_DIR="${ODOO_HOME_DIR:-/home/user/odoo19}"
_TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${ODOO_PY:=$_ODOO_HOME_DIR/venv/bin/python}"                 # venv Odoo (odoo-bin має shebang python3 системи — без залежностей Odoo)
: "${ODOO_SRC_BIN:=$_ODOO_HOME_DIR/src/odoo-bin}"
: "${ODOO_BIN:=$_TOOLS_DIR/odoo-bin.sh}"                        # обгортка: $ODOO_PY $ODOO_SRC_BIN "$@"
: "${ODOO_DELIVERY_DIR:=$_ODOO_HOME_DIR/delivery}"              # ОКРЕМИЙ каталог доставки install.sh --addons-src (поза репо)
: "${ODOO_ADDONS_PATH:=$_ODOO_HOME_DIR/src/addons,$_ODOO_HOME_DIR/src/odoo/addons,$ODOO_DELIVERY_DIR}"
: "${ODOO_DATA_DIR:=$_ODOO_HOME_DIR/data-tools}"               # data_dir конфігу tools (filestore <data_dir>/filestore/<db>)
: "${ODOO_CONF:=$_ODOO_HOME_DIR/odoo-tools.conf}"               # окремий конфіг tools (НЕ /home/user/odoo19/odoo.conf головного чекауту)
: "${ODOO_EDITION:=ce}"                                         # EE недоступна: ODOO_EE_ADDONS_PATH не задається
: "${ODOO_ALLOWED_HOSTS:=localhost,127.0.0.1}"                  # лише локальний PostgreSQL 16; PGHOST не задано = localhost (unix-сокет)
# Демо-дані (звірено з `odoo-bin server --help` Odoo 19.0: `--with-demo`; `--without-demo=BOOL` — «default»).
: "${ODOO_DEMO_OPT:=--with-demo}"
: "${ODOO_NODEMO_OPT:=--without-demo=True}"
# run_tests.sh: рядок підсумку Odoo 19 (`odoo.tests.result: 0 failed, 0 error(s) of 308 tests when loading database 'x'`).
: "${TESTS_SUMMARY_RE:=[0-9]+ failed, [0-9]+ error\(s\) of [0-9]+ tests}"
: "${PKG_REPO:=$(git -C "$_TOOLS_DIR" rev-parse --show-toplevel 2>/dev/null || true)}"
export ODOO_DATA_DIR ODOO_PY ODOO_SRC_BIN ODOO_BIN ODOO_DELIVERY_DIR ODOO_ADDONS_PATH ODOO_CONF ODOO_EDITION ODOO_ALLOWED_HOSTS \
       ODOO_DEMO_OPT ODOO_NODEMO_OPT TESTS_SUMMARY_RE PKG_REPO
# Конфіг tools: створюється з odoo.conf.example, якщо його ще немає (поза репо; секретів не містить).
if [[ ! -f "$ODOO_CONF" && -f "$_TOOLS_DIR/odoo.conf.example" ]]; then
  mkdir -p "$ODOO_DELIVERY_DIR" "$ODOO_DATA_DIR" 2>/dev/null || true
  sed -e "s#@ADDONS_PATH@#$ODOO_ADDONS_PATH#" -e "s#@DATA_DIR@#$ODOO_DATA_DIR#" "$_TOOLS_DIR/odoo.conf.example" >"$ODOO_CONF" 2>/dev/null || true
fi
unset _ODOO_HOME_DIR _TOOLS_DIR

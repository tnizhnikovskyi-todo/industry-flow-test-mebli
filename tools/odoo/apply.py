#!/usr/bin/env python3
"""Еталон C-00: застосування конфіг-пакета у ТЕСТОВУ базу. Лише stdlib. Не перевірявся на реальному Odoo 19.

Режими (підкоманди):
  modules  --db DB --modules a,b                       odoo-bin -u <модулі>: підхоплює data-файли з manifest (XML/CSV); потім перевірка state=installed
                                                       (psql, як require_installed в install.sh), інакше rc=1. Доставку модулів робить install.sh --addons-src.
  shell    --db DB --script FILE.py                    odoo-bin shell -d DB < FILE.py (змінна `env` у скрипті).
  plan     --config package/config --answers A.yaml [--out plan.json]   (C-00) preflight + модулі профілю (друкує через кому).
  config   --db DB --config package/config --answers A.yaml [--mode apply|compare|readback] [--out res.json]
           (C-00, адаптер формату package/config/: manifest.yaml format 2 + vp-map.yaml + data/*.yaml; odoo-bin shell + config_shell.py).
                                                       Скрипт сам викликає env.cr.commit(): інакше зміни відкочуються (припущення, звірити).
  rpc      --db DB --plan plan.json [--dry-run]        upsert за xml-id через XML-RPC /xmlrpc/2 (execute_kw).
Формат plan.json: [{"xmlid": "td_config.vp_01", "model": "res.partner", "values": {"name": "X"}}, ...]
  Скалярні значення; many2one -- числовий id (xml-id у id розв'язує викликач). Порядок записів = порядок застосування.
Середовище: ODOO_BIN, ODOO_CONF, ODOO_ADDONS_PATH (режими modules/shell); ODOO_URL, ODOO_LOGIN, ODOO_API_KEY,
  ODOO_ALLOWED_HOSTS=host1,host2 (режим rpc; без allowlist -- FLOW_STOP). Секрети лише зі змінних, не з аргументів.
Лічильники created/updated/unchanged у режимах modules/shell завжди 0: ідемпотентність за ними не перевіряється (лише rpc їх рахує).
Обмеження rpc: створення запису і ir.model.data -- два виклики, не атомарно; збій між ними лишає запис без xml-id і повтор створить дубль (відкрите питання C-00: чи є в Odoo 19 підтримуваний одновикликовий upsert за xml-id -- не вигадано). Значення в plan.json лише скалярні; ODOO_URL -- https (http лише для localhost/127.0.0.1).
Вихід: JSON-підсумок {"created","updated","unchanged","manual","errors"} в останньому рядку stdout. Коди: 0 ок, 1 помилки даних, 2 запуск/захист.
Відкрите для C-00: рядок підсумку тестів/поведінка shell-коміту в Odoo 19; JSON-2 API (/json/2) -- не використано, доки не підтверджено.
"""
import argparse, json, os, re, subprocess, sys, xmlrpc.client
from urllib.parse import urlparse

DB_OK = re.compile(r"(test-|test-pkg-|demo-|emu-).+")
DB_CHARS = re.compile(r"[A-Za-z0-9_-]+")
MOD_OK = re.compile(r"[a-z0-9_]+")
SCALAR = (str, int, float, bool, type(None))


def stop(msg):
    print("FLOW_STOP: " + msg, file=sys.stderr)
    sys.exit(2)


def guard_db(db):
    if not db:
        stop("не задано ім'я бази")
    if re.search("prod", db, re.I):
        stop("ім'я бази '%s' містить prod; відмова" % db)
    if not DB_OK.fullmatch(db) or not DB_CHARS.fullmatch(db):
        stop("база '%s' не відповідає test-*|test-pkg-*|demo-*|emu-*; відмова (прод не чіпаємо)" % db)


def guard_host(url):
    allowed = [h.strip() for h in os.environ.get("ODOO_ALLOWED_HOSTS", "").replace(" ", ",").split(",") if h.strip()]
    if not allowed:
        stop("задайте ODOO_ALLOWED_HOSTS (allowlist непродових серверів); ім'я бази сервер не гарантує")
    host = urlparse(url).hostname
    if host not in allowed:
        stop("хост '%s' не в ODOO_ALLOWED_HOSTS" % host)


def load_env_local():
    """C-00 (тест «меблі»): значення за замовчуванням з env.local.sh (як _common.sh); задані змінні не перезаписуються."""
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "env.local.sh")
    if os.environ.get("FLOW_ENV_LOCAL", "1") == "0" or not os.path.isfile(f):
        return
    try:
        out = subprocess.run(["bash", "-c", 'source "$1" >/dev/null 2>&1; env -0', "_", f], capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        stop("env.local.sh не завантажився: %s" % e)
    for kv in out.split(b"\0"):
        k, _, v = kv.decode("utf-8", "replace").partition("=")
        if k and k not in os.environ:
            os.environ[k] = v


def odoo_base(cmd=None):
    # C-00: підкоманда odoo-bin (shell) має йти ПЕРЕД -c/--addons-path (інакше Odoo 19: «server: error: unrecognized parameters: shell»)
    args = [os.environ.get("ODOO_BIN", "odoo-bin")] + ([cmd] if cmd else [])
    if os.environ.get("ODOO_CONF"):
        args += ["-c", os.environ["ODOO_CONF"]]
    ap = os.environ.get("ODOO_ADDONS_PATH", "")
    ed = os.environ.get("ODOO_EDITION", "ce")
    ee = os.environ.get("ODOO_EE_ADDONS_PATH", "")
    if ed == "ee":
        # як _common.sh: EE-шлях додається лише при ee; без доступу -- код 3 (WARN ee-unavailable)
        if not ee or not os.path.isdir(ee):
            sys.stderr.write("WARN ee-unavailable: ODOO_EE_ADDONS_PATH не задано або каталогу немає; EE-перевірка не виконана (не перевірено)\n")
            sys.exit(3)
        ap = (ap + "," if ap else "") + ee
    elif ed == "ce":
        if ee and ee.rstrip("/") in [x.rstrip("/") for x in ap.split(",") if x]:
            stop("ODOO_EDITION=ce, але ODOO_EE_ADDONS_PATH входить до ODOO_ADDONS_PATH")
    else:
        stop("ODOO_EDITION='%s' (очікується ce|ee)" % ed)
    if ap:
        args += ["--addons-path=" + ap]
    return args


def run_logged(cmd, db, stdin=None, mods=None):
    try:
        p = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
    except OSError as e:
        stop("не вдалося запустити %s: %s" % (cmd[0], e))
    bad = [l for l in (p.stdout + p.stderr).splitlines() if re.search(r" (ERROR|CRITICAL) |Traceback", l)]
    for l in bad[:40]:
        print(l, file=sys.stderr)
    errors = [] if p.returncode == 0 and not bad else ["odoo-bin: код %d, ERROR-рядків %d" % (p.returncode, len(bad))]
    if not errors and mods:  # -u невстановленого/невідомого модуля -- тихий no-op (WARNING, код 0)
        for m in mods:
            try:
                q = subprocess.run(["psql", "-d", db, "-Atc", "select state from ir_module_module where name='%s'" % m],
                                   capture_output=True, text=True)
            except OSError as e:
                stop("не вдалося запустити psql: %s" % e)
            st = q.stdout.strip()
            if st != "installed":
                errors.append("module %s: стан '%s', очікується installed" % (m, st or "немає в базі"))
    print(json.dumps({"created": 0, "updated": 0, "unchanged": 0, "manual": 0, "errors": errors}))
    return 0 if not errors else 1


def rpc_conn(db):
    url = os.environ.get("ODOO_URL", "")
    login, key = os.environ.get("ODOO_LOGIN"), os.environ.get("ODOO_API_KEY")
    if not (url and login and key):
        stop("задайте ODOO_URL, ODOO_LOGIN, ODOO_API_KEY")
    pu = urlparse(url)
    if pu.scheme != "https" and not (pu.scheme == "http" and pu.hostname in ("localhost", "127.0.0.1")):
        stop("ODOO_URL має бути https (http лише для localhost/127.0.0.1): API-ключ не передаємо відкрито")
    guard_host(url)
    try:
        uid = xmlrpc.client.ServerProxy(url.rstrip("/") + "/xmlrpc/2/common").authenticate(db, login, key, {})
    except (OSError, xmlrpc.client.Error) as e:
        stop("автентифікація не вдалася: %s" % str(e)[:200])
    if not uid:
        stop("автентифікація в базі '%s' не вдалася" % db)
    obj = xmlrpc.client.ServerProxy(url.rstrip("/") + "/xmlrpc/2/object", allow_none=True)
    return lambda model, method, *a, **kw: obj.execute_kw(db, uid, key, model, method, list(a), kw)


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        stop("не вдалося прочитати JSON '%s': %s" % (path, e))


def norm(v):
    return v[0] if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int) else v  # many2one -> id


def same(cur, v):
    """Порівняння значення з бази (read) з планом: False з бази == null/"" з плану (для небулевого очікуваного)."""
    cur = norm(cur)
    if cur is False and (v is None or v == ""):
        return True
    return cur == v


def cmd_rpc(a):
    call = rpc_conn(a.db)
    plan = load_json(a.plan)
    if not isinstance(plan, list):
        stop("plan.json має бути списком")
    res = {"created": 0, "updated": 0, "unchanged": 0, "manual": 0, "errors": []}
    for it in plan:
        try:
            mod, name = it["xmlid"].split(".", 1)
            imd = call("ir.model.data", "search_read", [["module", "=", mod], ["name", "=", name]],
                       fields=["res_id", "model"], limit=1)
            vals = it["values"]
            if not all(isinstance(v, SCALAR) for v in vals.values()):
                raise ValueError("нескалярне значення в values (many2one -- числовий id; x2many не підтримано)")
            if not imd:
                if not a.dry_run:
                    rid = call(it["model"], "create", vals)
                    call("ir.model.data", "create", {"module": mod, "name": name, "model": it["model"], "res_id": rid})
                res["created"] += 1
                continue
            cur = call(it["model"], "read", [imd[0]["res_id"]], fields=list(vals))[0]
            diff = {k: v for k, v in vals.items() if not same(cur.get(k), v)}
            if diff:
                if not a.dry_run:
                    call(it["model"], "write", [imd[0]["res_id"]], diff)
                res["updated"] += 1
            else:
                res["unchanged"] += 1
        except Exception as e:  # noqa: BLE001
            res["errors"].append("%s: %s" % (it.get("xmlid"), str(e)[:200]))
    print(json.dumps(res))
    return 1 if res["errors"] else 0


def cmd_config(a):
    """plan: answers + package/config -> plan.json (preflight, модулі за when, пункти даних); друкує модулі через кому.
    config: plan + odoo-bin shell зі скриптом config_shell.py (apply|compare|readback); підсумок JSON, код 1 при errors/FAIL."""
    import tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import config_plan  # потребує PyYAML (системний python3), не stdlib
    plan = config_plan.build(a.config, a.answers)
    mode = getattr(a, "cfg_mode", None) or "plan"
    errs = [x for x in plan["preflight"] if x["on_violation"] == "error"]
    if mode == "plan":
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(plan, f, ensure_ascii=False, default=str)
        for x in plan["preflight"]:
            sys.stderr.write("PREFLIGHT %s %s: %s\n" % (x["on_violation"], x["id"], x["message"]))
        if errs:
            sys.stderr.write("PREFLIGHT STOP: %s\n" % ",".join(x["id"] for x in errs))
            return 1
        print(",".join(plan["modules"]))
        return 0
    if errs:
        print(json.dumps({"preflight": "STOP", "errors": [x["id"] + ": " + x["message"] for x in errs]}, ensure_ascii=False))
        return 1
    with tempfile.TemporaryDirectory() as td:
        pin, pout = os.path.join(td, "plan.json"), a.out or os.path.join(td, "out.json")
        with open(pin, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, default=str)
        os.environ.update({"CFG_IN": pin, "CFG_MODE": mode, "CFG_OUT": pout})
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_shell.py"), encoding="utf-8").read()
        try:
            p = subprocess.run(odoo_base("shell") + ["-d", a.db, "--no-http", "--log-level=warn"], input=src, capture_output=True, text=True)
        except OSError as e:
            stop("не вдалося запустити odoo-bin: %s" % e)
        tb = [l for l in (p.stdout + p.stderr).splitlines() if re.search(r" (ERROR|CRITICAL) |Traceback", l)]
        for l in tb[:20]:
            print(l, file=sys.stderr)
        try:
            res = json.load(open(pout, encoding="utf-8"))
        except (OSError, ValueError):
            print(json.dumps({"errors": ["config_shell.py не записав результат (код %d)" % p.returncode]}, ensure_ascii=False))
            return 1
    cnt = res["counts"]
    rb_fail = [x["vp"] for x in res.get("readback", []) if x.get("status") == "FAIL"]
    summary = {"mode": mode, "created": cnt["created"], "updated": cnt["updated"], "unchanged": cnt["unchanged"],
               "manual": cnt["manual"], "skipped": cnt["skipped"], "diff": cnt.get("diff", 0), "missing": cnt.get("missing", 0),
               "errors": [x for x in res["log"] if str(x[1]).startswith(("ERROR", "blocked"))],
               "readback": {"checked": len(res.get("readback", [])), "failed": rb_fail} if mode == "readback" else None}
    print(json.dumps(summary, ensure_ascii=False))
    bad = cnt["errors"] or rb_fail or (mode == "compare" and (cnt.get("diff") or cnt.get("missing")))
    return 1 if bad or p.returncode != 0 else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    m = sub.add_parser("modules"); m.add_argument("--db", required=True); m.add_argument("--modules", required=True)
    s = sub.add_parser("shell"); s.add_argument("--db", required=True); s.add_argument("--script", required=True)
    r = sub.add_parser("rpc"); r.add_argument("--db", required=True); r.add_argument("--plan", required=True)
    r.add_argument("--dry-run", action="store_true")
    # C-00 (адаптер до формату package/config/: manifest.yaml format 2, vp-map.yaml, data/*.yaml) -- див. README «Адаптер конфіг-пакета»
    c = sub.add_parser("config"); c.add_argument("--db", required=True); c.add_argument("--config", required=True)
    c.add_argument("--answers", required=True); c.add_argument("--mode", dest="cfg_mode", choices=["apply", "compare", "readback"], default="apply")
    c.add_argument("--out", help="JSON з повним результатом (лог пунктів, read-back)")
    p = sub.add_parser("plan"); p.add_argument("--config", required=True); p.add_argument("--answers", required=True)
    p.add_argument("--out", help="plan.json (відповіді, preflight, модулі, пункти даних)"); p.add_argument("--db", default=None)
    a = ap.parse_args()
    load_env_local()
    if a.mode == "plan":
        return cmd_config(a)
    guard_db(a.db)
    if a.mode != "rpc":  # C-00: як guard_db у _common.sh -- PGHOST (типово localhost) має бути в ODOO_ALLOWED_HOSTS
        allowed = [h.strip() for h in os.environ.get("ODOO_ALLOWED_HOSTS", "").replace(" ", ",").split(",") if h.strip()]
        if os.environ.get("PGHOST", "localhost") not in allowed:
            stop("сервер БД '%s' не в ODOO_ALLOWED_HOSTS; відмова" % os.environ.get("PGHOST", "localhost"))
    if a.mode == "modules":
        for x in a.modules.split(","):
            if not MOD_OK.fullmatch(x):
                stop("недопустиме ім'я модуля '%s'" % x)
        return run_logged(odoo_base() + ["-d", a.db, "-u", a.modules, "--stop-after-init", "--log-level=warn"], a.db, mods=a.modules.split(","))
    if a.mode == "shell":
        try:
            src = open(a.script, encoding="utf-8").read()
        except OSError as e:
            stop("не вдалося прочитати --script: %s" % e)
        return run_logged(odoo_base("shell") + ["-d", a.db, "--no-http", "--log-level=warn"], a.db, stdin=src)
    if a.mode in ("config", "plan"):
        return cmd_config(a)
    return cmd_rpc(a)


if __name__ == "__main__":
    sys.exit(main())

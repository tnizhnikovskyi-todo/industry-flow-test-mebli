#!/usr/bin/env python3
r"""Покриття «налаштування довідників» (таблиця (г) INDEX.md) — перелік будується з КОДУ td_*, не з пам'яті.

Запуск з кореня репо:
  python3 -I package/docs/user-guide/reference/check_setup.py --addons package/addons \
      --index package/docs/user-guide/INDEX.md --setup package/docs/user-guide/setup.md [--list] [--json]

Що збирає з коду (крім td_mebli_demo, td_*_elearning, tests/, migrations/):
  F — кожне поле `fields.*`, яке клас td_* додає до НЕ td-моделі (`_inherit` без власного `_name`), у т. ч. до
      `res.config.settings`; підпис — переклад uk.po модуля (field_description), інакше `string` з коду.
  M — кожна власна постійна модель td_* (`models.Model`, не Abstract/Transient). Модель, дія якої висить у меню під
      «Налаштування» (parent з `config`/`configuration` у xmlid) — обов'язково «довідник».
  P — кожен системний параметр `ir.config_parameter` з префіксом `td_`, який читає чи пише код td_* (`get_param('…')`,
      `config_parameter='…'`, константи `PARAM_* = '…'`): рядок з моделлю `ir.config_parameter` і ключем у «Технічна назва».
  V — кожна стандартна модель, подання якої (`inherit_id` на подання не td_*) розширює td_*: має бути названа
      в setup.md технічною назвою в зворотних лапках.
Звіряє з таблицею «## Покриття: налаштування довідників (г)» в INDEX.md:
  | Форма (модель) | Поле / довідник (UI) | Технічна назва | Модуль | Вид | Розділ |
  Форма — містить `модель`; Технічна назва — `поле` (для F) або `модель` (для M); Розділ — «setup.md § <заголовок>»
  (кілька — через «;»), заголовок має існувати в setup.md (## або ###).
Пропуск = елемент F/M без рядка; зайвий рядок = рядок без елемента в коді (застаріле); довідник під «Налаштування»,
  позначений не «довідник»; розділ, якого немає; V-модель без згадки; зображення setup.md без файлу.
Вихід: JSON [{id,status,msg}] (--json) або текст; код 1, якщо є FAIL. --list друкує перелік F/M/V (для складання таблиці).
"""
import argparse, ast, json, os, re, sys
import xml.etree.ElementTree as ET

SKIP_MOD = re.compile(r"^(td_mebli_demo|td_.*_elearning)$")
CONFIG_PARENT = re.compile(r"config", re.I)
IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def po_labels(path):
    """{(model_us, field): msgstr} з field_description uk.po."""
    out = {}
    if not os.path.exists(path):
        return out
    refs, msgid, msgstr, cur = [], None, None, None
    def flush():
        if refs and msgstr:
            for r in refs:
                m = re.match(r"model:ir\.model\.fields,field_description:[\w]+\.field_(\w+?)__(\w+)$", r)
                if m:
                    out[(m.group(1), m.group(2))] = msgstr
    for ln in open(path, encoding="utf-8").read().splitlines() + [""]:
        if ln.startswith("#:"):
            if msgstr is not None:
                flush(); refs, msgid, msgstr = [], None, None
            refs += ln[2:].split()
        elif ln.startswith("msgid "):
            msgid, cur = ast.literal_eval(ln[6:]), "id"
        elif ln.startswith("msgstr "):
            msgstr, cur = ast.literal_eval(ln[7:]), "str"
        elif ln.startswith('"') and cur == "str" and msgstr is not None:
            msgstr += ast.literal_eval(ln)
        elif ln.startswith('"') and cur == "id" and msgid is not None:
            msgid += ast.literal_eval(ln)
        elif not ln.strip():
            flush(); refs, msgid, msgstr, cur = [], None, None, None
    return out


def field_string(call):
    for kw in call.keywords:
        if kw.arg == "string" and isinstance(kw.value, ast.Constant):
            return kw.value.value
    kind = call.func.attr
    pos = {"Many2one": 1, "One2many": 2, "Many2many": 4, "Selection": 1}.get(kind, 0)
    if len(call.args) > pos and isinstance(call.args[pos], ast.Constant) and isinstance(call.args[pos].value, str):
        return call.args[pos].value
    return None


def scan(addons):
    F, M = [], []
    for mod in sorted(os.listdir(addons)):
        mdir = os.path.join(addons, mod)
        if not mod.startswith("td_") or SKIP_MOD.match(mod) or not os.path.isdir(mdir):
            continue
        labels = po_labels(os.path.join(mdir, "i18n", "uk.po"))
        for dp, dns, fs in os.walk(mdir):
            dns[:] = [d for d in dns if d not in ("tests", "migrations", "static", "__pycache__")]
            for f in sorted(fs):
                if not f.endswith(".py"):
                    continue
                tree = ast.parse(open(os.path.join(dp, f), encoding="utf-8").read())
                for c in ast.walk(tree):
                    if not isinstance(c, ast.ClassDef):
                        continue
                    base = {getattr(b, "attr", getattr(b, "id", "")) for b in c.bases}
                    name, inh, fl = None, [], []
                    for s in c.body:
                        if not (isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name)):
                            continue
                        k, v = s.targets[0].id, s.value
                        if k == "_name" and isinstance(v, ast.Constant):
                            name = v.value
                        elif k == "_inherit":
                            inh = [v.value] if isinstance(v, ast.Constant) else [e.value for e in getattr(v, "elts", []) if isinstance(e, ast.Constant)]
                        elif isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and getattr(v.func.value, "id", "") == "fields":
                            kws = {kw.arg for kw in v.keywords}
                            fl.append((k, v.func.attr, field_string(v), bool(kws & {"compute", "related"})))
                    if name and name not in inh:
                        if name.startswith("td.") and "Model" in base and not ({"AbstractModel", "TransientModel"} & base):
                            M.append({"model": name, "module": mod, "file": os.path.relpath(os.path.join(dp, f), addons)})
                        continue
                    model = name or (inh[0] if inh else None)
                    if not model or model.startswith("td.") or model.startswith("td_") or model.startswith("report."):
                        continue
                    for fname, ftype, st, comp in fl:
                        us = model.replace(".", "_")
                        F.append({"model": model, "field": fname, "module": mod, "type": ftype, "computed": comp,
                                  "label": labels.get((us, fname)) or st or fname, "label_en": st or fname})
    # одне поле може оголошуватись у кількох модулях (selection_add, перевизначення) — лишаємо оголошення з власним
    # `string` (модуль, що поле створює), інакше перше
    F2, pos = [], {}
    for x in F:
        k = (x["model"], x["field"])
        if k not in pos:
            pos[k] = len(F2); F2.append(x)
        elif F2[pos[k]]["label_en"] == x["field"] and x["label_en"] != x["field"]:
            F2[pos[k]] = x
    seenm, M2 = set(), []
    for x in M:
        if x["model"] not in seenm:
            seenm.add(x["model"]); M2.append(x)
    return F2, M2


PARAM_RE = re.compile(r"""(?:get_param\(\s*|config_parameter\s*=\s*|\bPARAM_[A-Z_]+\s*=\s*)['"](td_[a-z0-9_]*\.[a-z0-9_.]+)['"]""")


def scan_params(addons):
    """P: ключі ir.config_parameter td_* з коду модулів (без tests/, migrations/)."""
    P = {}
    for mod in sorted(os.listdir(addons)):
        mdir = os.path.join(addons, mod)
        if not mod.startswith("td_") or SKIP_MOD.match(mod) or not os.path.isdir(mdir):
            continue
        for dp, dns, fs in os.walk(mdir):
            dns[:] = [d for d in dns if d not in ("tests", "migrations", "static", "__pycache__")]
            for f in sorted(fs):
                if f.endswith(".py"):
                    for key in PARAM_RE.findall(open(os.path.join(dp, f), encoding="utf-8").read()):
                        P.setdefault(key, mod)
    return P


def xml_files(addons):
    for mod in sorted(os.listdir(addons)):
        mdir = os.path.join(addons, mod)
        if not mod.startswith("td_") or SKIP_MOD.match(mod) or not os.path.isdir(mdir):
            continue
        for dp, dns, fs in os.walk(mdir):
            dns[:] = [d for d in dns if d not in ("tests", "static", "i18n", "__pycache__")]
            for f in fs:
                if f.endswith(".xml"):
                    try:
                        yield mod, ET.parse(os.path.join(dp, f)).getroot()
                    except ET.ParseError:
                        continue


def scan_xml(addons):
    """V: стандартні моделі з успадкованими поданнями; config-моделі: дія з меню під *config*."""
    V, actions, menus = {}, {}, []
    for mod, root in xml_files(addons):
        for rec in root.iter("record"):
            mdl = rec.get("model")
            fields = {f.get("name"): f for f in rec.findall("field")}
            if mdl == "ir.ui.view" and "inherit_id" in fields and "model" in fields:
                ref = fields["inherit_id"].get("ref", "")
                vm = (fields["model"].text or "").strip()
                if ref and not ref.startswith("td_") and "." in ref and not vm.startswith("td."):
                    V.setdefault(vm, set()).add(mod)
            if mdl == "ir.actions.act_window" and "res_model" in fields:
                actions[rec.get("id")] = (fields["res_model"].text or "").strip()
        for mi in root.iter("menuitem"):
            menus.append((mi.get("parent", ""), mi.get("action", "")))
    cfg = set()
    for parent, act in menus:
        if act and CONFIG_PARENT.search(parent):
            m = actions.get(act.split(".")[-1])
            if m:
                cfg.add(m)
    return V, cfg


def headings(text):
    return {re.sub(r"\s+", " ", h.strip()).lower() for h in re.findall(r"(?m)^#{2,4}\s+(.+?)\s*$", text)}


def parse_table(index):
    m = re.search(r"(?ms)^##\s*Покриття:\s*налаштування довідників.*?$(.*?)(?=^##\s|\Z)", index)
    if not m:
        return None
    rows = []
    for ln in m.group(1).splitlines():
        if not ln.strip().startswith("|") or re.match(r"^\|\s*-", ln.strip()):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[0].startswith("Форма"):
            continue
        model = re.findall(r"`([a-z0-9_.]+)`", cells[0])
        tech = re.findall(r"`([a-z0-9_.]+)`", cells[2])
        rows.append({"model": model[0] if model else "", "tech": tech[0] if tech else "", "kind": cells[4].lower(),
                     "sections": cells[5], "raw": ln.strip()})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addons", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--setup", required=True)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    F, M = scan(a.addons)
    V, cfg = scan_xml(a.addons)
    P = scan_params(a.addons)
    if a.list:
        for x in sorted(F, key=lambda x: (x["model"], x["field"])):
            print(f"F\t{x['model']}\t{x['field']}\t{x['module']}\t{x['type']}\t{'comp' if x['computed'] else ''}\t{x['label']}")
        for x in M:
            print(f"M\t{x['model']}\t{x['module']}\t{'config' if x['model'] in cfg else ''}")
        for k in sorted(V):
            print(f"V\t{k}\t{','.join(sorted(V[k]))}")
        for k in sorted(P):
            print(f"P\tir.config_parameter\t{k}\t{P[k]}")
        return 0
    res = []
    add = lambda i, s, m="": res.append({"id": i, "status": s, "msg": m})
    index = open(a.index, encoding="utf-8").read() if os.path.exists(a.index) else ""
    setup = open(a.setup, encoding="utf-8").read() if os.path.exists(a.setup) else ""
    rows = parse_table(index)
    if rows is None:
        add("SU-table", "FAIL", "в INDEX немає таблиці «## Покриття: налаштування довідників (г)»")
        rows = []
    else:
        add("SU-table", "PASS", f"рядків {len(rows)}")
    have = {(r["model"], r["tech"]) for r in rows}
    missF = [f"{x['model']}.{x['field']}" for x in F if (x["model"], x["field"]) not in have]
    missM = [x["model"] for x in M if (x["model"], x["model"]) not in have]
    missP = [k for k in sorted(P) if ("ir.config_parameter", k) not in have]
    known = {(x["model"], x["field"]) for x in F} | {(x["model"], x["model"]) for x in M} | {("ir.config_parameter", k) for k in P}
    extra = [f"{r['model']}:{r['tech']}" for r in rows if (r["model"], r["tech"]) not in known]
    add("SU-fields", "FAIL" if missF else "PASS", f"полів у коді {len(F)}, без рядка {len(missF)}" + (": " + ", ".join(missF[:15]) if missF else ""))
    add("SU-models", "FAIL" if missM else "PASS", f"моделей td_* у коді {len(M)}, без рядка {len(missM)}" + (": " + ", ".join(missM) if missM else ""))
    add("SU-params", "FAIL" if missP else "PASS", f"системних параметрів td_* у коді {len(P)}, без рядка {len(missP)}" + (": " + ", ".join(missP) if missP else ""))
    add("SU-stale", "FAIL" if extra else "PASS", f"рядків без елемента в коді {len(extra)}" + (": " + ", ".join(extra[:10]) if extra else ""))
    badcfg = [m for m in sorted(cfg) if m.startswith("td.") and not any(r["model"] == m and r["tech"] == m and "довідник" in r["kind"] for r in rows)]
    add("SU-config", "FAIL" if badcfg else "PASS", f"моделей у меню «Налаштування» {len([m for m in cfg if m.startswith('td.')])}" + ("; не позначено «довідник»: " + ", ".join(badcfg) if badcfg else ""))
    hs = headings(setup)
    nosec = []
    for r in rows:
        secs = re.findall(r"setup\.md\s*§\s*([^;|]+)", r["sections"])
        if not secs:
            nosec.append(f"{r['model']}:{r['tech']} (немає «setup.md § …»)")
        for s in secs:
            if re.sub(r"\s+", " ", s.strip()).lower() not in hs:
                nosec.append(f"{r['model']}:{r['tech']} → «{s.strip()}»")
    add("SU-sections", "FAIL" if nosec else "PASS", f"посилань на розділи без заголовка в setup.md {len(nosec)}" + (": " + "; ".join(nosec[:10]) if nosec else ""))
    noview = [m for m in sorted(V) if f"`{m}`" not in setup]
    add("SU-forms", "FAIL" if noview else "PASS", f"стандартних моделей із поданнями, розширеними td_*: {len(V)}, не названо в setup.md {len(noview)}" + (": " + ", ".join(noview) if noview else ""))
    base = os.path.dirname(a.setup)
    broken = [r for r in IMG.findall(setup) if not os.path.isfile(os.path.join(base, r))]
    add("SU-img", "FAIL" if broken or not IMG.findall(setup) else "PASS", f"кадрів у setup.md {len(IMG.findall(setup))}" + ("; немає файлу: " + ", ".join(broken[:8]) if broken else ""))
    gaps = len(missF) + len(missM) + len(missP)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for r in res:
            print(f"{r['status']:5} {r['id']}: {r['msg']}")
        print(f"Підсумок: полів {len(F)}, моделей {len(M)}, параметрів {len(P)}, форм {len(V)}; пропусків {gaps}")
    return 1 if any(r["status"] == "FAIL" for r in res) else 0


if __name__ == "__main__":
    sys.exit(main())

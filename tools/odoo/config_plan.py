"""C-00 (тест «меблі»): answers.yaml + package/config/ (manifest.yaml format 2, vp-map.yaml, data/*.yaml) -> plan.
Відповіді = default схеми package/templates/answers.yaml, поверх них -- файл відповідей (повний, як package/demo/answers.yaml).
preflight -- правила manifest.yaml `preflight` (вирази над `a`); модулі -- edition_profiles[edition].modules за `when`.
Вирази беруться лише з файлів репо пакета (довірені); потребує PyYAML (системний python3). Використовує apply.py plan|config."""
import os
import re

import yaml


def _when_ok(expr, a):
    if not expr:
        return True
    e = re.sub(r"(VP-\d+|edition|contract_mode)", lambda m: "a['%s']" % m.group(1), expr)
    e = re.sub(r"\btrue\b", "True", re.sub(r"\bfalse\b", "False", e))
    return bool(eval(e, {"__builtins__": {}}, {"a": a}))  # noqa: S307 -- вираз з manifest.yaml репо


def build(cfg_dir, answers_path):
    cfg_dir = os.path.abspath(cfg_dir)
    tdir = os.path.join(os.path.dirname(cfg_dir), "templates")
    schema = yaml.safe_load(open(os.path.join(tdir, "answers.yaml"), encoding="utf-8"))
    a = {k: v.get("default") for k, v in schema.items() if isinstance(v, dict)}
    given = yaml.safe_load(open(answers_path, encoding="utf-8")) or {}
    unknown = sorted(set(given) - set(a))
    a.update(given)
    man = yaml.safe_load(open(os.path.join(cfg_dir, "manifest.yaml"), encoding="utf-8"))
    if man.get("format") != 2:
        raise SystemExit("FLOW_STOP: manifest.yaml format=%r (адаптер C-00 знає лише format 2)" % man.get("format"))
    pf = []
    for r in man.get("preflight", []):
        env = {"__builtins__": {}}
        if eval(r["when"], env, {"a": a}) and not eval(r["require"], env, {"a": a}):  # noqa: S307
            pf.append({"id": r["id"], "on_violation": r["on_violation"], "message": r["message"]})
    edition = a.get("edition") or "ce"
    mods = [m["name"] for m in man["edition_profiles"][edition]["modules"]
            if _when_ok(m.get("when"), a) and not m.get("auto_install")]
    data = []
    for f in man["data_files"]:
        for it in yaml.safe_load(open(os.path.join(cfg_dir, f), encoding="utf-8")) or []:
            it["_file"] = f
            data.append(it)
    vpmap = yaml.safe_load(open(os.path.join(cfg_dir, "vp-map.yaml"), encoding="utf-8"))
    return {"answers": a, "unknown_keys": unknown, "vpmap": vpmap, "data": data, "preflight": pf, "modules": mods,
            "edition": edition, "language": (man.get("install") or {}).get("language")}

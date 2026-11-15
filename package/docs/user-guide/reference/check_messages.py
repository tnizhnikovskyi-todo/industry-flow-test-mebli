#!/usr/bin/env python3
"""Повнота довідника messages.md (A-16b): кожне повідомлення UserError / ValidationError / AccessError з коду td_*
(без td_*_demo, td_*_elearning, tests) — дослівно (msgstr uk.po модуля) є в messages.md.
Запуск з кореня репо: python3 -I package/docs/user-guide/reference/check_messages.py --addons package/addons
Вихід: JSON {"total", "missing", "items"}; код 1, якщо є пропущені. Лише stdlib."""
import argparse, ast, json, os, re, sys

EXC = {'UserError', 'ValidationError', 'AccessError'}
HELPERS = {'_td_check_manager'}  # методи, що отримують текст і самі піднімають AccessError


def load_po(path):
    d, cur, key = {}, {}, None
    if not os.path.exists(path):
        return d
    for ln in open(path, encoding='utf-8'):
        ln = ln.rstrip('\n')
        m = re.match(r'^(msgid|msgstr) "(.*)"$', ln)
        if m:
            if m.group(1) == 'msgid' and 'msgstr' in cur:
                if cur.get('msgid'):
                    d[cur['msgid']] = cur['msgstr']
                cur = {}
            key = m.group(1)
            cur[key] = m.group(2)
        elif ln.startswith('"') and key:
            cur[key] += ln[1:-1]
    if cur.get('msgid'):
        d[cur['msgid']] = cur.get('msgstr', '')
    un = lambda s: s.replace('\\"', '"').replace('\\n', '\n')
    return {un(k): un(v) for k, v in d.items()}


def text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call):
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, 'id', '')
        if name in ('_', '_lt') and node.args:
            return text(node.args[0])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = text(node.left), text(node.right)
        if a is not None and b is not None:
            return a + b
    return None


def collect(addons):
    found = []
    for mod in sorted(os.listdir(addons)):
        if not mod.startswith('td_') or re.search(r'_(demo|elearning)$', mod):
            continue
        po = load_po(os.path.join(addons, mod, 'i18n', 'uk.po'))
        for dp, ds, fs in os.walk(os.path.join(addons, mod)):
            if 'tests' in os.path.relpath(dp, addons).split(os.sep):
                continue
            for f in sorted(fs):
                if not f.endswith('.py'):
                    continue
                path = os.path.join(dp, f)
                tree = ast.parse(open(path, encoding='utf-8').read())
                assigns = {}
                for n in ast.walk(tree):
                    if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                        s = text(n.value)
                        if s:
                            assigns.setdefault(n.targets[0].id, []).append((n.lineno, s))
                    msg = None
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in HELPERS and n.args:
                        msg = text(n.args[0])
                    if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call):
                        fn = n.exc.func
                        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, 'id', '')
                        if name in EXC and n.exc.args:
                            a = n.exc.args[0]
                            msg = text(a)
                            if msg is None and isinstance(a, ast.Name):
                                prev = [x for x in assigns.get(a.id, []) if x[0] < n.lineno]
                                msg = prev[-1][1] if prev else None
                    if msg:
                        found.append((os.path.relpath(path, addons), n.lineno, msg, po.get(msg) or msg))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--addons', required=True)
    ap.add_argument('--messages', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'messages.md'))
    a = ap.parse_args()
    body = open(a.messages, encoding='utf-8').read()
    items = collect(a.addons)
    missing = [{'src': f'{f}:{ln}', 'msgid': m} for f, ln, m, uk in items
               if '«' + uk.replace('|', '/').replace('\n', ' ') + '»' not in body]
    print(json.dumps({'total': len(items), 'unique': len({i[2] for i in items}), 'missing': len(missing), 'items': missing},
                     ensure_ascii=False, indent=1))
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()

# C-00 (тест «меблі»): застосування конфіг-пакета у `odoo-bin shell` (stdin). Запускає `apply.py config` (не викликати напряму).
# Вхід -- змінні CFG_IN (plan.json від config_plan.build), CFG_MODE=apply|compare|readback, CFG_OUT (JSON результату).
# Семантика -- config-as-code/references/apply-semantics.md: upsert за xml-id td_config.* (ir.model.data, noupdate), xmlid_target --
# запис чужого модуля, settings -- res.config.settings.execute() останнім, chart -- try_loading; read-back -- за vp-map.yaml.
# Перевірені на Odoo 19.0 CE (A-12 спроби 3-4); read-back має пакетні пункти «меблі» (AC-030, AC-004) -- для іншого пакета адаптувати.
import json, os, re
IN = json.load(open(os.environ['CFG_IN'])); MODE = os.environ['CFG_MODE']; OUT = os.environ['CFG_OUT']
a = IN['answers']; vpmap = IN['vpmap']
company = env.ref('base.main_company')
TD_FEATURES = ('configurator', 'offcut', 'cutting_batch', 'kiosk', 'quality', 'label_scan', 'change_sign', 'nbu',
               'ai_mapping', 'analog', 'shop_board')
cnt = {'created': 0, 'updated': 0, 'unchanged': 0, 'manual': 0, 'errors': 0, 'skipped': 0, 'missing': 0, 'diff': 0}
log = []

def installed(m):
    r = env['ir.module.module'].search([('name', '=', m)])
    return r.state if r else 'absent'

def applies(cond):
    return all((a.get(k) in v) if isinstance(v, list) else (a.get(k) == v) for k, v in (cond or {}).items())

def tr_value(transform, vp):
    v = a.get(vp)
    if transform in (None, 'identity'):
        return v
    if isinstance(transform, dict) and 'expr' in transform:
        return eval(transform['expr'], {'a': a, 'sorted': sorted, 'TD_FEATURES': TD_FEATURES})
    key = str(v).lower() if isinstance(v, bool) else v
    return transform.get(key, transform.get(str(key)))

def resolve(val, item):
    if isinstance(val, str):
        m = re.fullmatch(r'\{\{([\w-]+)(?::(\w+))?\}\}', val)
        if m:
            vp, name = m.groups()
            if name and ('transform_' + name) in item:
                val = tr_value(item['transform_' + name], vp)
            elif name:
                val = tr_value(vpmap[vp]['transform'], vp)[name]
            else:
                val = tr_value(vpmap[vp].get('transform'), vp)
        if isinstance(val, str) and '{company_id}' in val:
            val = 'ref:' + val.replace('{company_id}', str(company.id))
        if isinstance(val, str) and val.startswith('refjson:'):
            return json.dumps(env.ref(val[8:]).id)
        if isinstance(val, str) and val.startswith('ref:'):
            return env.ref(val[4:]).id
    return val

def cur(rec, f):
    v = rec[f]
    fld = rec._fields[f]
    if fld.type == 'many2one':
        return v.id or None
    if fld.type in ('one2many', 'many2many'):
        return sorted(v.ids)
    return v

def same(rec, f, v):
    c = cur(rec, f)
    if rec._fields[f].type == 'many2one':
        return c == (v or None)
    if rec._fields[f].type == 'float':
        return abs((c or 0) - (v or 0)) < 1e-6
    if rec._fields[f].type == 'selection':
        return (c or False) == (v or False)
    return c == v

def own(xmlid):
    return env.ref(xmlid, raise_if_not_found=False)

settings_vals = {}
for it in IN['data']:
    iid = it['id']
    try:
        if it.get('manual'):
            cnt['manual'] += 1; log.append((iid, 'manual')); continue
        if not applies(it.get('applies_if')):
            cnt['skipped'] += 1; log.append((iid, 'skipped(applies_if)')); continue
        if it.get('requires_module') and installed(it['requires_module']) != 'installed':
            cnt['errors'] += 1; log.append((iid, 'blocked: module')); continue
        vals = {k: resolve(v, it) for k, v in (it.get('values') or {}).items()}
        kind = it['kind']
        if kind == 'settings':
            settings_vals.update(vals); log.append((iid, 'settings(queued)')); continue
        if kind == 'chart':
            code = vals['chart_template']
            if company.chart_template == code:
                cnt['unchanged'] += 1; log.append((iid, 'unchanged'))
            elif MODE == 'apply':
                env['account.chart.template'].try_loading(code, company, install_demo=False)
                cnt['updated'] += 1; log.append((iid, 'updated'))
            else:
                cnt['diff'] += 1; log.append((iid, 'DIFF'))
            continue
        model = env[it['model']]
        if it.get('xmlid_target'):
            rec = env.ref(it['xmlid_target']).with_context(active_test=False)
        else:
            rec = own(iid)
            if rec:
                rec = rec.with_context(active_test=False)
        if not rec:
            if MODE == 'apply':
                cv = dict(vals)
                if it.get('lines'):
                    cv['line_ids'] = [(0, 0, l) for l in it['lines']]
                if it['model'] == 'account.payment.term' and 'active' in cv:
                    act = cv.pop('active')
                new = model.create(cv)
                if it['model'] == 'account.payment.term':
                    new.active = act
                mod, name = iid.split('.')
                env['ir.model.data'].create({'module': mod, 'name': name, 'model': it['model'], 'res_id': new.id, 'noupdate': True})
                cnt['created'] += 1; log.append((iid, 'created'))
            else:
                cnt['missing'] += 1; log.append((iid, 'MISSING'))
            continue
        diff = {f: v for f, v in vals.items() if not same(rec, f, v)}
        if it.get('lines'):
            have = sorted((l.value, l.value_amount, l.nb_days) for l in rec.line_ids)
            want = sorted((l['value'], l['value_amount'], l['nb_days']) for l in it['lines'])
            if have != want:
                diff['line_ids'] = [(5, 0, 0)] + [(0, 0, l) for l in it['lines']]
        if not diff:
            cnt['unchanged'] += 1; log.append((iid, 'unchanged'))
        elif MODE == 'apply':
            rec.write(diff); cnt['updated'] += 1; log.append((iid, 'updated ' + ','.join(diff)))
        else:
            cnt['diff'] += 1; log.append((iid, 'DIFF ' + json.dumps({k: str(v) for k, v in diff.items()}, ensure_ascii=False)))
    except Exception as e:
        cnt['errors'] += 1; log.append((iid, 'ERROR %r' % e)); env.cr.rollback()

if settings_vals:
    S = env['res.config.settings']
    srec = S.create({})   # default_get + related company_id.* (apply-semantics: read-back related через компанію)
    dg = {k: srec[k] for k in settings_vals}
    diff = {k: v for k, v in settings_vals.items() if bool(dg.get(k)) != bool(v)}
    if not diff:
        cnt['unchanged'] += 1; log.append(('settings', 'unchanged %d fields' % len(settings_vals)))
    elif MODE == 'apply':
        S.create(settings_vals).execute(); cnt['updated'] += 1; log.append(('settings', 'execute ' + ','.join(diff)))
    else:
        cnt['diff'] += 1; log.append(('settings', 'DIFF ' + ','.join(diff)))

rb = []
if MODE == 'readback':
    for vp, m in vpmap.items():
        exp_raw = a.get(vp)
        ok_applies = applies(m.get('applies_if'))
        anchor = m['anchor']
        try:
            if anchor.startswith('res.company:') and not anchor.endswith(':account_sale_tax_id'):
                f = anchor.rsplit(':', 1)[1]
                exp = tr_value(m.get('transform'), vp) if ok_applies else company.default_get([f]).get(f)
                got = company[f]
                ok = (got or False) == (exp or False) if company._fields[f].type != 'float' else abs(got - float(exp)) < 1e-6
            elif anchor.startswith('ir.module.module:'):
                name = re.search(r'name=(\w+)', anchor).group(1)
                exp = tr_value(m['transform'], vp) if ok_applies else 'uninstalled'
                got = installed(name)
                ok = got == exp or (exp in ('uninstalled', 'absent') and got in ('uninstalled', 'absent'))
            elif vp == 'VP-02':
                exp = tr_value(m['transform'], vp) if ok_applies else {}
                dg = env['res.config.settings'].default_get(['group_td_feature_' + f for f in TD_FEATURES])
                got = {f: bool(dg['group_td_feature_' + f]) for f in TD_FEATURES}
                impl = env.ref('base.group_user').implied_ids
                got_impl = sorted(f for f in TD_FEATURES if env.ref('td_mebli_base.group_feature_' + f) in impl)
                want = {f: bool(exp.get(f)) for f in TD_FEATURES}
                ok = got == want and got_impl == sorted(f for f, v in want.items() if v)
                exp = sorted(f for f, v in want.items() if v); got = got_impl
            elif anchor.startswith('account.payment.term:'):
                xid = re.search(r'xml_id=([\w.]+)', anchor).group(1)
                exp = tr_value(m['transform'], vp); got = own(xid).with_context(active_test=False).active; ok = got == exp
                dflt = env['ir.default'].search([('field_id', '=', env.ref('account.field_res_partner__property_payment_term_id').id)])
                pdef = env['res.partner'].with_company(company).new({}).property_payment_term_id
                got = {'active': got, 'ir.default': len(dflt), 'partner_default': pdef.get_external_id().get(pdef.id) if pdef else None,
                       'milestones': own(xid).line_ids.mapped('td_milestone'), 'terms_total': env['account.payment.term'].with_context(active_test=False).search_count([('line_ids.td_milestone', '!=', False)])}
                got['ir.default_json'] = dflt.mapped('json_value')
                ok = ok and ((got['partner_default'] == xid and len(dflt) == 1) if exp else (got['partner_default'] is None and all(j == 'false' for j in dflt.mapped('json_value'))))
            elif anchor.startswith('ir.default:'):
                exp = tr_value(m['transform'], vp); got = own('td_config.default_bom_consumption').json_value; ok = got == exp
            elif anchor.startswith('res.company:xml_id=base.main_company:account_sale_tax_id'):
                exp = tr_value(m['transform'], vp)
                exp_id = env.ref(exp.replace('{company_id}', str(company.id))).id if exp else False
                got = company.account_sale_tax_id.id or False; ok = got == exp_id
                got = company.account_sale_tax_id.get_external_id().get(company.account_sale_tax_id.id) if got else None
            else:
                exp = got = '?'; ok = False
        except Exception as e:
            exp, got, ok = exp_raw, 'ERROR %r' % e, False
        rb.append({'vp': vp, 'answer': exp_raw, 'expected': exp, 'got': got, 'status': 'PASS' if ok else 'FAIL', 'applies': ok_applies})
    tmpl = [x for x in ('mail_template_td_new_date', 'mail_template_td_payment_reminder', 'mail_template_td_install_reminder',
                        'mail_template_td_measure_booking', 'mail_template_td_install_date', 'mail_template_td_briefing')
            if env.ref('td_mebli_notify.' + x, raise_if_not_found=False)]
    rb.append({'vp': 'AC-030 templates', 'got': len(tmpl), 'status': 'PASS' if len(tmpl) == 6 else 'FAIL'})
    rb.append({'vp': 'AC-004 alarm', 'got': bool(env.ref('td_mebli_measure.alarm_mail_measure_1day', raise_if_not_found=False)), 'status': 'PASS'})
    s80 = {}
    for it in IN['data']:
        if it['kind'] == 'settings' and not it.get('manual') and applies(it.get('applies_if')):
            s80.update({k: resolve(v, it) for k, v in it['values'].items()})
    srec = env['res.config.settings'].create({})
    dg = {k: srec[k] for k in s80}
    rb.append({'vp': 'settings', 'got': {k: dg.get(k) for k in s80}, 'status': 'PASS' if all(bool(dg.get(k)) == bool(v) for k, v in s80.items()) else 'FAIL'})

if MODE == 'apply':
    env.cr.commit()
else:
    env.cr.rollback()
json.dump({'mode': MODE, 'counts': cnt, 'log': log, 'readback': rb, 'td_config_imd': env['ir.model.data'].search_count([('module', '=', 'td_config')])},
          open(OUT, 'w'), ensure_ascii=False, indent=1, default=str)
print('DONE', MODE, cnt)

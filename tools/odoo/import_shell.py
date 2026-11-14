# C-00 (тест «меблі»): імпорт CSV майстер-даних у `odoo-bin shell` (stdin). Запускає import.sh (не викликати напряму).
# Канал -- ORM `Model.load(fields, rows)` (той самий, що base_import «Імпорт» в інтерфейсі; заголовки CSV -- як у base_import:
# `id`, `<поле>`, `<поле>/id`). Перевірено на Odoo 19.0 CE (A-13 спроби 1-4). Кожен файл -- окрема транзакція (commit);
# перша помилка -- rollback файла і стоп. Вхід: IMP_FILES (шляхи через \n, модель -- з імені `NN_<model>.csv` або IMP_MODEL),
# IMP_OUT -- JSON результату.
import csv, json, os
files = [f for f in os.environ['IMP_FILES'].split('\n') if f]
forced = os.environ.get('IMP_MODEL') or None
res = []
for f in files:
    model = forced or os.path.basename(f).split('_', 1)[1][:-4]
    with open(f, encoding='utf-8', newline='') as fh:
        rows = list(csv.reader(fh))
    hdr, data = rows[0], rows[1:]
    try:
        if model not in env:
            raise ValueError('модель %s відсутня в базі' % model)
        r = env[model].with_context(tracking_disable=True).load(hdr, data)
        errs = [m.get('message') for m in r.get('messages', []) if m.get('type') == 'error']
        warn = [m.get('message') for m in r.get('messages', []) if m.get('type') != 'error']
        ids = [i for i in (r.get('ids') or []) if i]
        ok = not errs and len(ids) == len(data)
        res.append({'file': f, 'model': model, 'rows': len(data), 'ids': len(ids), 'errors': errs[:5], 'warnings': warn[:3], 'ok': ok})
        if not ok:
            env.cr.rollback()
            break
        env.cr.commit()
    except Exception as e:  # noqa: BLE001
        env.cr.rollback()
        res.append({'file': f, 'model': model, 'rows': len(data), 'ids': 0, 'errors': [repr(e)[:300]], 'ok': False})
        break
json.dump({'results': res}, open(os.environ['IMP_OUT'], 'w'), ensure_ascii=False, indent=1)

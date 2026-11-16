# Звіт кроку A-11 (fix6: BAS виключено з пакета; «Виключити для» технолога; іконка «Керівник») — тестовий режим

Наряд: `tests/naryad/A-11-fix6.yaml` (`params.mode: fix`). Гілка `flow/A-11-fix6-test` від `origin/flow/A-17-7-test` @ `2733ccc` (worktree `/home/user/wt-bas2`).
Підстави — рішення власника 2026-11-16 (передано менеджерською сесією): «BAS прибираємо взагалі» (рядки 55–56 `flow/decisions.md` — вносить головна сесія);
технолог — «Виключити для», видалення — лише адміністратор, технолог архівує (рядок 57 — вносить головна сесія); нова іконка «Керівник». `flow/decisions.md` у цій гілці не змінювався.
Скіл `odoo19-mvp-build:code-dev` у сесії недоступний (скіл організації) — зміни зробила сесія. Доставка — окремий каталог `/home/user/odoo19/delivery-bas2`
(конфіги `odoo-tools-bas2{,-light,-B,-old}.conf`, порти 8296–8299).

```yaml
run: {step: A-11, scope: package/mebli, attempt: fix6, started: 2026-11-16T13:00:00Z, finished: 2026-11-16T13:35:00Z}
result: done
pr: "PR не створено (наказ сесії: PR робить головна сесія); гілка flow/A-11-fix6-test"
skill_versions: {"odoo19-mvp-build:code-dev": "недоступний (скіл організації) — виконала сесія"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 300000, tokens_out: 30000, agent_hours: 0.6}   # оцінка
cost_estimated: true
base_sha: 2733ccc
checks:
  - {id: deferred-removed, status: PASS, msg: "git rm -r package/deferred (39 файлів: td_mebli_bas, td_mebli_attendance, td_mebli_migration/{scripts/convert_bas.py, tests/test_convert_bas.py}, master-data/td/19b…21b + README, README) — каталогу немає; код лише в історії git (f48d954, 2733ccc)"}
  - {id: old-bases, status: PASS, msg: "td_mebli_base 19.0.1.1.4 migrations/19.0.1.1.4/end-migrate.py (AI-42): td_mebli_bas/td_mebli_attendance → «to remove», Odoo видаляє їх у тому ж оновленні; без коду — скрипт скидає таблиці td_mebli_bas_*. Стара база test-mebli-bas2-oldtpl (код 2733ccc + обидва модулі, профіль A, 49 модулів) → копії: (1) оновлення з доставкою без коду BAS, (2) зі старою доставкою, де каталоги td_mebli_bas/_attendance лишились (install.sh їх не видаляє) — обидва install.sh --update RC 0 без ERROR; модулі uninstalled, ir.model.data 0, ir.model td.mebli.bas* 0, полів/колонок td_bas_* 0, таблиць 0, подань з td_bas/action_td_send_bas 0; get_views форм/списків sale.order, res.partner, product.template/product, hr.employee, account.move/payment, res.config.settings, mrp.production, project.task — OK. Без скидання таблиць (перша версія скрипта) у випадку (1) лишались 3 таблиці td_mebli_bas_* — виправлено"}
  - {id: helper, status: PASS, msg: "td_mebli_install 19.0.1.1.8: _td_cancel_pay_marks (кликав лише виключений AC-042) і test_ac_021_cancel_marks_helper прибрано; ручні позначки AC-021 і «Скасовано» — без змін"}
  - {id: texts, status: PASS, msg: "td_mebli_migration 19.0.1.1.8 (міграція 1.1.7, дані, тест test_ac_089_no_steps_of_excluded_modules — «виключено»), td_mebli_sale 19.0.1.1.5 (докстрінг історичної міграції 1.1.0 без слова BAS); grep -wiE 'BAS|BAF' package/addons — лише AC-COVERAGE.md (банер «виключено» + рядки AC-039…042, 078, 109 + історичні розділи)"}
  - {id: ac-coverage, status: PASS, msg: "AC-COVERAGE.md: банер «виключено рішенням власника 2026-11-16»; AC-039…042, 078, 109 — «виключено», тести «—»; AC-089 без тесту конвертора BAS; AC-021 без хелпера; рядки моделей/полів td.mebli.bas.*, td_bas_* і структури td_mebli_bas прибрано; підсумок done 113 + виключено 6"}
  - {id: d24-exclusions, status: PASS, msg: "td_mebli_mrp 19.0.1.1.7: ACL product.template.attribute.exclusion technologist 1/1/1/0; product.product._unlink_or_archive — для технолога без права unlink варіанти архівуються (AI-43). Що зачіпає збереження виключення з форми значення: product.template.attribute.exclusion create/write → product.template._create_variant_ids() → product.product create/archive/unlink (Odoo 19 product/models/product_template_attribute_exclusion.py, product_template.py:861). Тест test_d24_technologist_keeps_exclusions_and_archives (Form значення → вкладка «Виключити для» → збереження; зміна; unlink — AccessError; виключення між атрибутами з варіантами — варіант архівовано, 4 → 3 активних, 0 видалено; архівування операції, специфікації, робочого центру, товару — PASS, їх unlink — AccessError; адміністратор видаляє виключення) і оновлений test_d23 (рядок атрибута технолог «прибирає» → архівується) — 6/6 PASS (TestD20Technologist, база test-mebli-bas2-up1); повний прогін — A-14-9"}
  - {id: icon, status: PASS, msg: "td_mebli_dashboard 19.0.1.1.4: static/description/icon.svg 50×50 (циферблат-спідометр з 3 сегментів #1AD3BB/#FBB945/#F86126, стрілка й вісь #005E7A/#FC868B, основа #985184; без стовпчиків) + icon.png 100×100 (рендер Chromium, прозорий фон); web_icon меню не змінювався (web_icon_data в Odoo 19 не зберігається — береться з файла)"}
  - {id: lint, status: PASS, msg: "ruff (E,F,W,B,I) змінених .py: нових знахідок 0 (3 давні: I001 payment.py, I001/B017 test_g3.py)"}
  - {id: versions, status: PASS, msg: "+1 патч: base 1.1.4, install 1.1.8, migration 1.1.8, sale 1.1.5, mrp 1.1.7, dashboard 1.1.4"}
  - {id: tests-clean, status: PASS, msg: "чисті бази A/light/B — у A-14-9"}
  - {id: where-only, status: PASS, msg: "package/deferred/ (видалено), package/addons/{td_mebli_base,_install,_migration,_sale,_mrp,_dashboard}, AC-COVERAGE.md, AI-DECISIONS (AI-37/38 — «замінено», AI-39 — п.2 «вирішено рішенням власника», AI-42, AI-43), наряд, звіт"}
data_sources: ["repo:package/@2733ccc", "/home/user/odoo19/src (Odoo 19.0 CE: odoo/modules/loading.py крок 5, product/models/*)", "local:test-mebli-bas2-oldtpl, -up1, -up2"]
memo: |
  Рішення AI (власник — вето): AI-42 (міграцію для старих баз лишено — автоматичне видалення модулів BAS наприкінці оновлення td_mebli_base;
  дані кодів BAS не зберігаються — вивантажити до оновлення), AI-43 (технічні доповнення до рішення про «Виключити для»: варіанти архівуються,
  рядок атрибута архівується). Невпевнений: (1) реальну базу клієнта не перевірено (клієнтів немає) — лише синтетична стара база; (2) оновлення
  має зачепити td_mebli_base (оновлення всіх td_*), інакше міграція не запуститься — так у admin.md; (3) іконка: «Відвідування» Odoo теж має
  циферблат зі стрілкою (жовто-коричневий годинник) — наша — кольоровий напівкруглий спідометр на основі; на головному екрані owner/admin поруч
  не стоять (див. A-16b-6).
  Недовірені дані: інструкцій не виявлено. Odoo-mcp не використовувався.
observations: []
```

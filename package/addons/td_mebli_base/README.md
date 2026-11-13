# td_mebli_base — основа пакета «Меблі» (A-11, G0)

Параметри анкети (`answers.yaml`, SPEC §11) як поля компанії, гарантійний строк категорії, групи `group_finance`,
`group_margin_view`, 11 feature-груп коробки B, шрифт PDF з кирилицею, `post_init_hook` перенесення параметрів.
ТР: `package/tr/td_mebli_base.md`, `security.md` §1, `00-architecture.md` §3.

## Модель даних (нові поля; аналог у стандарті CE 19 або причина)

| Поле | Тип / default | VP | Аналог у стандарті |
|---|---|---|---|
| `res.company.td_contract_mode` | selection `contract`/`sale`, порожнє = `unset` | `contract_mode` | немає (текст договору — пакетний звіт) |
| `res.company.td_payment_control` | selection `warn`/`block`, `warn` | VP-06 | немає (контроль доплати перед виїздом бригади) |
| `res.company.td_pay_reminder_days` | integer 1–7, 2 | VP-07 | немає |
| `res.company.td_margin_to_salesman` | boolean, False | VP-08 | немає (`sale_margin` показує маржу без груп) |
| `res.company.td_cutting_mode` | selection `both`/`distributor`, `both` | VP-09 | немає; поле додано в G0 (рішення AI, TR не задає) |
| `res.company.td_stuck_days` | integer 1–30, 5 | VP-10 | немає |
| `res.company.td_price_threshold_pct` | float 1–50, 5.0 | VP-11 | немає |
| `res.company.td_min_offcut_mm` | integer 100–1000, 300 | VP-12 | немає |
| `res.company.td_claim_overdue_days` | integer 1–60, 14 | VP-13 | немає |
| `res.company.td_crew_split` | selection `equal`/`time`, `equal` | VP-14 | немає |
| `res.company.td_crew_base` | selection `final`/`stage`, `final` | VP-15 | немає |
| `res.company.td_crew_pct` | float 0–100, 0 | дані B-04 | немає |
| `res.company.td_install_in_price` | boolean, False | VP-16 | немає |
| `res.company.td_act_checklist` | text (translate) | дані B-04 | немає |
| `res.company.td_legal_checked` | boolean, False | — (№17) | немає |
| `res.company.td_box_profile` | selection `light`/`A`/`B`/`C`, `A` | VP-01 (інформаційне) | немає |
| `product.category.td_warranty_months` | integer ≥ 0, порожнє | — (№17) | немає (`product` не має строку гарантії) |

Налаштування: `res.config.settings` — ті самі поля `related='company_id.…'`, розділ «Меблі»; режим договору показано в
налаштуваннях Продажів (`td_mebli_sale`), бо туди веде текст помилки AC-034. Feature-галочки — `group_td_feature_<VP-02>`
з `implied_group` (стандарт `res.config.settings`).

## Шрифт PDF (AC-N.06)
Шрифт — Roboto (Apache License 2.0), який постачає сам Odoo (`web/static/fonts/google/Roboto`, файл `LICENSE.txt` там);
пакет не копіює файли шрифту, а оголошує 4 накреслення під іменем `TdMebli Roboto` у `web.report_assets_common`
(`static/src/scss/td_mebli_report.scss`). Звіт пакета отримує кирилицю цим шрифтом, якщо його кореневий елемент має клас
`td_mebli_report` (додають групи у своїх звітах). Стандартний шрифт звітів Lato кирилиці не має: wkhtmltopdf бере
системний (на стенді — Inter/DejaVu), це й перевіряє контрольна частина тесту.

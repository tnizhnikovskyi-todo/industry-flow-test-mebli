"""ВІДКЛАДЕНО рішенням власника 2026-11-16 (обмін з BAS/BAF не входить у збірку; AI-37). Тест конвертера
scripts/convert_bas.py, вийнятий з td_mebli_migration/tests/test_migration.py (A-11-fix5) без змін логіки. Не встановлюється
й не запускається: при поверненні BAS — перенести convert_bas.py у td_mebli_migration/scripts/, цей метод — у
TestMigrationConverters, шаблони td/19b-21b — з package/deferred/master-data/td/ у package/master-data/td/."""
import csv
import os
import tempfile

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.td_mebli_migration.scripts import convert_bas


@tagged('post_install', '-at_install')
class TestConvertBas(AccountTestInvoicingCommon):

    def _write(self, path, rows, delimiter=','):
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            csv.writer(handle, delimiter=delimiter).writerows(rows)

    def _read(self, path):
        with open(path, encoding='utf-8') as handle:
            return list(csv.reader(handle))

    HEADERS = {
        '02_res.partner.csv': ['id', 'name', 'is_company', 'supplier_rank', 'customer_rank', 'vat', 'company_registry',
                               'phone', 'email'],
        '05_product.product.csv': ['id', 'name', 'default_code', 'type', 'is_storable', 'categ_id/id', 'uom_id/id',
                                   'sale_ok', 'purchase_ok', 'route_ids/id'],
        '13_hr.employee.csv': ['id', 'name', 'job_title', 'pin'],
        'td/19b_res.partner.csv': ['id', 'td_bas_code'],
        'td/20b_product.product.csv': ['id', 'td_bas_code'],
        'td/21b_hr.employee.csv': ['id', 'td_bas_code'],
    }

    def test_ac_089_bas_converter_keeps_the_bas_code(self):
        """Return A-13-2: the code of BAS goes into td/19b-21b; the standard templates keep their header (light)."""
        with tempfile.TemporaryDirectory() as tmp:
            source, templates, out = (os.path.join(tmp, name) for name in ('src', 'tpl', 'out'))
            for folder in (source, os.path.join(templates, 'td'), out):
                os.makedirs(folder)
            for name, header in self.HEADERS.items():
                self._write(os.path.join(templates, name), [header])
            self._write(os.path.join(source, 'partners.csv'),
                        [['Код', 'Наименование', 'ИНН', 'ЕДРПОУ'], ['00-001', 'Демо-Постачальник', '', '1'],
                         ['00-002', '=HYPERLINK("x")', '', '']], delimiter=';')
            self._write(os.path.join(source, 'products.csv'),
                        [['Код', 'Наименование', 'Артикул'], ['N-01', 'Board 18', 'B18']], delimiter=';')
            self._write(os.path.join(source, 'employees.csv'),
                        [['Табельный номер', 'Сотрудник', 'Должность'], ['T-7', 'Cutter', 'Operator']], delimiter=';')
            code = convert_bas.main(['--source', source, '--templates', templates, '--out', out])
            self.assertEqual(code, 0)
            self.assertEqual(set(convert_bas.DRAFT_MAPPING), set(self.HEADERS))
            for name, header in self.HEADERS.items():
                rows = self._read(os.path.join(out, name))
                self.assertEqual(rows[0], header, f"{name}: the converter writes the header of the template as it is")
            partners = self._read(os.path.join(out, '02_res.partner.csv'))
            self.assertEqual(partners[1][0], 'td_md.res_partner_00_001')
            self.assertEqual(partners[2][1], '\'=HYPERLINK("x")', "a formula is written as text")
            self.assertEqual(self._read(os.path.join(out, 'td', '19b_res.partner.csv'))[1:],
                             [['td_md.res_partner_00_001', '00-001'], ['td_md.res_partner_00_002', '00-002']],
                             "the external code of BAS is kept, on the same ids as the partners")
            self.assertEqual(self._read(os.path.join(out, 'td', '20b_product.product.csv'))[1],
                             ['td_md.product_product_n_01', 'N-01'])
            self.assertEqual(self._read(os.path.join(out, 'td', '21b_hr.employee.csv'))[1],
                             ['td_md.hr_employee_t_7', 'T-7'])

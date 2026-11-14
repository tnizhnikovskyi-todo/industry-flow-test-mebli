#!/usr/bin/env python3
"""Converter BAS/BAF → CSV templates of the package (AC-089, step B-06). SKELETON: the export format of BAS/BAF is not
agreed (ВП-1); DRAFT_MAPPING below is our guess of the column names of a CSV export and must be replaced by the mapping
file made on the samples of the customer (--mapping). Run on a copy, load the result into a TEST database only.

    python3 convert_bas.py --source <export dir> --templates package/master-data --out <dir> [--mapping map.json]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_core import run  # noqa: E402

# draft until ВП-1: <template of A-13>: {source: <file of the export>, columns: {<template column>: <rule>}}
# The code of BAS (td_bas_code, module td_mebli_bas, VP-04) goes into the separate templates td/19b, td/20b, td/21b (second
# pass of the same ids), never into the standard templates 02, 05, 13: these must stay importable without td_mebli_bas
# (light profile). Without td_mebli_bas leave the td/ targets out (--mapping) or do not import their files.
DRAFT_MAPPING = {
    '02_res.partner.csv': {'source': 'partners.csv', 'columns': {
        'id': {'xmlid': 'res_partner', 'from': 'Код'}, 'name': 'Наименование', 'is_company': {'const': 'True'},
        'vat': 'ИНН', 'company_registry': 'ЕДРПОУ'}},
    '05_product.product.csv': {'source': 'products.csv', 'columns': {
        'id': {'xmlid': 'product_product', 'from': 'Код'}, 'name': 'Наименование', 'default_code': 'Артикул',
        'type': {'const': 'consu'}, 'is_storable': {'const': 'True'}}},
    '13_hr.employee.csv': {'source': 'employees.csv', 'columns': {
        'id': {'xmlid': 'hr_employee', 'from': 'Табельный номер'}, 'name': 'Сотрудник', 'job_title': 'Должность'}},
    'td/19b_res.partner.csv': {'source': 'partners.csv', 'columns': {
        'id': {'xmlid': 'res_partner', 'from': 'Код'}, 'td_bas_code': 'Код'}},
    'td/20b_product.product.csv': {'source': 'products.csv', 'columns': {
        'id': {'xmlid': 'product_product', 'from': 'Код'}, 'td_bas_code': 'Код'}},
    'td/21b_hr.employee.csv': {'source': 'employees.csv', 'columns': {
        'id': {'xmlid': 'hr_employee', 'from': 'Табельный номер'}, 'td_bas_code': 'Табельный номер'}},
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', required=True, help='folder with the CSV export of BAS/BAF')
    parser.add_argument('--templates', required=True, help='package/master-data (headers of the templates of A-13)')
    parser.add_argument('--out', required=True, help='folder for the filled templates')
    parser.add_argument('--mapping', help='JSON mapping made on the samples (replaces the draft mapping)')
    return run(parser.parse_args(argv), DRAFT_MAPPING)


if __name__ == '__main__':
    sys.exit(main())

"""Common core of the converters of the migration (tr/migration.md §3): an export of the old system (CSV) → CSV templates
of the package (A-13, package/master-data). Standard library only: the converters run outside Odoo (step B-06).

The export formats of BAS/BAF and BAZIS are not known (ВП-1, ВП-3): a mapping says which column of the export goes into
which column of the template. The header of the template is read from package/master-data, not copied here.

Mapping of one target file: {"<target column>": <rule>}, a rule is
  "<source column>"                         — the value of the column;
  {"const": "<value>"}                      — a fixed value;
  {"xmlid": "<prefix>", "from": "<column>"} — external id td_md.<prefix>_<slug of the value> (the id of A-13 templates);
  {"from": "<column>", "map": {...}}        — a value translated by a table (unknown values stay empty, reported).
"""
import csv
import json
import os
import re
import unicodedata

FORMULA_START = ('=', '+', '-', '@', '\t', '\r')


def slug(value):
    text = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower()
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    return text or re.sub(r'\W+', '_', str(value).lower()).strip('_')


def safe(value):
    """A text cell that a spreadsheet would run as a formula is written as text (CSV injection)."""
    text = '' if value is None else str(value)
    return "'" + text if text.startswith(FORMULA_START) else text


def template_header(path):
    with open(path, encoding='utf-8-sig', newline='') as handle:
        return next(csv.reader(handle))


def convert_rows(rows, mapping, header):
    """Rows of the export (dicts) → rows of the template (lists in the order of `header`). The header of the template is
    kept as it is: a column of the mapping that the template has not (e.g. td_bas_code in a standard template) is not
    written and is reported — the fields td_* have their own templates td/ of A-13. Returns (columns, rows, problems)."""
    columns = list(header)
    problems = [f'column «{column}» is not in the template: not written (fields td_* go into the templates td/)'
                for column in mapping if column not in header]
    result = []
    for number, row in enumerate(rows, start=2):
        out = []
        for column in columns:
            rule = mapping.get(column)
            if rule is None:
                value = ''
            elif isinstance(rule, str):
                if rule not in row:
                    problems.append(f'row {number}: no column «{rule}» in the export')
                value = row.get(rule, '')
            elif 'const' in rule:
                value = rule['const']
            elif 'xmlid' in rule:
                source = row.get(rule['from'], '')
                value = f"td_md.{rule['xmlid']}_{slug(source)}" if source else ''
            elif 'map' in rule:
                source = row.get(rule['from'], '')
                value = rule['map'].get(source, '')
                if source and not value:
                    problems.append(f'row {number}: value «{source}» of «{rule["from"]}» is not in the table')
            else:
                raise ValueError(f'unknown rule for the column {column}: {rule!r}')
            out.append(safe(value))
        result.append(out)
    return columns, result, problems


def read_export(path, delimiter=';', encoding='utf-8-sig'):
    with open(path, encoding=encoding, newline='') as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_template(path, columns, rows):
    with open(path, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def run(args, default_mappings):
    """CLI body: for each target template of the mapping file (or the default draft mapping) converts the export."""
    mappings = default_mappings
    if args.mapping:
        with open(args.mapping, encoding='utf-8') as handle:
            mappings = json.load(handle)
    problems_all = []
    for target, spec in mappings.items():
        source = f"{args.source}/{spec['source']}"
        header = template_header(f'{args.templates}/{target}')
        columns, rows, problems = convert_rows(read_export(source, spec.get('delimiter', ';')), spec['columns'], header)
        out = os.path.join(args.out, target)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        write_template(out, columns, rows)
        problems_all += [f'{target}: {problem}' for problem in problems]
        print(f'{target}: {len(rows)} rows')
    for problem in problems_all:
        print(f'WARNING {problem}')
    return 1 if problems_all else 0

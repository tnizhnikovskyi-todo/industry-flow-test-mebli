#!/usr/bin/env python3
"""Converter of the BAZIS library → CSV templates of the package (AC-089, step B-06). SKELETON: the export format of the
BAZIS library is not known (ВП-3); DRAFT_MAPPING is a guess for a CSV export of materials and must be replaced by the
mapping file made on the samples (--mapping). Load the result into a TEST database only.

    python3 convert_bazis.py --source <export dir> --templates package/master-data --out <dir> [--mapping map.json]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_core import run  # noqa: E402

DRAFT_MAPPING = {
    '05_product.product.csv': {'source': 'materials.csv', 'columns': {
        'id': {'xmlid': 'product_product', 'from': 'Article'}, 'name': 'Name', 'default_code': 'Article',
        'type': {'const': 'consu'}, 'is_storable': {'const': 'True'}}},
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', required=True, help='folder with the CSV export of the BAZIS library')
    parser.add_argument('--templates', required=True, help='package/master-data (headers of the templates of A-13)')
    parser.add_argument('--out', required=True, help='folder for the filled templates')
    parser.add_argument('--mapping', help='JSON mapping made on the samples (replaces the draft mapping)')
    return run(parser.parse_args(argv), DRAFT_MAPPING)


if __name__ == '__main__':
    sys.exit(main())

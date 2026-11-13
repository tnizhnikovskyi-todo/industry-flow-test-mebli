"""AC-005: the number of a measurement sheet is ЗМ/YYYY/NNNN (the slice had «ЗМ-»). The sequence is noupdate data, so
the prefix of an existing database is changed here; the numbers already given stay as they are."""


def migrate(cr, version):
    cr.execute("""
        UPDATE ir_sequence SET prefix = 'ЗМ/%%(year)s/', padding = 4
         WHERE id IN (SELECT res_id FROM ir_model_data
                       WHERE module = 'td_mebli_measure' AND name = 'seq_td_mebli_measure' AND model = 'ir.sequence')
           AND prefix = 'ЗМ-'
    """)

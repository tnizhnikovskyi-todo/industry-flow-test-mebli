"""19.0.1.1.1 (review A-14 m4): the job of the exchange with BAS and the sequence of the batches are `noupdate` — an
update of the package must not switch on again the job the finance user switched off (e.g. during the cutover) nor reset
the numbering. The data file is `noupdate` now; the records already in the database keep the old flag in ir.model.data,
it is set here."""

XMLIDS = ('seq_td_mebli_bas_batch', 'ir_cron_td_bas_exchange')


def migrate(cr, version):
    if not version:
        return
    cr.execute("UPDATE ir_model_data SET noupdate = TRUE WHERE module = %s AND name IN %s",
               ('td_mebli_bas', XMLIDS))

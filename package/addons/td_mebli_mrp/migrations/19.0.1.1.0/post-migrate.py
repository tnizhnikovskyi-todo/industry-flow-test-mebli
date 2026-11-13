"""19.0.1.1.0 (AC-052, review A-11): the new field mrp.bom.td_cut_version locks the parts of a specification sent to
cutting. A database of the slice already has cutting jobs that were sent (or got their result, or are done) — their
specifications get version 1, otherwise their parts would become editable after the update.

td_mebli_cutting depends on this module, so its tables may be absent (the module is not installed): checked first."""


def migrate(cr, version):
    if not version:
        return
    cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'td_mebli_cutting_job_production_rel'")
    if not cr.fetchone():
        return
    cr.execute("""
        UPDATE mrp_bom b
           SET td_cut_version = 1
         WHERE COALESCE(b.td_cut_version, 0) = 0
           AND EXISTS (SELECT 1
                         FROM td_mebli_cutting_job j
                         JOIN td_mebli_cutting_job_production_rel r ON r.job_id = j.id
                         JOIN mrp_production p ON p.id = r.production_id
                        WHERE p.bom_id = b.id AND j.state IN ('sent', 'result', 'done'))
    """)

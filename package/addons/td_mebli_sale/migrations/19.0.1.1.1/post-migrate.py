"""19.0.1.1.1 (review A-14 M2): the mail template «change of the order for signature» is `noupdate` — its text is edited
for the customer on B-04 and an update of the package (B-11) must not overwrite it. The data file is `noupdate` now;
the record already in the database keeps the old flag in ir.model.data, it is set here."""

XMLIDS = ('mail_template_td_change_sign',)


def migrate(cr, version):
    if not version:
        return
    cr.execute("UPDATE ir_model_data SET noupdate = TRUE WHERE module = %s AND name IN %s",
               ('td_mebli_sale', XMLIDS))

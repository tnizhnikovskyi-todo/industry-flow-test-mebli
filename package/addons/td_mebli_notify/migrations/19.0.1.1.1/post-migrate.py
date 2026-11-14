"""19.0.1.1.1 (review A-14 M2): the mail templates and the activity type of the module are `noupdate` — the texts of the
letters are edited for the customer on B-04 and an update of the package (B-11) must not overwrite them. The data file
is `noupdate` now; the records already in the database keep the old flag in ir.model.data, it is set here."""

XMLIDS = (
    'mail_template_td_new_date', 'mail_template_td_payment_reminder', 'mail_template_td_install_reminder',
    'mail_template_td_measure_booking', 'mail_template_td_install_date', 'mail_template_td_briefing',
    'mail_activity_type_td_forecast_shift',
)


def migrate(cr, version):
    if not version:
        return
    cr.execute("UPDATE ir_model_data SET noupdate = TRUE WHERE module = %s AND name IN %s",
               ('td_mebli_notify', XMLIDS))

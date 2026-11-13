"""19.0.1.1.0: the setting «Payment before installation» moved to the company (td_mebli_base, VP-06).

The old settings view of the slice reads the removed field td_mebli_payment_control; it is deleted before the update,
otherwise the settings views of the modules updated after this one fail to validate."""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        DELETE FROM ir_ui_view WHERE id IN (
            SELECT res_id FROM ir_model_data
             WHERE module = 'td_mebli_install' AND model = 'ir.ui.view'
               AND name = 'res_config_settings_view_form_td_mebli_install')
    """)
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'td_mebli_install' AND name = 'res_config_settings_view_form_td_mebli_install'
    """)

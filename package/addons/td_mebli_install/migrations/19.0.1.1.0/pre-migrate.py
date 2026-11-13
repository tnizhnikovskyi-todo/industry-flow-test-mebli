"""19.0.1.1.0: the setting «Payment before installation» moved to the company (td_mebli_base, VP-06).

The old settings view of the slice reads the removed field td_mebli_payment_control; it is deleted before the update,
otherwise the settings views of the modules updated after this one fail to validate.

Review A-11 (round 2): the live duplicate accruals are cancelled before the unique indexes are created."""
import logging

_logger = logging.getLogger(__name__)


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

    # review A-11 (round 2): the unique indexes of 19.0.1.1.0 (one live accrual per time line, one per installer
    # and act) are not created over live duplicates — the duplicates are cancelled first: the oldest accrual stays,
    # the others get the state «Cancelled» and the reason in the cancellation reason
    cr.execute("ALTER TABLE td_mebli_accrual ADD COLUMN IF NOT EXISTS cancel_reason varchar")
    for columns in ('productivity_id', 'act_id, employee_id'):
        first = columns.split(',')[0].strip()
        cr.execute(f"""
            UPDATE td_mebli_accrual a
               SET state = 'cancel',
                   cancel_reason = 'Дубль нарахування #' || d.keep_id || ' (оновлення 19.0.1.1.0)'
              FROM (SELECT id, MIN(id) OVER (PARTITION BY {columns}) AS keep_id
                      FROM td_mebli_accrual
                     WHERE state != 'cancel' AND {first} IS NOT NULL) d
             WHERE a.id = d.id AND d.id != d.keep_id
        """)
        if cr.rowcount:
            _logger.warning("td_mebli_install: %s duplicate accruals (%s) cancelled before the unique index",
                            cr.rowcount, columns)

"""19.0.1.1.0 (review A-11, update of a database of the slice): the form view of the order of the slice
`td_mebli_ua.view_order_form_td_mebli_ua` has the button «Send to BAS» (`action_td_send_bas`), which moved to the new
module td_mebli_bas. td_mebli_ua is updated after this module, so the old view is still in the database when the views
of this module are validated, and the update fails («action_td_send_bas is not a valid action»). The view is no longer
in td_mebli_ua (19.0.1.1.0): it is deleted here, with its xmlid, before the views of this module are loaded."""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT res_id FROM ir_model_data
         WHERE module = 'td_mebli_ua' AND model = 'ir.ui.view' AND name = 'view_order_form_td_mebli_ua'
    """)
    view_ids = [row[0] for row in cr.fetchall()]
    if not view_ids:
        return
    cr.execute("DELETE FROM ir_ui_view WHERE id = ANY(%s) OR inherit_id = ANY(%s)", (view_ids, view_ids))
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'td_mebli_ua' AND model = 'ir.ui.view' AND name = 'view_order_form_td_mebli_ua'
    """)

"""Scenario of the demo show (docs/industries/mebli/prototype-real/SHOW.md) as code.

run(env, upto) replays the steps up to the given one on a database with td_mebli_demo, so that
screenshots can be retaken on a clean database. Steps (see SHOW.md): 1-3 quotation, 4 order BoM,
5 confirmation, 9-11 cutting job, 12 offcuts, 13 finished manufacturing orders.
"""


def _custom(env, tmpl, attr_xmlid, text):
    value = env.ref(f'td_mebli_demo.val_{attr_xmlid}_custom')
    ptav = tmpl.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.product_attribute_value_id == value)
    return (0, 0, {'custom_product_template_attribute_value_id': ptav.id, 'custom_value': str(text)})


def make_order(env, product_xmlid, dims, body, facade, edge, fitting, qty=1.0):
    """Quotation with one configured furniture line. body/facade/edge/fitting are xmlids of attribute values."""
    tmpl = env.ref(f'td_mebli_demo.{product_xmlid}')
    chosen = tmpl.attribute_line_ids.product_template_value_ids.filtered(
        lambda v: v.product_attribute_value_id in [env.ref(f'td_mebli_demo.{x}') for x in (body, facade, edge, fitting)])
    width, height, depth = dims
    return env['sale.order'].create({
        'partner_id': env.ref('td_mebli_demo.partner_salon').id,
        'order_line': [(0, 0, {
            'product_id': tmpl.product_variant_id.id, 'product_uom_qty': qty,
            'product_custom_attribute_value_ids': [
                _custom(env, tmpl, 'w', width), _custom(env, tmpl, 'h', height), _custom(env, tmpl, 'd', depth)],
            'product_no_variant_attribute_value_ids': [(6, 0, chosen.ids)],
        })],
    })


def run(env, upto=14):
    result = {}
    # steps 2-3: the quotation of a wardrobe
    order = make_order(env, 'prod_wardrobe', (1800, 2400, 600), 'val_body_sonoma', 'val_facade_mdf',
                       'val_edge_2', 'val_fit_premium')
    result['order'] = order
    if upto < 4:
        return result
    order.order_line.action_td_generate_bom()                      # step 4
    if upto < 5:
        return result
    dresser = make_order(env, 'prod_dresser', (800, 850, 450), 'val_body_white', 'val_facade_mdf',
                         'val_edge_04', 'val_fit_std')
    result['dresser_order'] = dresser
    (order | dresser).action_confirm()                             # step 5
    productions = (order | dresser).mrp_production_ids
    result['productions'] = productions
    if upto < 9:
        return result
    job = productions.action_td_create_cutting_job()               # step 9
    job = env[job['res_model']].browse(job['res_id'])
    job.action_send()
    result['job'] = job
    if upto < 10:
        return result
    job.action_simulate()                                          # steps 10-11
    if upto < 12:
        return result
    job.action_done()                                              # step 12
    if upto < 13:
        return result
    for production in productions:                                 # step 13
        for workorder in production.workorder_ids:
            workorder.button_start()
            workorder.button_finish()
        production.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()
    return result

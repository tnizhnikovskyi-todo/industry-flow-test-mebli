import logging

_logger = logging.getLogger(__name__)

# System parameters of the slice (A-21) -> field of the company; value transform of the slice keys
SLICE_PARAMS = {
    'td_mebli_sale.contract_mode': ('td_contract_mode', {'work': 'contract', 'contract': 'contract', 'sale': 'sale'}),
    'td_mebli_install.payment_control': ('td_payment_control', {'warn': 'warn', 'block': 'block'}),
}
SLICE_WARRANTY = 'td_mebli_claim.warranty_months'

# Contract of the config package before A-11 (package/config/vp-map.yaml: kind td_param, key td_mebli.vp_xx)
CONFIG_PARAMS = {
    'td_mebli.vp_01': 'td_box_profile',
    'td_mebli.vp_06': 'td_payment_control',
    'td_mebli.vp_07': 'td_pay_reminder_days',
    'td_mebli.vp_08': 'td_margin_to_salesman',
    'td_mebli.vp_09': 'td_cutting_mode',
    'td_mebli.vp_10': 'td_stuck_days',
    'td_mebli.vp_11': 'td_price_threshold_pct',
    'td_mebli.vp_12': 'td_min_offcut_mm',
    'td_mebli.vp_13': 'td_claim_overdue_days',
    'td_mebli.vp_14': 'td_crew_split',
    'td_mebli.vp_15': 'td_crew_base',
    'td_mebli.vp_16': 'td_install_in_price',
    'td_mebli.contract_mode': 'td_contract_mode',
}


def _convert(field, raw):
    """Text of a system parameter -> value of the field, or None when the text is not a valid answer."""
    raw = (raw or '').strip()
    if field.type == 'boolean':
        return {'true': True, '1': True, 'false': False, '0': False}.get(raw.lower())
    if field.type == 'integer':
        try:
            return int(float(raw))
        except ValueError:
            return None
    if field.type == 'float':
        try:
            return float(raw.replace(',', '.'))
        except ValueError:
            return None
    if field.type == 'selection':
        if raw in ('', 'unset'):
            return False
        return raw if raw in dict(field.selection) else None
    return None


def post_init_hook(env):
    """AC-N.04: the global system parameters of the slice and of the config package become the fields of every
    company (a global parameter meant the same answer for all companies). The old parameters stay: the modules
    td_mebli_install and td_mebli_claim read them until their groups move to the fields."""
    get = env['ir.config_parameter'].sudo().get_param
    companies = env['res.company'].sudo().with_context(active_test=False).search([])
    vals = {}
    for key, (name, transform) in SLICE_PARAMS.items():
        raw = get(key)
        if raw:
            if raw in transform:
                vals[name] = transform[raw]
            else:
                _logger.warning("td_mebli_base: system parameter %s=%r is not a known value, skipped", key, raw)
    for key, name in CONFIG_PARAMS.items():   # the config package is newer than the slice: its answers win
        raw = get(key)
        if raw is False or raw is None:
            continue
        value = _convert(companies._fields[name], raw)
        if value is None:
            _logger.warning("td_mebli_base: system parameter %s=%r is not a valid answer, skipped", key, raw)
            continue
        vals[name] = value
    if vals:
        companies.write(vals)
        _logger.info("td_mebli_base: parameters moved into the companies: %s", vals)
    months = get(SLICE_WARRANTY)
    if months:
        try:
            months = int(months)
        except ValueError:
            _logger.warning("td_mebli_base: %s=%r is not a number, skipped", SLICE_WARRANTY, months)
        else:
            categories = env['product.category'].sudo().search([('td_warranty_months', '=', 0)])
            categories.write({'td_warranty_months': months})
    # the salesmen of the companies with «Salesman Sees the Margin» get the group (also without moved parameters)
    companies.filtered('td_margin_to_salesman')._td_sync_margin_group()

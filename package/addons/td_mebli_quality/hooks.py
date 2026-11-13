def post_init_hook(env):
    """The function «quality» of box B is replaced by Quality: its feature group is no longer implied for the
    employees (the td_ buttons and screens of the function are hidden; the data stay)."""
    env.ref('base.group_user')._remove_group(env.ref('td_mebli_base.group_feature_quality'))
    env['mrp.routing.workcenter'].search([('td_quality_point', '!=', False)])._td_sync_quality_points()

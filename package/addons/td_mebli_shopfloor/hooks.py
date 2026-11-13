def post_init_hook(env):
    """The function «kiosk» of box B is replaced by Shop Floor: its feature group is no longer implied for the
    employees (the td_ buttons and screens of the function are hidden; the data stay)."""
    env.ref('base.group_user')._remove_group(env.ref('td_mebli_base.group_feature_kiosk'))

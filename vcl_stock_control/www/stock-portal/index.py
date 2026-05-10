import frappe


def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Login required.", frappe.PermissionError)

    roles = set(frappe.get_roles(user))
    is_admin = bool(roles & {"System Manager", "Stock Manager"})
    role = "Admin" if is_admin else ("Reviewer" if "Stock Reviewer" in roles else "Counter")

    active_cycle = frappe.get_value(
        "VCL Stock Count Cycle",
        {"status": ("in", ("Open", "In Progress")), "is_default": 1},
        ["name", "period_label", "start_date", "end_date", "status"],
        as_dict=True,
    ) or frappe.get_value(
        "VCL Stock Count Cycle",
        {"status": ("in", ("Open", "In Progress"))},
        ["name", "period_label", "start_date", "end_date", "status"],
        as_dict=True,
        order_by="modified desc",
    )

    sheet_filters = {} if is_admin else {"counter": user}
    my_sheets = frappe.get_all(
        "VCL Stock Count Sheet",
        filters=sheet_filters,
        fields=["name", "sheet_title", "pattern", "status", "coverage_satisfied"],
        order_by="modified desc",
        limit=50,
    )

    context.no_cache = 1
    context.role = role
    context.is_admin = is_admin
    context.active_cycle = active_cycle
    context.my_sheets = my_sheets
    return context

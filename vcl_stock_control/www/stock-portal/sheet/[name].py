import frappe


def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Login required.", frappe.PermissionError)

    name = frappe.form_dict.name
    sheet = frappe.get_doc("VCL Stock Count Sheet", name)
    sheet.check_permission("read")

    matrix = {}
    warehouses: list[str] = []
    items: list[tuple[str, str]] = []

    if sheet.pattern == "Multi-Warehouse Matrix":
        seen_w: list[str] = []
        seen_items: dict[str, str] = {}
        for line in sheet.lines:
            if line.warehouse and line.warehouse not in seen_w:
                seen_w.append(line.warehouse)
            if line.vcl_key not in seen_items:
                seen_items[line.vcl_key] = line.item_label or line.vcl_key
            matrix[(line.vcl_key, line.warehouse)] = line
        warehouses = seen_w
        items = list(seen_items.items())

    context.no_cache = 1
    context.sheet = sheet
    context.warehouses = warehouses
    context.items = items
    context.matrix = matrix
    return context

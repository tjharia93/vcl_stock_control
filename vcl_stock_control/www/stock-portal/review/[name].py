import frappe


def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Login required.", frappe.PermissionError)

    name = frappe.form_dict.name
    sheet = frappe.get_doc("VCL Stock Count Sheet", name)
    sheet.check_permission("read")

    roles = set(frappe.get_roles(user))
    can_review = bool(roles & {"System Manager", "Stock Manager"}) or sheet.reviewer == user

    context.no_cache = 1
    context.sheet = sheet
    context.can_review = can_review
    return context

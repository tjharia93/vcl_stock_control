import frappe

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.throw("Please log in to access this page.", frappe.AuthenticationError)

    context.no_cache = 1
    context.show_sidebar = False
    context.title = "Ink & Chemical Stock Entry"
    context.today = frappe.utils.today()

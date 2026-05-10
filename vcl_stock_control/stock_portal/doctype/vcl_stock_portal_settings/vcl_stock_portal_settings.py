import frappe
from frappe.model.document import Document


class VCLStockPortalSettings(Document):
    pass


def get_settings():
    return frappe.get_cached_doc("VCL Stock Portal Settings")

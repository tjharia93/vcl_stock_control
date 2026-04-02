import frappe
from frappe.model.document import Document


class StockCategory(Document):
    def validate(self):
        if self.is_item_linked and self.is_manual_only:
            frappe.throw("A Stock Category cannot be both Item Linked and Manual Only.")

import frappe
from frappe.model.document import Document


class StockMaterialProfile(Document):
    def validate(self):
        if self.linked_item:
            if not frappe.db.exists("Item", self.linked_item):
                frappe.throw(f"Linked Item {self.linked_item} does not exist.")

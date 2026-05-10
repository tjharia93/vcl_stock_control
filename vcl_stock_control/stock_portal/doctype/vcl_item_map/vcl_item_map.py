import frappe
from frappe.model.document import Document


class VCLItemMap(Document):
    def validate(self):
        if self.reconciliation_status in ("REUSE", "RECONCILE") and not self.erpnext_item:
            frappe.throw(
                f"VCL Item Map {self.vcl_key}: reconciliation_status={self.reconciliation_status} "
                "requires erpnext_item to be set."
            )

        if self.erpnext_item:
            item_uom = frappe.db.get_value("Item", self.erpnext_item, "stock_uom")
            if self.uom and item_uom and self.uom != item_uom:
                frappe.msgprint(
                    f"UOM mismatch for {self.vcl_key}: map says {self.uom}, "
                    f"ERPNext Item {self.erpnext_item} stock_uom is {item_uom}.",
                    indicator="orange",
                    alert=True,
                )

    def autoname(self):
        if self.vcl_key:
            self.vcl_key = self.vcl_key.strip().upper()

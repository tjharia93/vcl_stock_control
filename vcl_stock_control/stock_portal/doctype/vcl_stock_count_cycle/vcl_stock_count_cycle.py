import frappe
from frappe.model.document import Document


class VCLStockCountCycle(Document):
    def validate(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw("End Date cannot be before Start Date.")

        if self.is_default:
            others = frappe.get_all(
                "VCL Stock Count Cycle",
                filters={"is_default": 1, "name": ("!=", self.name)},
                pluck="name",
            )
            for n in others:
                frappe.db.set_value("VCL Stock Count Cycle", n, "is_default", 0)

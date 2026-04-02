import frappe
from frappe.model.document import Document


class StockUOMConversionRule(Document):
    def validate(self):
        if self.from_uom == self.to_uom:
            frappe.throw("From UOM and To UOM cannot be the same.")

        if not self.conversion_factor or self.conversion_factor <= 0:
            frappe.throw("Conversion Factor must be greater than zero.")

        if self.conversion_for == "Material Profile" and not self.material_profile:
            frappe.throw("Material Profile is required when Conversion For is 'Material Profile'.")
        elif self.conversion_for == "Stock Category" and not self.stock_category:
            frappe.throw("Stock Category is required when Conversion For is 'Stock Category'.")

import frappe
from frappe.model.document import Document
from vcl_stock_control.stock_utils import validate_stock_lines, validate_material_source


class FuelStockEntry(Document):
    def validate(self):
        self.validate_lines()

    def validate_lines(self):
        for row in self.items:
            # Fuel lines can use fuel_point + optional profile/manual desc
            has_source = getattr(row, "fuel_point", None) or getattr(row, "material_profile", None) or getattr(row, "manual_description", None)
            if not has_source:
                frappe.throw(f"Row {row.idx}: At least Fuel Point, Material Profile, or Manual Description is required.")
        validate_stock_lines(self, "items")

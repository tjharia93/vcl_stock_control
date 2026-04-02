import frappe
from frappe.model.document import Document
from vcl_stock_control.stock_utils import validate_stock_lines, validate_material_source


class RawMaterialStockEntry(Document):
    def validate(self):
        self.validate_lines()

    def validate_lines(self):
        for row in self.items:
            validate_material_source(row, require_item=False)
        validate_stock_lines(self, "items")

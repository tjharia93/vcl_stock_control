import frappe
from frappe.model.document import Document
from vcl_stock_control.stock_utils import validate_stock_lines, validate_material_source


class SpareStockEntry(Document):
    def validate(self):
        self.validate_lines()
        self.set_reorder_flags()

    def validate_lines(self):
        for row in self.items:
            validate_material_source(row, require_item=False)
        validate_stock_lines(self, "items")

    def set_reorder_flags(self):
        for row in self.items:
            if row.minimum_level and row.qty_in_default_uom is not None:
                row.reorder_flag = 1 if row.qty_in_default_uom < row.minimum_level else 0

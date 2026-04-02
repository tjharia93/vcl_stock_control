import frappe
from frappe.model.document import Document
from vcl_stock_control.stock_utils import validate_stock_lines, validate_material_source


class FinishedGoodsStockEntry(Document):
    def validate(self):
        self.calculate_pieces()
        self.validate_lines()

    def calculate_pieces(self):
        for row in self.items:
            bundle_pieces = (row.bundle_qty or 0) * (row.pieces_per_bundle or 0)
            carton_pieces = (row.carton_qty or 0) * (row.pieces_per_carton or 0)
            total = bundle_pieces + carton_pieces

            if total > 0:
                row.calculated_pieces = total
                # If default_uom is Pcs and entry_qty not manually set, use calculated
                if not row.entry_qty or row.entry_qty == 0:
                    row.entry_qty = total
                    row.entry_uom = row.default_uom
                    row.conversion_factor = 1.0

    def validate_lines(self):
        for row in self.items:
            validate_material_source(row, require_item=False)
        validate_stock_lines(self, "items")

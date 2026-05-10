import frappe
from frappe import _
from frappe.model.document import Document


class VCLStocktakeItemMap(Document):
    def validate(self):
        self.validate_approval_gate()

    def validate_approval_gate(self):
        """Block 'Approved for Print' until every operational prerequisite is met.

        Draft / Needs* / Ready for Review / Excluded / Inactive states are
        intentionally permissive so users can build mappings incrementally.
        """
        if self.mapping_status != "Approved for Print":
            return

        missing = []
        if not self.active:
            missing.append("Active flag")
        if not self.erpnext_item:
            missing.append("ERPNext Item")
        if not self.erpnext_warehouse:
            missing.append("ERPNext Warehouse")
        if not self.count_uom:
            missing.append("Count UOM")
        if not self.erpnext_stock_uom:
            missing.append("ERPNext Stock UOM")
        if not self.area:
            missing.append("Area")
        if not self.print_sequence or self.print_sequence <= 0:
            missing.append("Print Sequence (> 0)")

        if missing:
            frappe.throw(
                _("Cannot set Mapping Status to 'Approved for Print'. Missing or invalid: {0}.").format(
                    ", ".join(missing)
                )
            )

        if (
            self.count_uom
            and self.erpnext_stock_uom
            and self.count_uom != self.erpnext_stock_uom
            and (not self.conversion_rule or self.conversion_rule == "None")
        ):
            frappe.throw(
                _(
                    "Count UOM ({0}) differs from ERPNext Stock UOM ({1}); a Conversion Rule must be set for approval."
                ).format(self.count_uom, self.erpnext_stock_uom)
            )

        self._validate_conversion_inputs()

    def _validate_conversion_inputs(self):
        rule = self.conversion_rule or "None"

        if rule == "Fixed Factor":
            if not self.conversion_factor or self.conversion_factor <= 0:
                frappe.throw(
                    _("Conversion Factor must be greater than zero when Conversion Rule is 'Fixed Factor'.")
                )
        elif rule == "Reel to SQM":
            if not self.width_mm or not self.standard_length_m:
                frappe.throw(
                    _("Width (mm) and Standard Length (m) are required when Conversion Rule is 'Reel to SQM'.")
                )
        elif rule == "Reel to KG":
            if not self.avg_weight_kg:
                frappe.throw(
                    _("Avg Weight (kg) is required when Conversion Rule is 'Reel to KG'.")
                )
        elif rule == "Pack Size":
            if not self.conversion_factor or self.conversion_factor <= 0:
                frappe.throw(
                    _("Conversion Factor must be greater than zero when Conversion Rule is 'Pack Size'.")
                )

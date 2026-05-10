import frappe
from frappe import _
from frappe.model.document import Document


class VCLStocktakeMappingException(Document):
    def validate(self):
        self.validate_mapped_resolution()

    def validate_mapped_resolution(self):
        """When an exception is marked as 'Mapped', it must point at an Item Map row."""
        if self.resolution_status == "Mapped" and not self.linked_item_map:
            frappe.throw(
                _("Linked Item Map is required when Resolution Status is 'Mapped'.")
            )

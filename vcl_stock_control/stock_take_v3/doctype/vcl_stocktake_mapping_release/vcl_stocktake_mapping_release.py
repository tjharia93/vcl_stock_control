import frappe
from frappe import _
from frappe.model.document import Document


class VCLStocktakeMappingRelease(Document):
    def validate(self):
        self.validate_locked_transition()

    def validate_locked_transition(self):
        """Once Locked, a release can only move to Cancelled.

        New rows (is_new) and unchanged rows are skipped so this only triggers
        when an existing Locked release is being edited.
        """
        if self.is_new():
            return

        previous = self.get_doc_before_save()
        if not previous:
            return

        if previous.status == "Locked" and self.status not in ("Locked", "Cancelled"):
            frappe.throw(
                _("Release {0} is Locked. It can only be moved to Cancelled.").format(
                    self.release_version
                )
            )

import frappe
from frappe.model.document import Document
from frappe.utils import flt


VALID_TRANSITIONS = {
    "Draft": {"Counting", "Cancelled"},
    "Counting": {"Submitted", "Cancelled"},
    "Submitted": {"Under Review", "Cancelled"},
    "Under Review": {"Approved", "Counting", "Cancelled"},
    "Approved": {"Posted", "Cancelled"},
    "Posted": set(),
    "Cancelled": set(),
}


class VCLStockCountSheet(Document):
    def validate(self):
        self._enforce_transition()
        self._compute_variance()
        self._compute_coverage()

        if self.status in ("Submitted", "Under Review", "Approved", "Posted"):
            if self.coverage_required and not self.coverage_satisfied:
                missed = [
                    f"{l.idx}: {l.vcl_key}"
                    for l in self.lines
                    if not l.counted_at and not l.skip_reason
                ]
                frappe.throw(
                    "Coverage check failed. Every line must have a counted_at "
                    "value OR an explicit skip_reason before submit. Missed lines: "
                    + ", ".join(missed[:10])
                    + ("..." if len(missed) > 10 else "")
                )

    def _enforce_transition(self):
        if self.is_new():
            return
        previous = frappe.db.get_value("VCL Stock Count Sheet", self.name, "status")
        if previous and previous != self.status:
            allowed = VALID_TRANSITIONS.get(previous, set())
            if self.status not in allowed:
                frappe.throw(
                    f"Invalid status transition: {previous} -> {self.status}. "
                    f"Allowed from {previous}: {sorted(allowed) or 'none'}."
                )
            self._previous_status = previous
        else:
            self._previous_status = previous

    def _compute_variance(self):
        for line in self.lines:
            if line.skip_reason:
                line.variance_qty = 0
                continue
            line.variance_qty = flt(line.counted_qty) - flt(line.system_qty)

    def _compute_coverage(self):
        if not self.lines:
            self.coverage_satisfied = 0
            return
        for line in self.lines:
            if not line.counted_at and not line.skip_reason:
                self.coverage_satisfied = 0
                return
        self.coverage_satisfied = 1

    def on_update(self):
        previous = getattr(self, "_previous_status", None)
        if previous == self.status:
            return

        from vcl_stock_control.stock_portal.doctype.vcl_stock_portal_settings.vcl_stock_portal_settings import (
            get_settings,
        )

        if self.status == "Approved":
            settings = get_settings()
            if settings.direct_post_mode and not self.direct_post_mode_snapshot:
                self.db_set("direct_post_mode_snapshot", 1)
                from vcl_stock_control.api.post_to_erpnext import post_count_sheet
                post_count_sheet(self.name)

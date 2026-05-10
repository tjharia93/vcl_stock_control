"""
VCL Stock Portal staging -> ERPNext Stock Reconciliation bridge.

Architecture:
  VCL Stock Count Sheet (staging)  -->  ERPNext Stock Reconciliation
                                  via VCL Item Map translation layer

Rules:
  1. Coverage check: every line must have counted_at OR skip_reason set.
  2. qty=0 lines DO post. They are a valid audit signal ("counted, found nothing").
  3. Lines with skip_reason set are excluded from posting.
  4. Lines are grouped by warehouse; one Stock Reconciliation per warehouse.
  5. Every line goes through VCL Item Map; the portal never references ERPNext
     Item codes directly.
"""
from collections import defaultdict
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


@frappe.whitelist()
def post_count_sheet(sheet_name: str, posting_user: str | None = None) -> dict:
    """
    Translate a VCL Stock Count Sheet into one or more Stock Reconciliations.

    Returns: {"sheet": <name>, "stock_reconciliations": [<name>, ...]}
    """
    sheet = frappe.get_doc("VCL Stock Count Sheet", sheet_name)

    if sheet.status not in ("Approved", "Submitted"):
        frappe.throw(
            _("Sheet {0} is in status {1}; must be Approved (or Submitted with direct_post_mode) before posting.").format(
                sheet_name, sheet.status
            )
        )

    if sheet.coverage_required and not sheet.coverage_satisfied:
        frappe.throw(
            _("Sheet {0} did not satisfy coverage check. Refusing to post.").format(sheet_name)
        )

    postable = _filter_postable_lines(sheet)
    if not postable:
        frappe.throw(_("Sheet {0} has no postable lines (all skipped or empty).").format(sheet_name))

    grouped = _group_by_warehouse(postable)

    sr_names: list[str] = []
    for warehouse, lines in grouped.items():
        sr_name = _create_stock_reconciliation(
            sheet=sheet,
            warehouse=warehouse,
            lines=lines,
            posting_user=posting_user,
        )
        sr_names.append(sr_name)

    sheet.db_set("linked_stock_reconciliation", ", ".join(sr_names))
    sheet.db_set("status", "Posted")
    return {"sheet": sheet.name, "stock_reconciliations": sr_names}


def _filter_postable_lines(sheet) -> list:
    """Skip-reason lines OUT. qty=0 lines IN."""
    out = []
    for line in sheet.lines:
        if line.skip_reason:
            continue
        if not line.counted_at:
            frappe.throw(
                _("Line {0} ({1}) has no counted_at and no skip_reason — refusing to post.").format(
                    line.idx, line.vcl_key
                )
            )
        out.append(line)
    return out


def _group_by_warehouse(lines) -> dict:
    grouped: dict = defaultdict(list)
    for line in lines:
        warehouse = line.warehouse or _resolve_default_warehouse(line.vcl_key)
        if not warehouse:
            frappe.throw(
                _("Line {0} ({1}) has no warehouse and VCL Item Map has no default_warehouse.").format(
                    line.idx, line.vcl_key
                )
            )
        grouped[warehouse].append(line)
    return grouped


def _resolve_default_warehouse(vcl_key: str) -> str | None:
    return frappe.db.get_value("VCL Item Map", vcl_key, "default_warehouse")


def _resolve_erpnext_item(vcl_key: str) -> tuple[str, str]:
    """Returns (erpnext_item_code, uom). Raises if map is incomplete."""
    row = frappe.db.get_value(
        "VCL Item Map",
        vcl_key,
        ["erpnext_item", "uom", "reconciliation_status", "is_active"],
        as_dict=True,
    )
    if not row:
        frappe.throw(_("VCL Item Map has no entry for key {0}.").format(vcl_key))
    if not row.is_active:
        frappe.throw(_("VCL Item Map entry {0} is inactive.").format(vcl_key))
    if row.reconciliation_status == "PENDING":
        frappe.throw(
            _("VCL Item Map entry {0} is still PENDING reconciliation; cannot post.").format(vcl_key)
        )
    if not row.erpnext_item:
        frappe.throw(
            _("VCL Item Map entry {0} has no erpnext_item set.").format(vcl_key)
        )
    return row.erpnext_item, row.uom


def _create_stock_reconciliation(sheet, warehouse: str, lines: list, posting_user: str | None) -> str:
    company = _resolve_company(warehouse)
    accounts = _resolve_accounts(company)

    sr = frappe.new_doc("Stock Reconciliation")
    sr.purpose = "Stock Reconciliation"
    sr.posting_date = sheet.count_date
    sr.posting_time = (sheet.modified or now_datetime()).strftime("%H:%M:%S")
    sr.set_warehouse = warehouse
    sr.company = company
    if accounts.get("expense_account"):
        sr.expense_account = accounts["expense_account"]
    if accounts.get("cost_center"):
        sr.cost_center = accounts["cost_center"]
    if accounts.get("difference_account"):
        sr.difference_account = accounts["difference_account"]
    sr.remarks = (
        f"Posted from VCL Stock Count Sheet {sheet.name} "
        f"(cycle={sheet.cycle}, sheet_code={sheet.sheet_code}, "
        f"counter={sheet.counter or '?'}, reviewer={sheet.reviewer or '?'})"
    )

    for line in lines:
        item_code, _uom = _resolve_erpnext_item(line.vcl_key)
        sr.append("items", {
            "item_code": item_code,
            "warehouse": warehouse,
            "qty": flt(line.counted_qty),
        })

    sr.flags.ignore_permissions = bool(posting_user)
    sr.insert(ignore_permissions=bool(posting_user))
    sr.submit()
    return sr.name


def _resolve_company(warehouse: str) -> str:
    company = frappe.db.get_value("Warehouse", warehouse, "company")
    if not company:
        frappe.throw(_("Warehouse {0} has no company set.").format(warehouse))
    return company


def _resolve_accounts(company: str) -> dict:
    """Pull difference account / expense account / cost center defaults so the
    Stock Reconciliation submit doesn't fail on a fresh ERPNext where the user
    didn't pre-set them in Stock Settings."""
    out: dict = {}
    out["expense_account"] = frappe.db.get_value(
        "Company", company, "stock_adjustment_account"
    )
    out["cost_center"] = frappe.db.get_value("Company", company, "cost_center")
    out["difference_account"] = out["expense_account"]
    return out


@frappe.whitelist()
def coverage_status(sheet_name: str) -> dict:
    """Lightweight coverage check for the web UI guard."""
    sheet = frappe.get_doc("VCL Stock Count Sheet", sheet_name)
    total = len(sheet.lines)
    counted = sum(1 for l in sheet.lines if l.counted_at)
    skipped = sum(1 for l in sheet.lines if l.skip_reason)
    missed = [
        {"idx": l.idx, "vcl_key": l.vcl_key, "label": l.item_label}
        for l in sheet.lines
        if not l.counted_at and not l.skip_reason
    ]
    return {
        "sheet": sheet_name,
        "total_lines": total,
        "counted": counted,
        "skipped": skipped,
        "missed_count": len(missed),
        "missed": missed[:50],
        "satisfied": len(missed) == 0,
    }


@frappe.whitelist()
def record_count(sheet_name: str, line_idx: int, counted_qty: float) -> dict:
    """Single-line update from the web entry page. Stamps counted_at + counted_by."""
    sheet = frappe.get_doc("VCL Stock Count Sheet", sheet_name)
    if sheet.status not in ("Draft", "Counting"):
        frappe.throw(_("Cannot record counts on a sheet in status {0}.").format(sheet.status))

    line = next((l for l in sheet.lines if l.idx == int(line_idx)), None)
    if not line:
        frappe.throw(_("Line idx {0} not found on sheet {1}.").format(line_idx, sheet_name))

    line.counted_qty = flt(counted_qty)
    line.counted_at = now_datetime()
    line.counted_by = frappe.session.user
    line.skip_reason = None

    if sheet.status == "Draft":
        sheet.status = "Counting"

    sheet.save()
    return {"ok": True, "line_idx": line.idx, "counted_at": str(line.counted_at)}


@frappe.whitelist()
def skip_line(sheet_name: str, line_idx: int, reason: str) -> dict:
    """Mark a line as explicitly skipped. Required by coverage check."""
    if not reason or not reason.strip():
        frappe.throw(_("skip_reason is required when skipping a line."))

    sheet = frappe.get_doc("VCL Stock Count Sheet", sheet_name)
    if sheet.status not in ("Draft", "Counting"):
        frappe.throw(_("Cannot skip lines on a sheet in status {0}.").format(sheet.status))

    line = next((l for l in sheet.lines if l.idx == int(line_idx)), None)
    if not line:
        frappe.throw(_("Line idx {0} not found on sheet {1}.").format(line_idx, sheet_name))

    line.skip_reason = reason.strip()
    line.counted_at = now_datetime()
    line.counted_by = frappe.session.user
    sheet.save()
    return {"ok": True, "line_idx": line.idx}

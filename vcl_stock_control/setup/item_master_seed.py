"""
Seed VCL Item Map (and optionally the underlying ERPNext Item master) with the
Brown Paper Reels matrix variants for the v1 pilot.

Reads vcl_stock_control/setup/item_reconciliation_decisions.csv if present
(signed off by Tony + Tanuj + Radhika), else uses an inline 21-row stub.

Each row sets vcl_key, canonical_label, sheet_code, pattern,
reconciliation_status, and (when REUSE/RECONCILE) erpnext_item.

Bench entry points:
    bench --site <site> execute vcl_stock_control.setup.item_master_seed.run
    bench --site <site> execute vcl_stock_control.setup.item_master_seed.run \
        --kwargs "{'create_missing_items': True, 'item_group': 'Raw Material'}"
"""
from __future__ import annotations

import csv
from pathlib import Path

import frappe


SHEET_CODE = "BROWN_PAPER_REELS"
PATTERN = "Multi-Warehouse Matrix"
DEFAULT_ITEM_GROUP = "Raw Material"


def _decisions_path() -> Path:
    return Path(frappe.get_app_path("vcl_stock_control")) / "setup" / "item_reconciliation_decisions.csv"


def _load_decisions() -> list[dict]:
    p = _decisions_path()
    if p.exists():
        with open(p) as f:
            return list(csv.DictReader(f))
    return _STUB


def _ensure_uom(uom: str | None):
    if uom and not frappe.db.exists("UOM", uom):
        frappe.get_doc({"doctype": "UOM", "uom_name": uom, "must_be_whole_number": 0}).insert(
            ignore_permissions=True
        )


def _ensure_item_group(group: str):
    if not frappe.db.exists("Item Group", group):
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": group,
            "is_group": 0,
            "parent_item_group": "All Item Groups",
        }).insert(ignore_permissions=True)


def _ensure_item(row: dict, item_group: str) -> str:
    """Create the ERPNext Item if it doesn't exist; return its item_code.
    item_code = vcl_key so the canonical key and ERPNext code stay in sync
    on a greenfield deploy. RECONCILE rows that already point at a legacy
    code are left alone."""
    if row.get("erpnext_item"):
        return row["erpnext_item"]

    item_code = row["vcl_key"]
    if frappe.db.exists("Item", item_code):
        return item_code

    _ensure_uom(row.get("uom") or "Nos")
    _ensure_item_group(item_group)

    frappe.get_doc({
        "doctype": "Item",
        "item_code": item_code,
        "item_name": row["canonical_label"],
        "item_group": item_group,
        "stock_uom": row.get("uom") or "Nos",
        "is_stock_item": 1,
        "include_item_in_manufacturing": 0,
        "description": row["canonical_label"],
    }).insert(ignore_permissions=True)
    return item_code


def _upsert(row: dict, create_missing_items: bool, item_group: str) -> str:
    name = row["vcl_key"]
    if frappe.db.exists("VCL Item Map", name):
        doc = frappe.get_doc("VCL Item Map", name)
        action = "updated"
    else:
        doc = frappe.new_doc("VCL Item Map")
        doc.vcl_key = name
        action = "created"

    doc.canonical_label = row["canonical_label"]
    doc.sheet_code = row.get("sheet_code", SHEET_CODE)
    doc.pattern = row.get("pattern", PATTERN)
    doc.uom = row.get("uom") or None
    doc.default_warehouse = row.get("default_warehouse") or None
    doc.legacy_codes = row.get("legacy_codes") or None
    doc.variant_attributes = row.get("variant_attributes") or None
    doc.is_active = int(row.get("is_active", 1))
    doc.notes = row.get("notes") or None

    if create_missing_items:
        item_code = _ensure_item(row, item_group)
        doc.erpnext_item = item_code
        doc.reconciliation_status = row.get("reconciliation_status") or "REUSE"
    else:
        doc.erpnext_item = row.get("erpnext_item") or None
        doc.reconciliation_status = row.get("reconciliation_status", "PENDING")

    doc.save(ignore_permissions=True)
    return f"{action}:{name}"


def run(create_missing_items: bool = False, item_group: str = DEFAULT_ITEM_GROUP) -> dict:
    decisions = _load_decisions()
    results = []
    for row in decisions:
        results.append(_upsert(row, create_missing_items=create_missing_items, item_group=item_group))
    frappe.db.commit()
    summary = {
        "rows": len(results),
        "created": sum(1 for r in results if r.startswith("created:")),
        "updated": sum(1 for r in results if r.startswith("updated:")),
        "items_created_if_missing": create_missing_items,
        "item_group": item_group if create_missing_items else None,
    }
    print(f"[item_master_seed] {summary}")
    return summary


_STUB: list[dict] = [
    {
        "vcl_key": f"BPR-{gsm}GSM-{w}MM",
        "canonical_label": f"Brown Paper Reel {gsm}gsm {w}mm",
        "sheet_code": SHEET_CODE,
        "pattern": PATTERN,
        "reconciliation_status": "REUSE",
        "uom": "Kg",
        "variant_attributes": f'{{"gsm": {gsm}, "width_mm": {w}}}',
    }
    for gsm in (35, 40, 44, 50, 60, 70, 80)
    for w in (760, 1010, 1270)
][:21]

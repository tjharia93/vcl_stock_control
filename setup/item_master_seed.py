"""
Seed VCL Item Map with the Brown Paper Reels matrix variants for the v1 pilot.

Reads setup/item_reconciliation_decisions.csv if present (signed off by Tony +
Tanuj + Radhika), else uses an inline stub for the 21 BPR variants.

Each row sets vcl_key, canonical_label, sheet_code, pattern, reconciliation_status,
and (when REUSE/RECONCILE) erpnext_item.

Run with bench:
    bench --site <site> execute vcl_stock_control.setup.item_master_seed.run
"""
from __future__ import annotations

import csv
from pathlib import Path

import frappe


SHEET_CODE = "BROWN_PAPER_REELS"
PATTERN = "Multi-Warehouse Matrix"


def _decisions_path() -> Path:
    return Path(frappe.get_app_path("vcl_stock_control")).parent / "setup" / "item_reconciliation_decisions.csv"


def _load_decisions() -> list[dict]:
    p = _decisions_path()
    if p.exists():
        with open(p) as f:
            return list(csv.DictReader(f))
    return _STUB


def _upsert(row: dict) -> str:
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
    doc.reconciliation_status = row.get("reconciliation_status", "PENDING")
    doc.erpnext_item = row.get("erpnext_item") or None
    doc.uom = row.get("uom") or None
    doc.default_warehouse = row.get("default_warehouse") or None
    doc.legacy_codes = row.get("legacy_codes") or None
    doc.variant_attributes = row.get("variant_attributes") or None
    doc.is_active = int(row.get("is_active", 1))
    doc.notes = row.get("notes") or None
    doc.save(ignore_permissions=True)
    return f"{action}:{name}"


def run() -> dict:
    decisions = _load_decisions()
    results = []
    for row in decisions:
        results.append(_upsert(row))
    frappe.db.commit()
    summary = {
        "rows": len(results),
        "created": sum(1 for r in results if r.startswith("created:")),
        "updated": sum(1 for r in results if r.startswith("updated:")),
    }
    print(f"[item_master_seed] {summary}")
    return summary


_STUB: list[dict] = [
    {
        "vcl_key": f"BPR-{gsm}GSM-{w}MM",
        "canonical_label": f"Brown Paper Reel {gsm}gsm {w}mm",
        "sheet_code": SHEET_CODE,
        "pattern": PATTERN,
        "reconciliation_status": "PENDING",
        "uom": "Kg",
        "variant_attributes": f'{{"gsm": {gsm}, "width_mm": {w}}}',
    }
    for gsm in (35, 40, 44, 50, 60, 70, 80)
    for w in (760, 1010, 1270)
][:21]

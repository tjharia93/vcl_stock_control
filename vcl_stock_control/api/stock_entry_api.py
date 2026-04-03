import frappe
from frappe import _
from vcl_stock_control.stock_utils import _get_item_uom_conversion


@frappe.whitelist()
def get_ink_item_details(item_code):
    """Fetch all item data needed by the website page in one call.

    Returns item_name, stock_uom, valid UOMs with conversion factors,
    and optional stock_category.
    """
    if not item_code:
        frappe.throw(_("Item Code is required"))

    item = frappe.get_doc("Item", item_code)

    valid_uoms = []
    for uom_row in item.uoms:
        valid_uoms.append({
            "uom": uom_row.uom,
            "conversion_factor": uom_row.conversion_factor,
        })

    return {
        "item": item.name,
        "item_name": item.item_name,
        "stock_uom": item.stock_uom,
        "valid_uoms": valid_uoms,
        "stock_category": "",
    }


@frappe.whitelist()
def get_item_conversion_factor(item_code, from_uom, to_uom):
    """Return conversion factor for the selected item and UOM pair.

    Uses ERPNext Item's built-in UOM Conversion Detail table.
    """
    if not item_code or not from_uom or not to_uom:
        return 0

    if from_uom == to_uom:
        return 1.0

    factor = _get_item_uom_conversion(item_code, from_uom, to_uom)
    return factor or 0


@frappe.whitelist()
def create_ink_chemical_stock_entry(payload):
    """Create an Ink Chemical Stock Entry from website JSON payload.

    Payload shape:
    {
        "posting_date": "2026-04-03",
        "department": "Printing",
        "location": "Main Store",
        "remarks": "",
        "items": [
            {
                "item": "INK-001",
                "entry_uom": "Bottle",
                "entry_qty": 3,
                "supplier": "",
                "batch_no": "",
                "expiry_date": "",
                "notes": ""
            }
        ],
        "action": "save" or "submit"
    }
    """
    data = frappe.parse_json(payload)

    if not data.get("items"):
        frappe.throw(_("At least one stock line is required."))

    doc = frappe.new_doc("Ink Chemical Stock Entry")
    doc.posting_date = data.get("posting_date") or frappe.utils.today()
    doc.department = data.get("department", "")
    doc.location = data.get("location", "")
    doc.remarks = data.get("remarks", "")

    for row in data.get("items", []):
        item_code = row.get("item")
        if not item_code:
            frappe.throw(_("Item is required in every stock line."))

        # Fetch item details server-side for security
        item_doc = frappe.get_doc("Item", item_code)
        entry_uom = row.get("entry_uom") or item_doc.stock_uom
        entry_qty = frappe.utils.flt(row.get("entry_qty"))

        if entry_qty < 0:
            frappe.throw(_("Entry Qty cannot be negative for item {0}").format(item_code))

        # Recalculate conversion factor server-side
        if entry_uom == item_doc.stock_uom:
            conversion_factor = 1.0
        else:
            conversion_factor = _get_item_uom_conversion(item_code, entry_uom, item_doc.stock_uom)
            if not conversion_factor:
                frappe.throw(
                    _("No UOM conversion found for {0} from {1} to {2}").format(
                        item_code, entry_uom, item_doc.stock_uom
                    )
                )

        qty_in_default_uom = entry_qty * frappe.utils.flt(conversion_factor)

        doc.append("items", {
            "item": item_code,
            "item_name": item_doc.item_name,
            "default_uom": item_doc.stock_uom,
            "entry_uom": entry_uom,
            "entry_qty": entry_qty,
            "conversion_factor": conversion_factor,
            "qty_in_default_uom": qty_in_default_uom,
            "supplier": row.get("supplier", ""),
            "batch_no": row.get("batch_no", ""),
            "expiry_date": row.get("expiry_date") or None,
            "notes": row.get("notes", ""),
        })

    doc.insert(ignore_permissions=False)

    action = data.get("action", "save")
    if action == "submit":
        doc.submit()

    return {
        "name": doc.name,
        "docstatus": doc.docstatus,
        "message": _("Ink Chemical Stock Entry {0} {1} successfully").format(
            doc.name, "submitted" if doc.docstatus == 1 else "saved as draft"
        ),
    }

# Ink Chemical Stock Entry - Website Page

## Overview

Operator-facing website page for entering ink and chemical stock. Provides a cleaner UI than Desk while writing into the same backend DocTypes.

**URL:** `/ink-chemical-entry`

## How It Works

### Page Flow
1. User opens `/ink-chemical-entry` (must be logged in)
2. Fills header: Posting Date, Department, Location, Remarks
3. Clicks **+ Add Line** to add stock rows
4. Types item code/name - autocomplete dropdown appears
5. Selects item - system fills Item Name, Default UOM, Entry UOM options
6. Selects Entry UOM and enters Entry Qty
7. System calculates Qty in Default UOM live
8. Clicks **Save Draft** or **Save & Submit**
9. Document is created in `Ink Chemical Stock Entry` DocType

### What Gets Created
- Parent: `Ink Chemical Stock Entry` (with naming series ICSE-.YYYY.-.#####)
- Children: `Ink Chemical Stock Entry Line` (one per stock line)
- Save Draft = docstatus 0
- Save & Submit = docstatus 1

## File Structure

```
vcl_stock_control/
  api/
    stock_entry_api.py        # 3 whitelisted API methods
  www/
    ink-chemical-entry.html   # Page template (Jinja)
    ink-chemical-entry.py     # Page context controller
  public/
    js/ink_chemical_entry.js  # All client-side logic
    css/ink_chemical_entry.css # Page styling
```

## API Methods

### `get_ink_item_details(item_code)`
Returns item_name, stock_uom, and list of valid UOMs with conversion factors from the Item's UOM Conversion Detail table.

### `get_item_conversion_factor(item_code, from_uom, to_uom)`
Returns a single conversion factor. Uses ERPNext Item's built-in UOM table.

### `create_ink_chemical_stock_entry(payload)`
Creates the document from JSON payload. Server-side recalculates conversion factors for security. Supports `action: "save"` or `action: "submit"`.

**Payload shape:**
```json
{
    "posting_date": "2026-04-03",
    "department": "Printing",
    "location": "Main Store",
    "remarks": "",
    "items": [
        {
            "item": "AGBR - BLANKET REPAIR KIT",
            "entry_uom": "Bottle",
            "entry_qty": 3,
            "supplier": "LABCHEM",
            "batch_no": "",
            "expiry_date": "",
            "notes": ""
        }
    ],
    "action": "submit"
}
```

## Security
- Page requires login (Guest users redirected)
- API methods are `@frappe.whitelist()` (logged-in users only)
- Document creation respects DocType role permissions
- Backend recalculates conversion factors (does not trust client values)
- Submit only works if user has submit permission on the DocType

## Permissions Required
| Action | Minimum Role |
|--------|-------------|
| View page | Any logged-in user |
| Save draft | Stock User |
| Submit | Stock Manager |
| Cancel | Stock Manager |

## Header Fields
| Field | Required | Default |
|-------|----------|---------|
| Posting Date | Yes | Today |
| Department | No | - |
| Location | Yes | - |
| Remarks | No | - |

## Line Fields
| Field | Editable | Auto-filled |
|-------|----------|-------------|
| Item | Yes (autocomplete) | - |
| Item Name | No | From Item |
| Default UOM | No | From Item.stock_uom |
| Entry UOM | Yes (dropdown) | Options from Item UOMs |
| Entry Qty | Yes | - |
| Conversion Factor | No | From Item UOM table |
| Qty in Default UOM | No | entry_qty x conversion_factor |
| Supplier | Yes | - |
| Batch No | Yes | - |
| Expiry Date | Yes | - |
| Notes | Yes | - |

## Responsive
- Mobile-friendly layout
- On small screens: Supplier, Batch No, Expiry, Notes columns hidden
- Action buttons stack vertically on mobile

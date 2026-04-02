import frappe


def get_conversion_factor(from_uom, to_uom, item=None, material_profile=None, stock_category=None):
    """
    Get conversion factor with priority:
    1. Exact Item rule
    2. Exact Material Profile rule
    3. Stock Category rule
    4. Returns None if not found (caller must handle)
    """
    if from_uom == to_uom:
        return 1.0

    # Priority 1: Item-specific rule
    if item:
        factor = frappe.db.get_value(
            "Stock UOM Conversion Rule",
            {"conversion_for": "Item", "item": item, "from_uom": from_uom, "to_uom": to_uom, "is_active": 1},
            "conversion_factor",
        )
        if factor:
            return float(factor)

    # Priority 2: Material Profile rule
    if material_profile:
        factor = frappe.db.get_value(
            "Stock UOM Conversion Rule",
            {
                "conversion_for": "Material Profile",
                "material_profile": material_profile,
                "from_uom": from_uom,
                "to_uom": to_uom,
                "is_active": 1,
            },
            "conversion_factor",
        )
        if factor:
            return float(factor)

    # Priority 3: Stock Category rule
    if stock_category:
        factor = frappe.db.get_value(
            "Stock UOM Conversion Rule",
            {
                "conversion_for": "Stock Category",
                "stock_category": stock_category,
                "from_uom": from_uom,
                "to_uom": to_uom,
                "is_active": 1,
            },
            "conversion_factor",
        )
        if factor:
            return float(factor)

    return None


def calculate_qty_in_default_uom(entry_qty, conversion_factor):
    """Calculate qty_in_default_uom = entry_qty * conversion_factor."""
    if entry_qty is not None and conversion_factor:
        return float(entry_qty) * float(conversion_factor)
    return 0.0


def validate_stock_lines(doc, items_field="items"):
    """Common validation for all stock entry child tables."""
    if not doc.get(items_field):
        frappe.throw(f"At least one stock line is required in {doc.doctype}.")

    for row in doc.get(items_field):
        if not row.default_uom:
            frappe.throw(f"Row {row.idx}: Default UOM is required.")
        if not row.entry_uom:
            frappe.throw(f"Row {row.idx}: Entry UOM is required.")
        if not row.entry_qty and row.entry_qty != 0:
            frappe.throw(f"Row {row.idx}: Entry Qty is required.")
        if row.entry_qty and row.entry_qty < 0:
            frappe.throw(f"Row {row.idx}: Entry Qty cannot be negative.")

        # Auto-calculate conversion factor if not set and UOMs differ
        if row.entry_uom != row.default_uom and not row.conversion_factor:
            item = getattr(row, "item", None)
            material_profile = getattr(row, "material_profile", None)
            stock_category = getattr(row, "stock_category", None)

            factor = get_conversion_factor(
                row.entry_uom, row.default_uom,
                item=item, material_profile=material_profile,
                stock_category=stock_category,
            )
            if factor:
                row.conversion_factor = factor
            else:
                frappe.throw(
                    f"Row {row.idx}: No conversion rule found from {row.entry_uom} to {row.default_uom}. "
                    "Please enter the Conversion Factor manually or create a Stock UOM Conversion Rule."
                )

        # Set conversion factor to 1 if same UOM
        if row.entry_uom == row.default_uom:
            row.conversion_factor = 1.0

        # Calculate qty_in_default_uom
        row.qty_in_default_uom = calculate_qty_in_default_uom(row.entry_qty, row.conversion_factor)

        if row.qty_in_default_uom < 0:
            frappe.throw(f"Row {row.idx}: Qty in Default UOM cannot be negative.")


def validate_material_source(row, require_item=False):
    """Validate that a stock line has either an item, material_profile, or manual_description."""
    if require_item:
        if not getattr(row, "item", None):
            frappe.throw(f"Row {row.idx}: Item is required.")
    else:
        has_profile = getattr(row, "material_profile", None)
        has_manual = getattr(row, "manual_description", None)
        if not has_profile and not has_manual:
            frappe.throw(f"Row {row.idx}: Either Material Profile or Manual Description is required.")


@frappe.whitelist()
def fetch_conversion_factor(from_uom, to_uom, item=None, material_profile=None, stock_category=None):
    """Whitelisted method for client-side conversion factor lookup."""
    factor = get_conversion_factor(from_uom, to_uom, item=item, material_profile=material_profile, stock_category=stock_category)
    return factor or 0

import frappe


def _get_item_uom_conversion(item, from_uom, to_uom):
    """
    Look up conversion from ERPNext Item's built-in UOM Conversion Detail table.

    The Item stores conversions as: UOM -> stock_uom with a conversion_factor.
    E.g. if stock_uom = Millilitre and Bottle has factor 100,
    that means 1 Bottle = 100 Millilitre.
    """
    try:
        stock_uom = frappe.db.get_value("Item", item, "stock_uom")
        if not stock_uom:
            return None

        # Case 1: entry_uom is in UOM table, to_uom is stock_uom
        # Factor means: 1 entry_uom = factor × stock_uom
        if to_uom == stock_uom:
            factor = frappe.db.get_value(
                "UOM Conversion Detail",
                {"parent": item, "parenttype": "Item", "uom": from_uom},
                "conversion_factor",
            )
            if factor:
                return float(factor)

        # Case 2: from_uom is stock_uom, to_uom is in the table (inverse)
        if from_uom == stock_uom:
            factor = frappe.db.get_value(
                "UOM Conversion Detail",
                {"parent": item, "parenttype": "Item", "uom": to_uom},
                "conversion_factor",
            )
            if factor and float(factor) != 0:
                return 1.0 / float(factor)

        # Case 3: Neither is stock_uom - cross-convert via stock_uom
        from_factor = frappe.db.get_value(
            "UOM Conversion Detail",
            {"parent": item, "parenttype": "Item", "uom": from_uom},
            "conversion_factor",
        )
        to_factor = frappe.db.get_value(
            "UOM Conversion Detail",
            {"parent": item, "parenttype": "Item", "uom": to_uom},
            "conversion_factor",
        )
        if from_factor and to_factor and float(to_factor) != 0:
            return float(from_factor) / float(to_factor)

    except Exception:
        pass

    return None


def get_conversion_factor(from_uom, to_uom, item=None, material_profile=None, stock_category=None):
    """
    Get conversion factor.

    For Item-linked entries: uses ERPNext Item UOM Conversion Detail only.
    For manual entries: uses custom Stock UOM Conversion Rule
        (Material Profile level, then Stock Category level).
    """
    if from_uom == to_uom:
        return 1.0

    # Item-linked: use ERPNext Item UOM table only
    if item:
        factor = _get_item_uom_conversion(item, from_uom, to_uom)
        if factor:
            return factor

    # Manual stock: Material Profile rule
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

    # Manual stock: Stock Category rule
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
                    "Please enter the Conversion Factor manually or add the UOM conversion on the Item."
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

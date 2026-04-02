import frappe
from collections import defaultdict


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 150},
        {"label": "Default UOM", "fieldname": "default_uom", "fieldtype": "Data", "width": 100},
        {"label": "Material Count", "fieldname": "material_count", "fieldtype": "Int", "width": 120},
        {"label": "Total Qty in Default UOM", "fieldname": "total_qty", "fieldtype": "Float", "width": 180},
    ]


def get_data(filters):
    # Aggregate latest submitted stock by category + UOM
    summary = defaultdict(lambda: {"material_count": 0, "total_qty": 0.0})

    doctypes = [
        {"parent": "Ink Chemical Stock Entry", "child": "Ink Chemical Stock Entry Line",
         "category": "Ink / Chemical", "source_field": "item"},
        {"parent": "Raw Material Stock Entry", "child": "Raw Material Stock Entry Line",
         "category": "Raw Material", "source_field": "material_profile"},
        {"parent": "Finished Goods Stock Entry", "child": "Finished Goods Stock Entry Line",
         "category": "Finished Goods", "source_field": "material_profile"},
        {"parent": "Core Stock Entry", "child": "Core Stock Entry Line",
         "category": "Core", "source_field": "material_profile"},
        {"parent": "Spare Stock Entry", "child": "Spare Stock Entry Line",
         "category": "Spare", "source_field": "material_profile"},
        {"parent": "Fuel Stock Entry", "child": "Fuel Stock Entry Line",
         "category": "Fuel", "source_field": "material_profile"},
    ]

    for dt in doctypes:
        try:
            rows = frappe.db.sql("""
                SELECT
                    c.{source_field} as material,
                    c.default_uom,
                    c.qty_in_default_uom,
                    p.posting_date
                FROM `tab{child}` c
                INNER JOIN `tab{parent}` p ON c.parent = p.name
                WHERE p.docstatus = 1
                ORDER BY p.posting_date DESC
            """.format(
                source_field=dt["source_field"],
                child=dt["child"],
                parent=dt["parent"],
            ), as_dict=True)

            # Get latest entry per material
            seen = set()
            for row in rows:
                key = row.material or ""
                if key and key not in seen:
                    seen.add(key)
                    uom = row.default_uom or "Unknown"
                    cat_key = (dt["category"], uom)
                    summary[cat_key]["material_count"] += 1
                    summary[cat_key]["total_qty"] += row.qty_in_default_uom or 0
        except Exception:
            pass

    data = []
    for (category, uom), vals in sorted(summary.items()):
        data.append({
            "category": category,
            "default_uom": uom,
            "material_count": vals["material_count"],
            "total_qty": vals["total_qty"],
        })

    return data

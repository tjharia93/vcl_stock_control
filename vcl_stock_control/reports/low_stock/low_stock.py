import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 120},
        {"label": "Material / Item", "fieldname": "material", "fieldtype": "Data", "width": 250},
        {"label": "Default UOM", "fieldname": "default_uom", "fieldtype": "Data", "width": 100},
        {"label": "Latest Qty", "fieldname": "latest_qty", "fieldtype": "Float", "width": 120},
        {"label": "Minimum Level", "fieldname": "minimum_level", "fieldtype": "Float", "width": 120},
        {"label": "Reorder Flag", "fieldname": "reorder_flag", "fieldtype": "Check", "width": 100},
        {"label": "Entry Reference", "fieldname": "entry_ref", "fieldtype": "Data", "width": 180},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
    ]


def get_data(filters):
    data = []

    # Spare Stock Entry - has reorder_flag and minimum_level on lines
    try:
        rows = frappe.db.sql("""
            SELECT
                c.material_profile as material,
                c.manual_description as description,
                c.default_uom,
                c.qty_in_default_uom,
                c.minimum_level,
                c.reorder_flag,
                p.name as entry_ref,
                p.posting_date
            FROM `tabSpare Stock Entry Line` c
            INNER JOIN `tabSpare Stock Entry` p ON c.parent = p.name
            WHERE p.docstatus = 1
                AND c.minimum_level > 0
                AND c.qty_in_default_uom < c.minimum_level
            ORDER BY p.posting_date DESC
        """, as_dict=True)

        seen = set()
        for row in rows:
            key = row.material or row.description or ""
            if key and key not in seen:
                seen.add(key)
                data.append({
                    "category": "Spare",
                    "material": row.material or row.description or "",
                    "default_uom": row.default_uom or "",
                    "latest_qty": row.qty_in_default_uom or 0,
                    "minimum_level": row.minimum_level or 0,
                    "reorder_flag": 1,
                    "entry_ref": row.entry_ref,
                    "posting_date": row.posting_date,
                })
    except Exception:
        pass

    # Material Profiles with minimum_level set - check latest entries across all doctypes
    try:
        profiles = frappe.db.sql("""
            SELECT name, material_profile_name, stock_category, default_uom, minimum_level
            FROM `tabStock Material Profile`
            WHERE minimum_level > 0 AND is_active = 1
        """, as_dict=True)

        profile_doctypes = [
            ("Raw Material Stock Entry", "Raw Material Stock Entry Line"),
            ("Finished Goods Stock Entry", "Finished Goods Stock Entry Line"),
            ("Core Stock Entry", "Core Stock Entry Line"),
            ("Fuel Stock Entry", "Fuel Stock Entry Line"),
        ]

        for profile in profiles:
            for parent_dt, child_dt in profile_doctypes:
                try:
                    latest = frappe.db.sql("""
                        SELECT c.qty_in_default_uom, p.name as entry_ref, p.posting_date
                        FROM `tab{child}` c
                        INNER JOIN `tab{parent}` p ON c.parent = p.name
                        WHERE p.docstatus = 1 AND c.material_profile = %(profile)s
                        ORDER BY p.posting_date DESC
                        LIMIT 1
                    """.format(child=child_dt, parent=parent_dt),
                        {"profile": profile.name}, as_dict=True)

                    if latest and latest[0].qty_in_default_uom < profile.minimum_level:
                        data.append({
                            "category": profile.stock_category or "",
                            "material": profile.material_profile_name,
                            "default_uom": profile.default_uom or "",
                            "latest_qty": latest[0].qty_in_default_uom or 0,
                            "minimum_level": profile.minimum_level,
                            "reorder_flag": 1,
                            "entry_ref": latest[0].entry_ref,
                            "posting_date": latest[0].posting_date,
                        })
                except Exception:
                    pass
    except Exception:
        pass

    return data

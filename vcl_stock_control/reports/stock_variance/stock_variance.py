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
        {"label": "Previous Qty", "fieldname": "previous_qty", "fieldtype": "Float", "width": 120},
        {"label": "Previous Date", "fieldname": "previous_date", "fieldtype": "Date", "width": 110},
        {"label": "Current Qty", "fieldname": "current_qty", "fieldtype": "Float", "width": 120},
        {"label": "Current Date", "fieldname": "current_date", "fieldtype": "Date", "width": 110},
        {"label": "Variance", "fieldname": "variance", "fieldtype": "Float", "width": 120},
        {"label": "Variance %", "fieldname": "variance_pct", "fieldtype": "Percent", "width": 110},
    ]


def get_data(filters):
    if not filters or not filters.get("previous_date") or not filters.get("current_date"):
        return []

    data = []

    doctypes = [
        {"parent": "Ink Chemical Stock Entry", "child": "Ink Chemical Stock Entry Line",
         "category": "Ink / Chemical", "source_field": "item", "material_field": "item_name"},
        {"parent": "Raw Material Stock Entry", "child": "Raw Material Stock Entry Line",
         "category": "Raw Material", "source_field": "material_profile", "material_field": "manual_description"},
        {"parent": "Finished Goods Stock Entry", "child": "Finished Goods Stock Entry Line",
         "category": "Finished Goods", "source_field": "material_profile", "material_field": "manual_description"},
        {"parent": "Core Stock Entry", "child": "Core Stock Entry Line",
         "category": "Core", "source_field": "material_profile", "material_field": "manual_description"},
        {"parent": "Spare Stock Entry", "child": "Spare Stock Entry Line",
         "category": "Spare", "source_field": "material_profile", "material_field": "manual_description"},
        {"parent": "Fuel Stock Entry", "child": "Fuel Stock Entry Line",
         "category": "Fuel", "source_field": "material_profile", "material_field": "manual_description"},
    ]

    for dt in doctypes:
        if filters.get("stock_category") and dt["category"] != filters["stock_category"]:
            continue

        try:
            def get_snapshot(date):
                rows = frappe.db.sql("""
                    SELECT
                        c.{source_field} as material,
                        c.{material_field} as description,
                        c.default_uom,
                        c.qty_in_default_uom,
                        p.posting_date
                    FROM `tab{child}` c
                    INNER JOIN `tab{parent}` p ON c.parent = p.name
                    WHERE p.docstatus = 1 AND p.posting_date <= %(date)s
                    ORDER BY p.posting_date DESC
                """.format(
                    source_field=dt["source_field"],
                    material_field=dt["material_field"],
                    child=dt["child"],
                    parent=dt["parent"],
                ), {"date": date}, as_dict=True)

                snapshot = {}
                for row in rows:
                    key = row.material or row.description or ""
                    if key and key not in snapshot:
                        snapshot[key] = {
                            "qty": row.qty_in_default_uom or 0,
                            "uom": row.default_uom or "",
                            "date": row.posting_date,
                        }
                return snapshot

            prev_snap = get_snapshot(filters["previous_date"])
            curr_snap = get_snapshot(filters["current_date"])

            all_materials = set(list(prev_snap.keys()) + list(curr_snap.keys()))

            for mat in sorted(all_materials):
                prev_qty = prev_snap.get(mat, {}).get("qty", 0)
                prev_date = prev_snap.get(mat, {}).get("date")
                curr_qty = curr_snap.get(mat, {}).get("qty", 0)
                curr_date = curr_snap.get(mat, {}).get("date")
                uom = curr_snap.get(mat, {}).get("uom") or prev_snap.get(mat, {}).get("uom", "")
                variance = curr_qty - prev_qty
                variance_pct = (variance / prev_qty * 100) if prev_qty else 0

                data.append({
                    "category": dt["category"],
                    "material": mat,
                    "default_uom": uom,
                    "previous_qty": prev_qty,
                    "previous_date": prev_date,
                    "current_qty": curr_qty,
                    "current_date": curr_date,
                    "variance": variance,
                    "variance_pct": variance_pct,
                })
        except Exception:
            pass

    return data

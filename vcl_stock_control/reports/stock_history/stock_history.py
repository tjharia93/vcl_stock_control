import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": "Entry Reference", "fieldname": "entry_ref", "fieldtype": "Data", "width": 180},
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 120},
        {"label": "Material / Item", "fieldname": "material", "fieldtype": "Data", "width": 250},
        {"label": "Default UOM", "fieldname": "default_uom", "fieldtype": "Data", "width": 100},
        {"label": "Qty in Default UOM", "fieldname": "qty_in_default_uom", "fieldtype": "Float", "width": 140},
        {"label": "Location", "fieldname": "location", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    data = []

    doctypes = [
        {"parent": "Ink Chemical Stock Entry", "child": "Ink Chemical Stock Entry Line",
         "category": "Ink / Chemical", "material_field": "item_name", "source_field": "item"},
        {"parent": "Raw Material Stock Entry", "child": "Raw Material Stock Entry Line",
         "category": "Raw Material", "material_field": "manual_description", "source_field": "material_profile"},
        {"parent": "Finished Goods Stock Entry", "child": "Finished Goods Stock Entry Line",
         "category": "Finished Goods", "material_field": "manual_description", "source_field": "material_profile"},
        {"parent": "Core Stock Entry", "child": "Core Stock Entry Line",
         "category": "Core", "material_field": "manual_description", "source_field": "material_profile"},
        {"parent": "Spare Stock Entry", "child": "Spare Stock Entry Line",
         "category": "Spare", "material_field": "manual_description", "source_field": "material_profile"},
        {"parent": "Fuel Stock Entry", "child": "Fuel Stock Entry Line",
         "category": "Fuel", "material_field": "manual_description", "source_field": "material_profile"},
    ]

    for dt in doctypes:
        if filters and filters.get("stock_category") and dt["category"] != filters["stock_category"]:
            continue

        try:
            conditions = "p.docstatus = 1"
            values = {}

            if filters and filters.get("from_date"):
                conditions += " AND p.posting_date >= %(from_date)s"
                values["from_date"] = filters["from_date"]
            if filters and filters.get("to_date"):
                conditions += " AND p.posting_date <= %(to_date)s"
                values["to_date"] = filters["to_date"]
            if filters and filters.get("location"):
                conditions += " AND p.location LIKE %(location)s"
                values["location"] = f"%{filters['location']}%"

            query = """
                SELECT
                    p.posting_date,
                    p.name as entry_ref,
                    c.{source_field} as material,
                    c.{material_field} as description,
                    c.default_uom,
                    c.qty_in_default_uom,
                    p.location
                FROM `tab{child}` c
                INNER JOIN `tab{parent}` p ON c.parent = p.name
                WHERE {conditions}
                ORDER BY p.posting_date ASC, p.name ASC
            """.format(
                source_field=dt["source_field"],
                material_field=dt["material_field"],
                child=dt["child"],
                parent=dt["parent"],
                conditions=conditions,
            )

            rows = frappe.db.sql(query, values, as_dict=True)
            for row in rows:
                data.append({
                    "posting_date": row.posting_date,
                    "entry_ref": row.entry_ref,
                    "category": dt["category"],
                    "material": row.material or row.description or "",
                    "default_uom": row.default_uom or "",
                    "qty_in_default_uom": row.qty_in_default_uom or 0,
                    "location": row.location or "",
                })
        except Exception:
            pass

    data.sort(key=lambda x: x.get("posting_date") or "")
    return data

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 120},
        {"label": "Source Type", "fieldname": "source_type", "fieldtype": "Data", "width": 100},
        {"label": "Material / Item", "fieldname": "material", "fieldtype": "Data", "width": 250},
        {"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 200},
        {"label": "Default UOM", "fieldname": "default_uom", "fieldtype": "Data", "width": 100},
        {"label": "Qty in Default UOM", "fieldname": "qty_in_default_uom", "fieldtype": "Float", "width": 140},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": "Entry Reference", "fieldname": "entry_ref", "fieldtype": "Data", "width": 180},
        {"label": "Location", "fieldname": "location", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    data = []

    # Define all stock entry doctypes with their child tables and source fields
    doctypes = [
        {
            "parent": "Ink Chemical Stock Entry",
            "child": "Ink Chemical Stock Entry Line",
            "category": "Ink / Chemical",
            "source_type": "Item",
            "material_field": "item_name",
            "source_field": "item",
            "location_field": "location",
        },
        {
            "parent": "Raw Material Stock Entry",
            "child": "Raw Material Stock Entry Line",
            "category": "Raw Material",
            "source_type": "Profile",
            "material_field": "manual_description",
            "source_field": "material_profile",
            "location_field": "location",
        },
        {
            "parent": "Finished Goods Stock Entry",
            "child": "Finished Goods Stock Entry Line",
            "category": "Finished Goods",
            "source_type": "Profile",
            "material_field": "manual_description",
            "source_field": "material_profile",
            "location_field": "location",
        },
        {
            "parent": "Core Stock Entry",
            "child": "Core Stock Entry Line",
            "category": "Core",
            "source_type": "Profile",
            "material_field": "manual_description",
            "source_field": "material_profile",
            "location_field": "location",
        },
        {
            "parent": "Spare Stock Entry",
            "child": "Spare Stock Entry Line",
            "category": "Spare",
            "source_type": "Profile",
            "material_field": "manual_description",
            "source_field": "material_profile",
            "location_field": "location",
        },
        {
            "parent": "Fuel Stock Entry",
            "child": "Fuel Stock Entry Line",
            "category": "Fuel",
            "source_type": "Profile",
            "material_field": "manual_description",
            "source_field": "material_profile",
            "location_field": "location",
        },
    ]

    for dt in doctypes:
        try:
            conditions = "p.docstatus = 1"
            values = {}

            if filters and filters.get("posting_date"):
                conditions += " AND p.posting_date <= %(posting_date)s"
                values["posting_date"] = filters["posting_date"]

            if filters and filters.get("location"):
                conditions += " AND p.{loc} LIKE %(location)s".format(loc=dt["location_field"])
                values["location"] = f"%{filters['location']}%"

            if filters and filters.get("stock_category") and dt["category"] != filters["stock_category"]:
                continue

            query = """
                SELECT
                    c.{material_field} as description,
                    c.{source_field} as material,
                    c.default_uom,
                    c.qty_in_default_uom,
                    p.posting_date,
                    p.name as entry_ref,
                    p.{location_field} as location
                FROM `tab{child}` c
                INNER JOIN `tab{parent}` p ON c.parent = p.name
                WHERE {conditions}
                ORDER BY p.posting_date DESC
            """.format(
                material_field=dt["material_field"],
                source_field=dt["source_field"],
                location_field=dt["location_field"],
                child=dt["child"],
                parent=dt["parent"],
                conditions=conditions,
            )

            rows = frappe.db.sql(query, values, as_dict=True)

            # Track latest entry per material
            seen = set()
            for row in rows:
                key = (row.material or row.description or "")
                if key and key not in seen:
                    seen.add(key)
                    data.append({
                        "category": dt["category"],
                        "source_type": dt["source_type"],
                        "material": row.material or "",
                        "description": row.description or "",
                        "default_uom": row.default_uom or "",
                        "qty_in_default_uom": row.qty_in_default_uom or 0,
                        "posting_date": row.posting_date,
                        "entry_ref": row.entry_ref,
                        "location": row.location or "",
                    })
        except Exception:
            pass

    return data

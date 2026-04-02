frappe.query_reports["Latest Stock Snapshot"] = {
    "filters": [
        {
            "fieldname": "posting_date",
            "label": "As On Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "stock_category",
            "label": "Stock Category",
            "fieldtype": "Link",
            "options": "Stock Category"
        },
        {
            "fieldname": "location",
            "label": "Location",
            "fieldtype": "Data"
        }
    ]
};

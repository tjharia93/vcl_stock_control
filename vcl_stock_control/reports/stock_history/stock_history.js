frappe.query_reports["Stock History"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
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

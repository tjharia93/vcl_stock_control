frappe.query_reports["Stock Variance"] = {
    "filters": [
        {
            "fieldname": "previous_date",
            "label": "Previous Date",
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "current_date",
            "label": "Current Date",
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "stock_category",
            "label": "Stock Category",
            "fieldtype": "Link",
            "options": "Stock Category"
        }
    ]
};

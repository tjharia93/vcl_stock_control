import frappe


def after_install():
    """Create default Stock Category records after app installation."""
    categories = [
        {"stock_category_name": "Ink", "is_item_linked": 1, "is_manual_only": 0},
        {"stock_category_name": "Chemical", "is_item_linked": 1, "is_manual_only": 0},
        {"stock_category_name": "Raw Material", "is_item_linked": 0, "is_manual_only": 1},
        {"stock_category_name": "Finished Goods", "is_item_linked": 0, "is_manual_only": 1},
        {"stock_category_name": "Core", "is_item_linked": 0, "is_manual_only": 1},
        {"stock_category_name": "Spare", "is_item_linked": 0, "is_manual_only": 1},
        {"stock_category_name": "Fuel", "is_item_linked": 0, "is_manual_only": 1},
    ]
    for cat in categories:
        if not frappe.db.exists("Stock Category", cat["stock_category_name"]):
            doc = frappe.new_doc("Stock Category")
            doc.update(cat)
            doc.is_active = 1
            doc.insert(ignore_permissions=True)
    frappe.db.commit()

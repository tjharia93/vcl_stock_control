frappe.ui.form.on("Ink Chemical Stock Entry", {
    // No special header-level logic needed
});

frappe.ui.form.on("Ink Chemical Stock Entry Line", {
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            frappe.db.get_value("Item", row.item, ["item_name", "stock_uom"], function(r) {
                if (r) {
                    frappe.model.set_value(cdt, cdn, "item_name", r.item_name);
                    frappe.model.set_value(cdt, cdn, "default_uom", r.stock_uom);
                }
            });
        }
    },

    entry_uom: function(frm, cdt, cdn) {
        calculate_conversion(frm, cdt, cdn);
    },

    entry_qty: function(frm, cdt, cdn) {
        calculate_default_qty(cdt, cdn);
    },

    conversion_factor: function(frm, cdt, cdn) {
        calculate_default_qty(cdt, cdn);
    }
});

function calculate_conversion(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.entry_uom && row.default_uom && row.entry_uom !== row.default_uom) {
        frappe.call({
            method: "vcl_stock_control.stock_utils.fetch_conversion_factor",
            args: {
                from_uom: row.entry_uom,
                to_uom: row.default_uom,
                item: row.item || "",
                stock_category: row.stock_category || ""
            },
            callback: function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, "conversion_factor", r.message);
                }
            }
        });
    } else if (row.entry_uom === row.default_uom) {
        frappe.model.set_value(cdt, cdn, "conversion_factor", 1);
    }
}

function calculate_default_qty(cdt, cdn) {
    let row = locals[cdt][cdn];
    let qty = (row.entry_qty || 0) * (row.conversion_factor || 1);
    frappe.model.set_value(cdt, cdn, "qty_in_default_uom", qty);
}

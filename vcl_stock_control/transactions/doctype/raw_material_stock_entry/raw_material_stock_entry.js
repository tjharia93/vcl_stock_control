frappe.ui.form.on("Raw Material Stock Entry", {
    // No special header-level logic needed
});

frappe.ui.form.on("Raw Material Stock Entry Line", {
    material_profile: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.material_profile) {
            frappe.db.get_value("Stock Material Profile", row.material_profile,
                ["material_profile_name", "default_uom", "stock_category", "colour", "gsm",
                 "size_text", "width_mm", "length_mm", "country", "mill"],
                function(r) {
                    if (r) {
                        frappe.model.set_value(cdt, cdn, "default_uom", r.default_uom);
                        frappe.model.set_value(cdt, cdn, "stock_category", r.stock_category);
                        frappe.model.set_value(cdt, cdn, "colour", r.colour);
                        frappe.model.set_value(cdt, cdn, "gsm", r.gsm);
                        frappe.model.set_value(cdt, cdn, "size_text", r.size_text);
                        frappe.model.set_value(cdt, cdn, "width_mm", r.width_mm);
                        frappe.model.set_value(cdt, cdn, "length_mm", r.length_mm);
                        frappe.model.set_value(cdt, cdn, "country", r.country);
                        frappe.model.set_value(cdt, cdn, "mill", r.mill);
                    }
                }
            );
        }
    },

    entry_uom: function(frm, cdt, cdn) {
        fetch_and_set_conversion(cdt, cdn);
    },

    entry_qty: function(frm, cdt, cdn) {
        calc_qty(cdt, cdn);
    },

    conversion_factor: function(frm, cdt, cdn) {
        calc_qty(cdt, cdn);
    }
});

function fetch_and_set_conversion(cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.entry_uom && row.default_uom && row.entry_uom !== row.default_uom) {
        frappe.call({
            method: "vcl_stock_control.stock_utils.fetch_conversion_factor",
            args: {
                from_uom: row.entry_uom,
                to_uom: row.default_uom,
                material_profile: row.material_profile || "",
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

function calc_qty(cdt, cdn) {
    let row = locals[cdt][cdn];
    let qty = (row.entry_qty || 0) * (row.conversion_factor || 1);
    frappe.model.set_value(cdt, cdn, "qty_in_default_uom", qty);
}

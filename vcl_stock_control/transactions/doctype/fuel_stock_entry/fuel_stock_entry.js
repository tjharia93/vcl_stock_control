frappe.ui.form.on("Fuel Stock Entry", {
    // No special header-level logic needed
});

frappe.ui.form.on("Fuel Stock Entry Line", {
    material_profile: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.material_profile) {
            frappe.db.get_value("Stock Material Profile", row.material_profile,
                ["material_profile_name", "default_uom"],
                function(r) {
                    if (r) {
                        frappe.model.set_value(cdt, cdn, "default_uom", r.default_uom);
                    }
                }
            );
        }
    },

    entry_uom: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.entry_uom && row.default_uom && row.entry_uom !== row.default_uom) {
            frappe.call({
                method: "vcl_stock_control.stock_utils.fetch_conversion_factor",
                args: {
                    from_uom: row.entry_uom,
                    to_uom: row.default_uom,
                    material_profile: row.material_profile || "",
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
    },

    entry_qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "qty_in_default_uom",
            (row.entry_qty || 0) * (row.conversion_factor || 1));
    },

    conversion_factor: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "qty_in_default_uom",
            (row.entry_qty || 0) * (row.conversion_factor || 1));
    }
});

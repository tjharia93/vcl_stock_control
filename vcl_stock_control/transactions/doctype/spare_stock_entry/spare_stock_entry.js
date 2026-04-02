frappe.ui.form.on("Spare Stock Entry", {
    // No special header-level logic needed
});

frappe.ui.form.on("Spare Stock Entry Line", {
    material_profile: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.material_profile) {
            frappe.db.get_value("Stock Material Profile", row.material_profile,
                ["material_profile_name", "default_uom", "part_no", "minimum_level"],
                function(r) {
                    if (r) {
                        frappe.model.set_value(cdt, cdn, "default_uom", r.default_uom);
                        frappe.model.set_value(cdt, cdn, "part_no", r.part_no);
                        frappe.model.set_value(cdt, cdn, "minimum_level", r.minimum_level);
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
        spare_calc(cdt, cdn);
    },

    conversion_factor: function(frm, cdt, cdn) {
        spare_calc(cdt, cdn);
    }
});

function spare_calc(cdt, cdn) {
    let row = locals[cdt][cdn];
    let qty = (row.entry_qty || 0) * (row.conversion_factor || 1);
    frappe.model.set_value(cdt, cdn, "qty_in_default_uom", qty);

    // Auto-set reorder flag
    if (row.minimum_level && qty < row.minimum_level) {
        frappe.model.set_value(cdt, cdn, "reorder_flag", 1);
    } else {
        frappe.model.set_value(cdt, cdn, "reorder_flag", 0);
    }
}

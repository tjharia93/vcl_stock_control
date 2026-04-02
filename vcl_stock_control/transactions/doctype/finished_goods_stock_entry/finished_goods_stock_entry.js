frappe.ui.form.on("Finished Goods Stock Entry", {
    // No special header-level logic needed
});

frappe.ui.form.on("Finished Goods Stock Entry Line", {
    material_profile: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.material_profile) {
            frappe.db.get_value("Stock Material Profile", row.material_profile,
                ["material_profile_name", "default_uom", "size_text"],
                function(r) {
                    if (r) {
                        frappe.model.set_value(cdt, cdn, "default_uom", r.default_uom);
                        frappe.model.set_value(cdt, cdn, "size_text", r.size_text);
                    }
                }
            );
        }
    },

    bundle_qty: function(frm, cdt, cdn) { calc_pieces(cdt, cdn); },
    pieces_per_bundle: function(frm, cdt, cdn) { calc_pieces(cdt, cdn); },
    carton_qty: function(frm, cdt, cdn) { calc_pieces(cdt, cdn); },
    pieces_per_carton: function(frm, cdt, cdn) { calc_pieces(cdt, cdn); },

    entry_uom: function(frm, cdt, cdn) {
        fg_fetch_conversion(cdt, cdn);
    },

    entry_qty: function(frm, cdt, cdn) {
        fg_calc_qty(cdt, cdn);
    },

    conversion_factor: function(frm, cdt, cdn) {
        fg_calc_qty(cdt, cdn);
    }
});

function calc_pieces(cdt, cdn) {
    let row = locals[cdt][cdn];
    let bundle_pcs = (row.bundle_qty || 0) * (row.pieces_per_bundle || 0);
    let carton_pcs = (row.carton_qty || 0) * (row.pieces_per_carton || 0);
    let total = bundle_pcs + carton_pcs;

    frappe.model.set_value(cdt, cdn, "calculated_pieces", total);

    // Auto-fill entry_qty if not manually set
    if (total > 0 && (!row.entry_qty || row.entry_qty === 0)) {
        frappe.model.set_value(cdt, cdn, "entry_qty", total);
        if (row.default_uom) {
            frappe.model.set_value(cdt, cdn, "entry_uom", row.default_uom);
            frappe.model.set_value(cdt, cdn, "conversion_factor", 1);
        }
    }
}

function fg_fetch_conversion(cdt, cdn) {
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
}

function fg_calc_qty(cdt, cdn) {
    let row = locals[cdt][cdn];
    let qty = (row.entry_qty || 0) * (row.conversion_factor || 1);
    frappe.model.set_value(cdt, cdn, "qty_in_default_uom", qty);
}

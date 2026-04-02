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
        let row = locals[cdt][cdn];
        if (!row.entry_uom || !row.default_uom) return;

        if (row.entry_uom === row.default_uom) {
            frappe.model.set_value(cdt, cdn, "conversion_factor", 1);
            frappe.model.set_value(cdt, cdn, "qty_in_default_uom",
                (row.entry_qty || 0) * 1);
            return;
        }

        if (!row.item) return;

        // Fetch the full Item doc to read its uoms child table
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Item",
                name: row.item
            },
            callback: function(r) {
                if (r.message && r.message.uoms) {
                    let found = false;
                    for (let uom_row of r.message.uoms) {
                        if (uom_row.uom === row.entry_uom) {
                            frappe.model.set_value(cdt, cdn, "conversion_factor", uom_row.conversion_factor);
                            frappe.model.set_value(cdt, cdn, "qty_in_default_uom",
                                (row.entry_qty || 0) * uom_row.conversion_factor);
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        frappe.msgprint({
                            title: "No Conversion Found",
                            message: "No UOM conversion for " + row.entry_uom + " on Item " + row.item + ". Enter Conversion Factor manually or add the UOM on the Item master.",
                            indicator: "orange"
                        });
                    }
                }
            }
        });
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

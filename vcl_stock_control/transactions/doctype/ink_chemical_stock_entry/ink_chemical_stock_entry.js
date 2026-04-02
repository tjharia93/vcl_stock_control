frappe.ui.form.on("Ink Chemical Stock Entry", {
    // No special header-level logic needed
});

frappe.ui.form.on("Ink Chemical Stock Entry Line", {
    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            frappe.call({
                method: "frappe.client.get",
                args: { doctype: "Item", name: row.item },
                callback: function(r) {
                    if (r.message) {
                        let item_doc = r.message;
                        frappe.model.set_value(cdt, cdn, "item_name", item_doc.item_name);
                        frappe.model.set_value(cdt, cdn, "default_uom", item_doc.stock_uom);

                        // Build list of valid UOMs from Item's UOM table
                        let valid_uoms = [];
                        if (item_doc.uoms) {
                            for (let uom_row of item_doc.uoms) {
                                valid_uoms.push(uom_row.uom);
                            }
                        }

                        // Store on row for later use by conversion lookup
                        row._item_uoms = item_doc.uoms || [];
                        row._valid_uom_list = valid_uoms;

                        // Set filter on entry_uom to only show Item's UOMs
                        set_entry_uom_filter(frm, cdn, valid_uoms);
                    }
                }
            });
        } else {
            // Clear filter if item is removed
            let row_obj = locals[cdt][cdn];
            row_obj._item_uoms = [];
            row_obj._valid_uom_list = [];
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

        // If we already have the Item UOMs cached on the row, use them
        if (row._item_uoms && row._item_uoms.length) {
            let found = false;
            for (let uom_row of row._item_uoms) {
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
                    message: "No UOM conversion for " + row.entry_uom + " on Item " + row.item,
                    indicator: "orange"
                });
            }
            return;
        }

        // Fallback: fetch Item if UOMs not cached
        frappe.call({
            method: "frappe.client.get",
            args: { doctype: "Item", name: row.item },
            callback: function(r) {
                if (r.message && r.message.uoms) {
                    row._item_uoms = r.message.uoms;
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
                            message: "No UOM conversion for " + row.entry_uom + " on Item " + row.item,
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

function set_entry_uom_filter(frm, cdn, valid_uoms) {
    frm.fields_dict.items.grid.grid_rows_by_docname[cdn] &&
    frm.fields_dict.items.grid.grid_rows_by_docname[cdn].on_grid_fields_dict &&
    frm.fields_dict.items.grid.grid_rows_by_docname[cdn].on_grid_fields_dict.entry_uom &&
    frm.fields_dict.items.grid.grid_rows_by_docname[cdn].on_grid_fields_dict.entry_uom.get_query &&
    (frm.fields_dict.items.grid.grid_rows_by_docname[cdn].on_grid_fields_dict.entry_uom.get_query = function() {
        return {
            filters: { name: ["in", valid_uoms] }
        };
    });

    // Also set via set_query on the grid field for all rows
    frm.set_query("entry_uom", "items", function(doc, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row._valid_uom_list && row._valid_uom_list.length) {
            return {
                filters: { name: ["in", row._valid_uom_list] }
            };
        }
        return {};
    });
}

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
        fetch_and_set_factor(cdt, cdn);
    },

    entry_qty: function(frm, cdt, cdn) {
        calculate_default_qty(cdt, cdn);
    },

    conversion_factor: function(frm, cdt, cdn) {
        calculate_default_qty(cdt, cdn);
    }
});

function fetch_and_set_factor(cdt, cdn) {
    let row = locals[cdt][cdn];

    if (!row.entry_uom || !row.default_uom) return;

    if (row.entry_uom === row.default_uom) {
        frappe.model.set_value(cdt, cdn, "conversion_factor", 1);
        return;
    }

    if (!row.item) return;

    // Query ERPNext Item's built-in UOM Conversion Detail table directly
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "UOM Conversion Detail",
            filters: {
                parent: row.item,
                parenttype: "Item",
                uom: row.entry_uom
            },
            fields: ["conversion_factor"],
            limit_page_length: 1
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let factor = r.message[0].conversion_factor;
                frappe.model.set_value(cdt, cdn, "conversion_factor", factor);
            } else {
                frappe.msgprint({
                    title: __("No Conversion Found"),
                    message: __("No UOM conversion found for {0} on Item {1}. Please enter Conversion Factor manually or add the UOM on the Item master.", [row.entry_uom, row.item]),
                    indicator: "orange"
                });
            }
        }
    });
}

function calculate_default_qty(cdt, cdn) {
    let row = locals[cdt][cdn];
    let qty = (row.entry_qty || 0) * (row.conversion_factor || 1);
    frappe.model.set_value(cdt, cdn, "qty_in_default_uom", qty);
}

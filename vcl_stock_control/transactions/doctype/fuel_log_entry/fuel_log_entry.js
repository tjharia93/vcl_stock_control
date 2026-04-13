frappe.ui.form.on("Fuel Log Entry", {
    refresh: function(frm) {
        // Colour the consumption flag indicator
        if (frm.doc.consumption_flag === "Warning") {
            frm.get_field("consumption_flag").$wrapper.find(".control-value").css("color", "orange");
        } else if (frm.doc.consumption_flag === "Critical") {
            frm.get_field("consumption_flag").$wrapper.find(".control-value").css("color", "red");
        } else if (frm.doc.consumption_flag === "Normal") {
            frm.get_field("consumption_flag").$wrapper.find(".control-value").css("color", "green");
        }
    },

    transaction_type: function(frm) {
        // Reset irrelevant fields when switching type
        if (frm.doc.transaction_type === "Receive") {
            frm.set_value("issue_to", "");
            frm.set_value("qty_issued", 0);
            frm.set_value("vehicle", "");
            frm.set_value("driver", "");
            frm.set_value("km_before_fueling", 0);
            frm.set_value("purpose_description", "");
        } else {
            frm.set_value("qty_received", 0);
            frm.set_value("supplier_name", "");
            frm.set_value("delivery_reference", "");
        }
    },

    issue_to: function(frm) {
        // Clear vehicle fields when switching away from Vehicle
        if (frm.doc.issue_to !== "Vehicle") {
            frm.set_value("vehicle", "");
            frm.set_value("vehicle_plate", "");
            frm.set_value("driver", "");
            frm.set_value("driver_name", "");
            frm.set_value("km_before_fueling", 0);
        }
        if (frm.doc.issue_to === "Vehicle") {
            frm.set_value("purpose_description", "");
        }
    },

    vehicle: function(frm) {
        if (frm.doc.vehicle) {
            frappe.db.get_value("Vehicle", frm.doc.vehicle, "license_plate", function(r) {
                if (r && r.license_plate) {
                    frm.set_value("vehicle_plate", r.license_plate);
                }
            });
        } else {
            frm.set_value("vehicle_plate", "");
        }
    },

    driver: function(frm) {
        if (frm.doc.driver) {
            frappe.db.get_value("Employee", frm.doc.driver, "employee_name", function(r) {
                if (r && r.employee_name) {
                    frm.set_value("driver_name", r.employee_name);
                }
            });
        } else {
            frm.set_value("driver_name", "");
        }
    },

    issued_by: function(frm) {
        if (frm.doc.issued_by) {
            frappe.db.get_value("Employee", frm.doc.issued_by, "employee_name", function(r) {
                if (r && r.employee_name) {
                    frm.set_value("issued_by_name", r.employee_name);
                }
            });
        } else {
            frm.set_value("issued_by_name", "");
        }
    }
});

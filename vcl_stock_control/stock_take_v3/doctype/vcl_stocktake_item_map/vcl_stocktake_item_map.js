// Phase 1: hide conversion inputs that the selected Conversion Rule does not need.
// Logic mirrors the server-side validation in vcl_stocktake_item_map.py.

frappe.ui.form.on("VCL Stocktake Item Map", {
    refresh(frm) {
        update_conversion_visibility(frm);
    },
    conversion_rule(frm) {
        update_conversion_visibility(frm);
    },
});

function update_conversion_visibility(frm) {
    const rule = frm.doc.conversion_rule || "None";

    const show_factor = rule === "Fixed Factor" || rule === "Pack Size";
    const show_reel_dims = rule === "Reel to SQM";
    const show_avg_weight = rule === "Reel to KG";
    const show_reel_section = show_reel_dims || show_avg_weight;

    frm.toggle_display("conversion_factor", show_factor);
    frm.toggle_display("section_break_reel", show_reel_section);
    frm.toggle_display("width_mm", show_reel_dims);
    frm.toggle_display("standard_length_m", show_reel_dims);
    frm.toggle_display("avg_weight_kg", show_avg_weight);

    frm.toggle_reqd("conversion_factor", show_factor);
    frm.toggle_reqd("width_mm", show_reel_dims);
    frm.toggle_reqd("standard_length_m", show_reel_dims);
    frm.toggle_reqd("avg_weight_kg", show_avg_weight);
}

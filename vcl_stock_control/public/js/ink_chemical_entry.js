// VCL Ink Chemical Stock Entry - Website Page Logic
var VCL = VCL || {};

(function () {
    "use strict";

    var lineCounter = 0;
    var lineData = {}; // idx -> { item_uoms: [], item_details: {} }
    var itemSearchTimeout = null;

    // ─── Add Line ──────────────────────────────────────────────
    VCL.addLine = function () {
        lineCounter++;
        var template = document.getElementById("line-row-template");
        var clone = template.content.cloneNode(true);
        var row = clone.querySelector("tr");
        row.setAttribute("data-idx", lineCounter);
        row.querySelector(".line-idx").textContent = lineCounter;

        lineData[lineCounter] = { item_uoms: [], item_details: {} };

        document.getElementById("stock-lines-body").appendChild(clone);
        document.getElementById("no-lines-msg").style.display = "none";

        bindLineEvents(lineCounter);
        updateSummary();
    };

    // ─── Remove Line ───────────────────────────────────────────
    VCL.removeLine = function (idx) {
        var row = document.querySelector('tr[data-idx="' + idx + '"]');
        if (row) row.remove();
        delete lineData[idx];
        renumberLines();
        updateSummary();

        if (document.querySelectorAll(".vcl-line-row").length === 0) {
            document.getElementById("no-lines-msg").style.display = "block";
        }
    };

    // ─── Bind Events to a Line Row ─────────────────────────────
    function bindLineEvents(idx) {
        var row = document.querySelector('tr[data-idx="' + idx + '"]');

        // Item search
        var itemInput = row.querySelector('[data-field="item"]');
        itemInput.addEventListener("input", function () {
            clearTimeout(itemSearchTimeout);
            var val = this.value.trim();
            if (val.length < 2) {
                hideDropdown(idx);
                return;
            }
            itemSearchTimeout = setTimeout(function () {
                searchItems(idx, val);
            }, 300);
        });

        itemInput.addEventListener("blur", function () {
            setTimeout(function () { hideDropdown(idx); }, 200);
        });

        // Entry UOM change
        var entryUom = row.querySelector('[data-field="entry_uom"]');
        entryUom.addEventListener("change", function () {
            onEntryUomChange(idx);
        });

        // Entry Qty change
        var entryQty = row.querySelector('[data-field="entry_qty"]');
        entryQty.addEventListener("input", function () {
            calculateQty(idx);
        });

        // Remove button
        var removeBtn = row.querySelector(".vcl-remove-line");
        removeBtn.addEventListener("click", function () {
            VCL.removeLine(idx);
        });
    }

    // ─── Item Search ───────────────────────────────────────────
    function searchItems(idx, query) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item",
                filters: [
                    ["item_name", "like", "%" + query + "%"],
                    ["disabled", "=", 0]
                ],
                or_filters: [
                    ["name", "like", "%" + query + "%"]
                ],
                fields: ["name", "item_name"],
                limit_page_length: 10,
                order_by: "name asc"
            },
            callback: function (r) {
                if (r.message) {
                    showDropdown(idx, r.message);
                }
            }
        });
    }

    function showDropdown(idx, items) {
        var row = document.querySelector('tr[data-idx="' + idx + '"]');
        var dropdown = row.querySelector(".vcl-item-dropdown");
        dropdown.innerHTML = "";

        if (!items.length) {
            dropdown.innerHTML = '<div class="vcl-dropdown-item text-muted">No items found</div>';
            dropdown.style.display = "block";
            return;
        }

        items.forEach(function (item) {
            var div = document.createElement("div");
            div.className = "vcl-dropdown-item";
            div.textContent = item.name + " - " + item.item_name;
            div.addEventListener("mousedown", function (e) {
                e.preventDefault();
                selectItem(idx, item.name);
            });
            dropdown.appendChild(div);
        });
        dropdown.style.display = "block";
    }

    function hideDropdown(idx) {
        var row = document.querySelector('tr[data-idx="' + idx + '"]');
        if (row) {
            var dropdown = row.querySelector(".vcl-item-dropdown");
            if (dropdown) dropdown.style.display = "none";
        }
    }

    // ─── Select Item ───────────────────────────────────────────
    function selectItem(idx, itemCode) {
        var row = document.querySelector('tr[data-idx="' + idx + '"]');
        row.querySelector('[data-field="item"]').value = itemCode;
        hideDropdown(idx);

        // Fetch item details via API
        frappe.call({
            method: "vcl_stock_control.api.stock_entry_api.get_ink_item_details",
            args: { item_code: itemCode },
            callback: function (r) {
                if (r.message) {
                    var d = r.message;
                    lineData[idx].item_details = d;
                    lineData[idx].item_uoms = d.valid_uoms || [];

                    // Set readonly fields
                    setReadonly(row, "item_name", d.item_name);
                    setReadonly(row, "default_uom", d.stock_uom);

                    // Populate Entry UOM dropdown
                    var uomSelect = row.querySelector('[data-field="entry_uom"]');
                    uomSelect.innerHTML = '<option value="">Select UOM</option>';
                    (d.valid_uoms || []).forEach(function (u) {
                        var opt = document.createElement("option");
                        opt.value = u.uom;
                        opt.textContent = u.uom;
                        uomSelect.appendChild(opt);
                    });

                    // Reset qty fields
                    setReadonly(row, "conversion_factor", "1");
                    setReadonly(row, "qty_in_default_uom", "0.00");
                }
            }
        });
    }

    // ─── On Entry UOM Change ───────────────────────────────────
    function onEntryUomChange(idx) {
        var row = document.querySelector('tr[data-idx="' + idx + '"]');
        var entryUom = row.querySelector('[data-field="entry_uom"]').value;
        var defaultUom = row.querySelector('[data-field="default_uom"]').textContent;

        if (!entryUom || !defaultUom || defaultUom === "-") return;

        if (entryUom === defaultUom) {
            setReadonly(row, "conversion_factor", "1");
            calculateQty(idx);
            return;
        }

        // Look up from cached item UOMs
        var uoms = lineData[idx].item_uoms || [];
        var found = false;
        for (var i = 0; i < uoms.length; i++) {
            if (uoms[i].uom === entryUom) {
                setReadonly(row, "conversion_factor", uoms[i].conversion_factor);
                calculateQty(idx);
                found = true;
                break;
            }
        }

        if (!found) {
            // Fallback: call API
            var itemCode = row.querySelector('[data-field="item"]').value;
            frappe.call({
                method: "vcl_stock_control.api.stock_entry_api.get_item_conversion_factor",
                args: { item_code: itemCode, from_uom: entryUom, to_uom: defaultUom },
                callback: function (r) {
                    if (r.message) {
                        setReadonly(row, "conversion_factor", r.message);
                    } else {
                        setReadonly(row, "conversion_factor", "0");
                    }
                    calculateQty(idx);
                }
            });
        }
    }

    // ─── Calculate Qty ─────────────────────────────────────────
    function calculateQty(idx) {
        var row = document.querySelector('tr[data-idx="' + idx + '"]');
        var entryQty = parseFloat(row.querySelector('[data-field="entry_qty"]').value) || 0;
        var factor = parseFloat(row.querySelector('[data-field="conversion_factor"]').textContent) || 1;
        var result = entryQty * factor;
        setReadonly(row, "qty_in_default_uom", result.toFixed(2));
        updateSummary();
    }

    // ─── Summary ───────────────────────────────────────────────
    function updateSummary() {
        var rows = document.querySelectorAll(".vcl-line-row");
        var totalQty = 0;
        rows.forEach(function (row) {
            totalQty += parseFloat(row.querySelector('[data-field="qty_in_default_uom"]').textContent) || 0;
        });
        document.getElementById("total-lines").textContent = rows.length;
        document.getElementById("total-qty").textContent = totalQty.toFixed(2);
    }

    // ─── Build Payload ─────────────────────────────────────────
    function buildPayload(action) {
        var posting_date = document.getElementById("posting_date").value;
        var department = document.getElementById("department").value;
        var location = document.getElementById("location").value;
        var remarks = document.getElementById("remarks").value;

        if (!posting_date) {
            showMessage("Posting Date is required.", "error");
            return null;
        }
        if (!location) {
            showMessage("Location is required.", "error");
            return null;
        }

        var rows = document.querySelectorAll(".vcl-line-row");
        if (rows.length === 0) {
            showMessage("Add at least one stock line.", "error");
            return null;
        }

        var items = [];
        var valid = true;
        rows.forEach(function (row) {
            var item = row.querySelector('[data-field="item"]').value;
            var entry_uom = row.querySelector('[data-field="entry_uom"]').value;
            var entry_qty = row.querySelector('[data-field="entry_qty"]').value;

            if (!item || !entry_uom || !entry_qty) {
                showMessage("Row " + row.querySelector(".line-idx").textContent + ": Item, Entry UOM, and Entry Qty are required.", "error");
                valid = false;
                return;
            }

            items.push({
                item: item,
                entry_uom: entry_uom,
                entry_qty: parseFloat(entry_qty),
                supplier: row.querySelector('[data-field="supplier"]').value || "",
                batch_no: row.querySelector('[data-field="batch_no"]').value || "",
                expiry_date: row.querySelector('[data-field="expiry_date"]').value || "",
                notes: row.querySelector('[data-field="notes"]').value || ""
            });
        });

        if (!valid) return null;

        return {
            posting_date: posting_date,
            department: department,
            location: location,
            remarks: remarks,
            items: items,
            action: action
        };
    }

    // ─── Save Draft ────────────────────────────────────────────
    VCL.saveDraft = function () {
        var payload = buildPayload("save");
        if (!payload) return;
        submitEntry(payload);
    };

    // ─── Save & Submit ─────────────────────────────────────────
    VCL.saveSubmit = function () {
        var payload = buildPayload("submit");
        if (!payload) return;

        if (!confirm("Submit this stock entry? Submitted entries cannot be edited.")) return;
        submitEntry(payload);
    };

    function submitEntry(payload) {
        disableButtons(true);
        showMessage("Saving...", "info");

        frappe.call({
            method: "vcl_stock_control.api.stock_entry_api.create_ink_chemical_stock_entry",
            args: { payload: JSON.stringify(payload) },
            callback: function (r) {
                disableButtons(false);
                if (r.message) {
                    var msg = r.message.message + " (" + r.message.name + ")";
                    showMessage(msg, "success");

                    // Clear form after success
                    setTimeout(function () {
                        VCL.resetPage();
                    }, 2000);
                }
            },
            error: function (r) {
                disableButtons(false);
                showMessage("Error saving entry. Check the details and try again.", "error");
            }
        });
    }

    // ─── Reset Page ────────────────────────────────────────────
    VCL.resetPage = function () {
        document.getElementById("posting_date").value = frappe.datetime
            ? frappe.datetime.get_today()
            : new Date().toISOString().split("T")[0];
        document.getElementById("department").value = "";
        document.getElementById("location").value = "";
        document.getElementById("remarks").value = "";
        document.getElementById("stock-lines-body").innerHTML = "";
        document.getElementById("no-lines-msg").style.display = "block";
        lineCounter = 0;
        lineData = {};
        updateSummary();
        hideMessage();
    };

    // ─── Helpers ───────────────────────────────────────────────
    function setReadonly(row, field, value) {
        var el = row.querySelector('[data-field="' + field + '"]');
        if (el) el.textContent = value;
    }

    function renumberLines() {
        var rows = document.querySelectorAll(".vcl-line-row");
        rows.forEach(function (row, i) {
            row.querySelector(".line-idx").textContent = i + 1;
        });
    }

    function disableButtons(disabled) {
        document.getElementById("btn-save-draft").disabled = disabled;
        document.getElementById("btn-save-submit").disabled = disabled;
    }

    function showMessage(text, type) {
        var el = document.getElementById("vcl-message");
        el.textContent = text;
        el.className = "vcl-message vcl-message-" + type;
        el.style.display = "block";
    }

    function hideMessage() {
        document.getElementById("vcl-message").style.display = "none";
    }

})();

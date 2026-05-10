/* VCL Stock Portal — entry page client.
 * Implements: auto-save (30s), per-cell record_count, skip flow, totals,
 * coverage banner refresh, submit guard.
 */
(function () {
    const root = document.querySelector('.vcl-portal[data-sheet]');
    if (!root) return;

    const sheetName = root.dataset.sheet;
    const pattern = root.dataset.pattern;
    const AUTO_SAVE_MS = 30000;

    const dirty = new Map(); // line_idx -> {qty?, skip?}

    function debounce(fn, ms) {
        let t;
        return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
    }

    async function callApi(method, args) {
        const res = await fetch('/api/method/' + method, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Frappe-CSRF-Token': window.frappe?.csrf_token || ''
            },
            body: new URLSearchParams(args).toString()
        });
        if (!res.ok) throw new Error(await res.text());
        return (await res.json()).message;
    }

    async function flushDirty() {
        if (dirty.size === 0) return;
        const entries = Array.from(dirty.entries());
        dirty.clear();
        for (const [idx, change] of entries) {
            try {
                if (change.skip !== undefined && change.skip) {
                    await callApi('vcl_stock_control.api.post_to_erpnext.skip_line', {
                        sheet_name: sheetName, line_idx: idx, reason: change.skip
                    });
                } else if (change.qty !== undefined) {
                    await callApi('vcl_stock_control.api.post_to_erpnext.record_count', {
                        sheet_name: sheetName, line_idx: idx, counted_qty: change.qty
                    });
                }
            } catch (e) {
                console.error('save failed for line', idx, e);
                dirty.set(idx, change); // requeue
            }
        }
        await refreshCoverage();
        recomputeTotals();
    }

    const debouncedFlush = debounce(flushDirty, 1500);

    async function refreshCoverage() {
        try {
            const c = await callApi('vcl_stock_control.api.post_to_erpnext.coverage_status', {
                sheet_name: sheetName
            });
            document.getElementById('coverage-counted').textContent = c.counted;
            document.getElementById('coverage-skipped').textContent = c.skipped;
            const missedEl = document.getElementById('coverage-missed');
            missedEl.textContent = c.missed_count + ' missed';
            missedEl.classList.toggle('vcl-warn-text', c.missed_count > 0);

            const submitBtn = document.getElementById('btn-submit');
            const blocker = document.getElementById('submit-blocker');
            if (submitBtn) {
                submitBtn.disabled = !c.satisfied;
                blocker.textContent = c.satisfied
                    ? ''
                    : `Cannot submit: ${c.missed_count} line(s) need a count or skip reason.`;
            }
        } catch (e) {
            console.error('coverage refresh failed', e);
        }
    }

    function recomputeTotals() {
        if (pattern !== 'Multi-Warehouse Matrix') return;
        const colTotals = {};
        let grand = 0;
        document.querySelectorAll('tr[data-vcl-key]').forEach(row => {
            let rowTotal = 0;
            row.querySelectorAll('input.vcl-qty').forEach(inp => {
                const v = parseFloat(inp.value) || 0;
                rowTotal += v;
                const w = inp.dataset.warehouse;
                colTotals[w] = (colTotals[w] || 0) + v;
            });
            const totEl = row.querySelector('.vcl-row-total');
            if (totEl) totEl.textContent = rowTotal.toFixed(3);
            grand += rowTotal;
        });
        document.querySelectorAll('th.vcl-col-total').forEach(th => {
            th.textContent = (colTotals[th.dataset.warehouse] || 0).toFixed(3);
        });
        const gt = document.getElementById('vcl-grand-total');
        if (gt) gt.textContent = grand.toFixed(3);
    }

    document.querySelectorAll('input.vcl-qty').forEach(inp => {
        inp.addEventListener('input', () => {
            const idx = parseInt(inp.dataset.lineIdx, 10);
            const cur = dirty.get(idx) || {};
            cur.qty = parseFloat(inp.value) || 0;
            dirty.set(idx, cur);
            recomputeTotals();
            debouncedFlush();
        });
    });

    document.querySelectorAll('input.vcl-skip').forEach(inp => {
        inp.addEventListener('change', () => {
            const idx = parseInt(inp.dataset.lineIdx, 10);
            const reason = (inp.value || '').trim();
            if (!reason) return;
            dirty.set(idx, { skip: reason });
            debouncedFlush();
        });
    });

    setInterval(flushDirty, AUTO_SAVE_MS);
    window.addEventListener('beforeunload', flushDirty);

    document.getElementById('btn-submit')?.addEventListener('click', async () => {
        await flushDirty();
        try {
            await callApi('frappe.client.set_value', {
                doctype: 'VCL Stock Count Sheet',
                name: sheetName,
                fieldname: 'status',
                value: 'Submitted'
            });
            window.location.href = '/stock-portal/review/' + encodeURIComponent(sheetName);
        } catch (e) {
            alert('Submit failed: ' + e.message);
        }
    });

    refreshCoverage();
    recomputeTotals();
})();

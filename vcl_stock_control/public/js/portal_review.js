/* VCL Stock Portal — review page client. */
(function () {
    const root = document.querySelector('.vcl-portal[data-sheet]');
    if (!root) return;
    const sheetName = root.dataset.sheet;

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

    async function setStatus(status) {
        await callApi('frappe.client.set_value', {
            doctype: 'VCL Stock Count Sheet',
            name: sheetName,
            fieldname: 'status',
            value: status
        });
        window.location.reload();
    }

    document.getElementById('btn-send-back')?.addEventListener('click', () => setStatus('Counting'));
    document.getElementById('btn-approve')?.addEventListener('click', () => setStatus('Approved'));

    document.getElementById('btn-post')?.addEventListener('click', async () => {
        if (!confirm('Post this sheet to ERPNext as Stock Reconciliation? This is irreversible.')) return;
        try {
            const res = await callApi('vcl_stock_control.api.post_to_erpnext.post_count_sheet', {
                sheet_name: sheetName
            });
            alert('Posted. Stock Reconciliation: ' + (res.stock_reconciliations || []).join(', '));
            window.location.reload();
        } catch (e) {
            alert('Post failed: ' + e.message);
        }
    });
})();

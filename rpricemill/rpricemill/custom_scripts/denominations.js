frappe.ui.form.on('POS Closing Entry', {
    onload: function (frm) {
        let curr = [{ 'currency': 2000, 'count': 0 }, { 'currency': 500, 'count': 0 }, { 'currency': 200, 'count': 0 }, { 'currency': 100, 'count': 0 },
        { 'currency': 50, 'count': 0 }, { 'currency': 20, 'count': 0 }, { 'currency': 10, 'count': 0 }, { 'currency': 5, 'count': 0 }, { 'currency': 2, 'count': 0 },
        { 'currency': 1, 'count': 0 }, { 'currency': 0.50, 'count': 0 }];
        frm.set_value('denominations', curr);
        frappe.call({
            method: "rpricemill.custom.get_sales_summary",
            args: {
                company: frm.doc.company,
            },
            callback: function (r) {
                if (r.message) {
                    frm.doc.sales_summary = r.message
                    frm.refresh_fields();
                }
            }
        });
        frm.refresh_fields();
    },
    get_current_balance: function (frm) {
        for (var i = 0; i < (frm.doc.payment_reconciliation).length; i++) {
            frappe.call({
                method: "rpricemill.custom.get_current_balance",
                args: {
                    company: frm.doc.company,
                    freeze: true,
                    mode_of_pay: frm.doc.payment_reconciliation[i].mode_of_payment,
                    idx: i
                },
                callback: function (r) {
                    if (r.message) {
                        frm.doc.payment_reconciliation[r.message[1]].expected_amount = r.message[0]
                        frm.refresh_fields();
                    }
                }
            });
        }

    },
    calculate: function (frm) {
        var cash_amount = 0;
        for (var x = 0; x < frm.doc.denominations.length; x++) {
            cash_amount += frm.doc.denominations[x]['count'] * parseFloat(frm.doc.denominations[x]['currency']);
        }
        for (var y = 0; y < frm.doc.payment_reconciliation.length; y++) {
            if (frm.doc.payment_reconciliation[y].mode_of_payment == 'Cash') {
                frm.doc.payment_reconciliation[y]['closing_amount'] = cash_amount;
            }
        }
        frm.refresh_fields();
    },

})
frappe.ui.form.on('POS Closing Entry Detail', {

})
frappe.ui.form.on('Denominations', {
    count: function (frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        d.total = parseFloat(d.currency) * parseFloat(d.count);
        frm.refresh_fields();
    }
})

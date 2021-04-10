frappe.ui.form.on('Delivery Note', {
    store_branch: function (frm) {
        if (frm.doc.store_branch) {
            frappe.call({
                method: "rpricemill.custom.get_address",
                args: {
                    store_branch: frm.doc.store_branch,
                    freeze: true
                },
                callback: function (r) {
                    if (r.message) {
                        frm.doc.company_address = r.message
                        frm.doc.shipping_address_name = r.message
                        frm.refresh_fields();
                    }
                }
            });
        }
    }

})
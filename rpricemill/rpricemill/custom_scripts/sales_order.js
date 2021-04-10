frappe.ui.form.on('Sales Order', {
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
                        frm.doc.customer_address = r.message
                        frm.doc.shipping_address_name = r.message
                        frm.refresh_fields();
                    }
                }
            });
        }
    }

})
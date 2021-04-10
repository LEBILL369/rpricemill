frappe.ui.form.on('Purchase Receipt', {
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
                        frm.doc.supplier_address = r.message
                        frm.doc.shipping_address = r.message
                        frm.refresh_fields();
                    }
                }
            });
        }
    }

})
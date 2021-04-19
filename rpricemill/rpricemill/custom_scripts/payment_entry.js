frappe.ui.form.on('Payment Entry', {
	party: function (frm) {
		if (frm.doc.party) {
			if (frm.doc.party_type == "Customer") {
				frappe.call({
					method: "rpricemill.custom.get_mobile_number",
					args: {
						customer: frm.doc.party,
						freeze: true
					},
					callback: function (r) {
						if (r.message) {
							frm.doc.mobile_number = r.message
							frm.refresh_fields();
						}
					}
				});
			}
		}
	}
})
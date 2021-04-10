frappe.ui.form.on('Sales Invoice', {
  customer: function (frm) {
    if (frm.doc.customer) {
      frappe.call({
        method: "rpricemill.custom.get_customer_data",
        args: {
          customer: frm.doc.customer,
          company: frm.doc.company,
          freeze: true
        },
        callback: function (r) {
          if (r.message) {
            frm.doc.annual_billing = r.message["billing_this_year"]
            frm.doc.total_unpaid = r.message["total_unpaid"]
            frm.doc.loyalty_point_balance = r.message["loyalty_points"]
            frm.doc.customer_details = r.message["info"]
            frm.refresh_fields();
          }
        }
      });
    }
  },
  redeem_loyalty_points: function (frm) {
    frappe.call({
      method: "rpricemill.custom.get_account",
      args: {
        "company": frm.doc.company
      },
      callback: function (r) {
        if (r) {
          frm.set_value("loyalty_redemption_account", r.message);
          frm.refresh_fields();
        }
      }
    });
  },

})
// Copyright (c) 2025, Abhishek and contributors
// For license information, please see license.txt

frappe.ui.form.on("Apply Dealership", {
  refresh(frm) {
    set_read_only_if_not_account_manager(frm);
  },
  onload(frm) {
    set_read_only_if_not_account_manager(frm);
  },
  override(frm) {
        if (frm.doc.override) {
            frm.set_value("account_override_datetime", frappe.datetime.now_datetime());
        } else {
            frm.set_value("account_override_datetime", null);
        }
    },
    order_override(frm) {
        if (frm.doc.order_override) {
            frm.set_value("first_order_override", frappe.datetime.now_datetime());
        } else {
            frm.set_value("first_order_override", null);
        }
    }
});

function set_read_only_if_not_account_manager(frm) {
  if (!frappe.user.has_role("Account Manager")) {
    const fields = [
      "approved_amount",
      "remark",
      "attach_slip",
      "bank_transaction_id",
      "approval_date"
    ];

    fields.forEach(field => {
      frm.set_df_property(field, "read_only", 1);
    });
  }
}

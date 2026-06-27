// Copyright (c) 2026, Abhishek and contributors
// For license information, please see license.txt

frappe.ui.form.on("Deposit Amount Payment Approal", {
        refresh(frm) {
                        frm.set_df_property("slip_attach", "reqd", true);
                        frm.set_df_property("company_bank_account", "reqd", true);
                        frm.set_df_property("bank_transaction_id", "reqd", true);
                        frm.set_df_property("approval_amount", "reqd", true);
        },
});

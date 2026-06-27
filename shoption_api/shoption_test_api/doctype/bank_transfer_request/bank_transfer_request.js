// Copyright (c) 2025, Abhishek and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank Transfer Request", {
        refresh(frm) {
                   if (frm.doc.transfer_type == "Bank Transfer") {
                          frm.set_df_property("utr_number", "read_only", false);
                }else{
                        frm.set_df_property("utr_number", "read_only", true);
                }
        },
});

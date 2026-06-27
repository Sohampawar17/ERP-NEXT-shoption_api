// Copyright (c) 2025, Abhishek and contributors
// For license information, please see license.txt

frappe.ui.form.on("Raise a Complaint", {
    refresh(frm) {
            frm.trigger("render_order_html");

  },
    order_id(frm) {
        frm.trigger("render_order_html");
    },

    render_order_html(frm) {
        if (!frm.doc.order_id) {
            frm.set_df_property("order_details", "options", "");
            return;
        }

        frm.set_df_property(
            "order_details",
            "options",
            "<div style='padding:10px;color:#666;'>Loading order details...</div>"
        );

        frappe.call({
            method: "shoption_api.shoption_test_api.doctype.raise_a_complaint.raise_a_complaint.get_order_details_html",
            args: {
                order_doctype: "Sales Order", // or dynamically set based on your use case
                order_id: frm.doc.order_id
            },
            callback(r) {
                console.log("Order details HTML response:", r);
                const html = (r.message && r.message.html) ? r.message.html : "";
                frm.set_df_property("order_details", "options", html);
            }
        });
    }

});

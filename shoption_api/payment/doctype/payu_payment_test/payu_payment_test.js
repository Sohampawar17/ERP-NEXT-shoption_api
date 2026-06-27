// Copyright (c) 2025, Abhishek and contributors
// For license information, please see license.txt

frappe.ui.form.on("PayU Payment Test", {
    pay_now(frm) {
        if (!frm.doc.payu_token) {
            frappe.msgprint("Payment token not generated");
            return;
        }

        frappe.call({
            method: "shoption_api.payment.payment_api.payment_api.start_payu_payment",
            args: {
                token: frm.doc.payu_token
            },
            callback: function (r) {
                console.log(r)
                if (r.message && r.message.html) {
                    // Replace entire page with PayU auto-submit HTML
                    document.open();
                    document.write(r.message.html);
                    document.close();
                }
            }
        });
    }


});

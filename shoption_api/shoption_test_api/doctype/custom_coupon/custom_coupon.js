frappe.ui.form.on("Custom Coupon", {
    coupon_code(frm) {
        if (frm.doc.coupon_code) {
            frm.set_value(
                "coupon_code",
                frm.doc.coupon_code.toUpperCase()
            );
        }
    }
});

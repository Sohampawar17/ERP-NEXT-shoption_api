// Copyright (c) 2025
// Shopping Cart Form Scripts

frappe.ui.form.on("Shopping Cart", {
    user(frm) {
        if (!frm.doc.user) return;

        frappe.call({
            method: "get_customer_from_user",
            doc: frm.doc,
            callback(r) {
                if (!r.message || r.message.error) {
                    frappe.msgprint("No customer linked with this user");
                    return;
                }
                frm.set_value("customer", r.message.parent);
            }
        });
    },
});

frappe.ui.form.on("Cart Item", {
    item(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item) return;

        fetch_item_details(frm, cdt, cdn, row);
    },

    quantity(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item) return;

        fetch_item_details(frm, cdt, cdn, row);

        calculate_total_quantity(frm);
        calculate_total_amount(frm);
    },

    items_add(frm) {
        calculate_total_quantity(frm);
        calculate_total_amount(frm);
    },

    items_remove(frm) {
        calculate_total_quantity(frm);
        calculate_total_amount(frm);
    }
});

// ---- Fetch Item Details from Python ----
function fetch_item_details(frm, cdt, cdn, row) {
    frappe.call({
        method: "get_item_details_for_cart",
        doc: frm.doc,
        args: {
            item_code: row.item,
            qty: row.quantity || 1,
            brand: row.brand || ""
        },
        freeze: true,
        freeze_message: __("Fetching item details..."),

        callback(r) {
            if (!r.message) {
                frappe.msgprint("No item details received");
                return;
            }

            const d = r.message;

            frappe.model.set_value(cdt, cdn, "item_name", d.item_name);
            frappe.model.set_value(cdt, cdn, "description", d.description);
            frappe.model.set_value(cdt, cdn, "uom", d.uom);
            frappe.model.set_value(cdt, cdn, "quantity", d.qty);

            // Pricing
            frappe.model.set_value(cdt, cdn, "rate", d.price_list_rate);
            frappe.model.set_value(cdt, cdn, "selling_price_list", d.price_list);
            frappe.model.set_value(cdt, cdn, "amount", d.amount);
            frappe.model.set_value(cdt, cdn, "rate_with_gst", d.rate_with_gst || d.price_list_rate);
            frappe.model.set_value(cdt, cdn, "discount", d.discount || 0);
            frm.refresh_field("items");

            calculate_total_quantity(frm);
            calculate_total_amount(frm);
        }
    });
}

// ---- Total Quantity Calculation ----
function calculate_total_quantity(frm) {
    let total_qty = 0;
    (frm.doc.items || []).forEach(d => {
        total_qty += d.quantity || 0;
    });
    frm.set_value("total_quantity", total_qty);
}

// ---- Total Amount Calculation ----
function calculate_total_amount(frm) {
    let total_amount = 0;
    (frm.doc.items || []).forEach(d => {
        total_amount += d.amount || 0;
    });
    frm.set_value("total_amount", total_amount);
}

// Copyright (c) 2025, Abhishek and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Dealership Profile", {
//     dealership(frm) {
//         frappe.msgprint("Dealership field changed");

//         frappe.call({
//             method: "get_dealership_plan_range",
//             doc: frm.doc,
//             callback() {
//                 // Server already updated the doc
//                 frm.refresh_field("dealership_plan_range");
//                 frm.refresh_field("tahsils");
//                 frm.refresh_field("marketplaces");
//             }   
//         });
//     }
// });

frappe.ui.form.on("Dealership Profile", {
    refresh(frm) {
        // agar record API se aaya hai
        if (frm.doc.dealership && !frm.__autofill_done) {
            frm.__autofill_done = true;

            // manually trigger same logic
            frm.trigger("dealership");
        }
    },

    dealership(frm) {
        frappe.call({
            method: "get_dealership_plan_range",
            doc: frm.doc,
            callback() {
                frm.refresh_field("dealership_plan_range");
                frm.refresh_field("tahsils");
                frm.refresh_field("marketplaces");
            }
        });
    }
});



// Copyright (c) 2025, Abhishek and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Dealership Profile", {
//     dealership_plan(frm) {
//         if (!frm.doc.dealership_plan) return;

//         frappe.call({
//             method: "get_dealership_plan_range",
//             doc: frm.doc,
//             callback() {
//                 // Server already updated the doc
//                 frm.refresh_field("dealership_plan_range");
//             }
//         });
//     }
// });

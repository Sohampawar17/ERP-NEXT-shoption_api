// Copyright (c) 2025, Abhishek and contributors
// For license information, please see license.txt
frappe.ui.form.on("Transporter District", {
    district: function (frm, cdt, cdn) {

        let row = locals[cdt][cdn];
        console.log("Selected Districts (from row):", row.district);

        frm.set_query("tahsil", "transporter_district", function (doc, cdt2, cdn2) {
            let child = locals[cdt2][cdn2];

            console.log("Filtering Tahsil for row:", child);
            console.log("District filter applied:", child.district);

            return {
                filters: {
                    district: ["in", child.district]   // Multiselect filter
                }
            };
        });
    }
});



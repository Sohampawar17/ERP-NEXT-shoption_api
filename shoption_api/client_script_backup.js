// Full payment and COD script  

// frappe.ui.form.on('Item Price', {
//     custom_full_payment_discount_type: calculate_prices,
//     custom_full_payment_discount_value: calculate_prices,

//     custom_cod_discount_type: calculate_prices,
//     custom_cod_discount_value: calculate_prices,

//     price_list_rate: calculate_prices,
//     rate: calculate_prices
// });


// function calculate_prices(frm) {
//     let rate = frm.doc.rate || frm.doc.price_list_rate || 0;

//     // --------------------------
//     // FULL PAYMENT CALCULATION
//     // --------------------------
//     if (frm.doc.custom_full_payment_discount_type === "Percentage") {
//         let d = frm.doc.custom_full_payment_discount_value || 0;
//         frm.doc.custom_full_payment = rate - (rate * d / 100);
//     }
//     else if (frm.doc.custom_full_payment_discount_type === "Amount") {
//         let d = frm.doc.custom_full_payment_discount_value || 0;
//         frm.doc.custom_full_payment = rate - d;
//     }
//     else {
//         frm.doc.custom_full_payment = rate;
//     }

//     // --------------------------
//     // COD CALCULATION
//     // --------------------------
//     if (frm.doc.custom_cod_discount_type === "Percentage") {
//         let d = frm.doc.custom_cod_discount_value || 0;
//         frm.doc.custom_cash_on_delivery_ = rate - (rate * d / 100);
//     }
//     else if (frm.doc.custom_cod_discount_type === "Amount") {
//         let d = frm.doc.custom_cod_discount_value || 0;
//         frm.doc.custom_cash_on_delivery_ = rate - d;
//     }
//     else {
//         frm.doc.custom_cash_on_delivery_ = rate;
//     }

//     frm.refresh_fields();
// }


// User id override
// Doctype - User 
// Apply to - Form 
// frappe.listview_settings['User'] = {
//     hide_name_column: true,

//     add_fields: ["username"],

//     get_indicator: function (doc) {
//         return [__(doc.username), "blue", "username,=," + doc.username];
//     },

//     formatters: {
//         "name": function (value, df, doc) {
//             return doc.username || value;
//         },
//         "email": function (value, df, doc) {
//             return doc.username || value;
//         }
//     }
// };


// Lead button 
// Doctype - Lead
// Apply to - Form
// frappe.ui.form.on("Lead", {
//     refresh(frm) {

//         // Remove previous buttons (avoid duplicates)
//         frm.clear_custom_buttons();

//         // Button visible only if status is Open or Draft
//         const is_open = (frm.doc.status === "Open" || frm.doc.status === "Draft");

//         if (!is_open) {
//             return;   // Don't show anything
//         }

//         // Show Farmer Button (conditions)
//         if (frm.doc.type === "Farmer" && frm.doc.custom_farmar_created != 1) {
//             frm.add_custom_button("Farmer registeration", function () {
//                 frappe.new_doc("Farmer Registration", {
//                     from_document: frm.doc.name,
//                     mobile_number: frm.doc.mobile_no,
//                     party_name: frm.doc.lead_name
//                 });
//             });
//         }

//         // Show Dealer Button (conditions)
//         if (frm.doc.type === "Dealer" && frm.doc.custom_dealer_created != 1) {
//             frm.add_custom_button("Dealer Registration", function () {
//                 frappe.new_doc("Delear Registration", {
//                     from_document: frm.doc.name,
//                     mobile_number: frm.doc.mobile_no,
//                     party_name: frm.doc.lead_name
//                 });
//             });
//         }
//     }
// });



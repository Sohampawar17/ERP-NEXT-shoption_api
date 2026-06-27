frappe.query_reports["Dealership Overview"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "dealer_id",
			label: __("Customer / Dealer"),
			fieldtype: "Link",
			options: "Delear Registration",
		},
	],
};

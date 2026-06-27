import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	report_summary = get_report_summary(data)
	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{"label": _("Executive Name"), "fieldname": "executive_name", "fieldtype": "Data", "width": 150},
		{"label": _("Customer / Dealer"), "fieldname": "dealer_id", "fieldtype": "Link", "options": "Delear Registration", "width": 160},
  		{"label": _("Shop Name"), "fieldname": "shop_name", "fieldtype": "Data", "width": 170},
		{"label": _("Dealership Type"), "fieldname": "dealership_type", "fieldtype": "Link", "options": "Dealership Category Master", "width": 170},
		{"label": _("Plan"), "fieldname": "delership_plan", "fieldtype": "Link", "options": "Dealership Plan", "width": 140},
		{"label": _("Area Details"), "fieldname": "area_details", "fieldtype": "Data", "width": 240},
		{"label": _("Deposit Received"), "fieldname": "deposit_amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Deposit Status"), "fieldname": "deposit_status", "fieldtype": "Data", "width": 120},
		{"label": _("First Order Received"), "fieldname": "first_order_received", "fieldtype": "Currency", "width": 150},
		{"label": _("First Order Status"), "fieldname": "first_order_status", "fieldtype": "Data", "width": 130},
		{"label": _("Monthly Target"), "fieldname": "monthly_target", "fieldtype": "Float", "width": 120},
		{"label": _("Agreement Status"), "fieldname": "agreement_status", "fieldtype": "Data", "width": 130},
		{"label": _("Agreement Date"), "fieldname": "agreement_date", "fieldtype": "Datetime", "width": 150},
		{"label": _("Approval Status"), "fieldname": "approval_status", "fieldtype": "Data", "width": 140},
		{"label": _("Form Status"), "fieldname": "form_status", "fieldtype": "Data", "width": 130},
	]


def get_data(filters):
	conditions = ["ad.docstatus != 2"]
	if filters.get("from_date"):
		conditions.append("DATE(ad.creation) >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("DATE(ad.creation) <= %(to_date)s")

	if filters.get("dealer_id"):
		conditions.append("ad.dealer_id = %(dealer_id)s")

	where_clause = " and ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT
			ad.date,
			ad.owner AS executive_name,
			ad.dealer_id,
			ad.dealership_type,
			ad.dealership_plan_name AS delership_plan,
			ad.shop_name,

			CASE
				WHEN dp.plan_coverage = 'Marketplaces' THEN IFNULL((
					SELECT GROUP_CONCAT(DISTINCT mp.marketplace_name ORDER BY mp.marketplace_name SEPARATOR ', ')
					FROM `tabDealership Plan Marketplace` dpm
					LEFT JOIN `tabMarketplace` mp ON mp.name = dpm.marketplace
					WHERE dpm.parent = ad.name AND dpm.parenttype = 'Apply Dealership'
				), '')
				WHEN dp.plan_coverage = 'Tehsils' THEN IFNULL((
					SELECT GROUP_CONCAT(DISTINCT th2.tahshil ORDER BY th2.tahshil SEPARATOR ', ')
					FROM `tabDealership Plan Tehsil` dpt
					LEFT JOIN `tabTahshil` th2 ON th2.name = dpt.tehsil
					WHERE dpt.parent = ad.name AND dpt.parenttype = 'Apply Dealership'
				), '')
				ELSE IFNULL(d.district_name, ad.district)
			END AS area_details,

			IFNULL(ad.deposit_amount, 0) AS deposit_amount,

			CASE
				WHEN IFNULL(ad.override, 0) = 1 OR ad.account_override_datetime IS NOT NULL THEN 'Override'
				WHEN IFNULL(ad.deposit_amount, 0) > 0 THEN 'Received'
				ELSE 'Pending'
			END AS deposit_status,

			IFNULL(ad.total_paid_order_amount, 0) AS first_order_received,

			CASE
				WHEN IFNULL(ad.order_override, 0) = 1 OR ad.first_order_override IS NOT NULL THEN 'Override'
				WHEN IFNULL(ad.first_order_value, 0) <= 0 THEN 'N/A'
				WHEN IFNULL(ad.total_paid_order_amount, 0) >= IFNULL(ad.first_order_value, 0)
					AND IFNULL(ad.first_order_value, 0) > 0
				THEN 'Received'

				WHEN IFNULL(ad.total_paid_order_amount, 0) > 0
				THEN 'Partial'

				ELSE 'Pending'
			END AS first_order_status,

			ROUND(IFNULL(ad.dealership_target, 0) / 12, 2) AS monthly_target,

			CASE
				WHEN IFNULL(ad.dealership_aggrement, '') != ''
				THEN 'Completed'
				ELSE 'Pending'
			END AS agreement_status,

			CASE
				WHEN ad.docstatus = 1 THEN ad.modified
				ELSE NULL
			END AS agreement_date,

			ad.approval_status,
			ad.form_status

		FROM `tabApply Dealership` ad

		LEFT JOIN `tabTerritory` t
			ON t.name = ad.state

		LEFT JOIN `tabDistrict` d
			ON d.name = ad.district

		LEFT JOIN `tabTahshil` th
			ON th.name = ad.tehsil_

		LEFT JOIN `tabDealership Plan` dp
			ON dp.name = ad.delership_plan
		where {where_clause}
		order by ad.creation desc
	""",
		filters,
		as_dict=1,
	)


def get_chart_data(data):
	deposit_received = sum(1 for row in data if row.get("deposit_status") == "Received")
	deposit_pending = sum(1 for row in data if row.get("deposit_status") == "Pending")
	first_order_received = sum(1 for row in data if row.get("first_order_status") == "Received")
	first_order_pending = sum(1 for row in data if row.get("first_order_status") != "Received")
	agreement_completed = sum(1 for row in data if row.get("agreement_status") == "Completed")
	agreement_pending = sum(1 for row in data if row.get("agreement_status") == "Pending")

	return {
		"data": {
			"labels": [
				"Deposit Received",
				"Deposit Pending",
				"First Order Received",
				"First Order Pending",
				"Agreement Completed",
				"Agreement Pending",
			],
			"datasets": [
				{
					"name": "Count",
					"values": [
						deposit_received,
						deposit_pending,
						first_order_received,
						first_order_pending,
						agreement_completed,
						agreement_pending,
					],
				}
			],
		},
		"type": "bar",
		"height": 280,
	}


def get_report_summary(data):
	total_records = len(data)
	total_deposit_amount = sum((row.get("deposit_amount") or 0) for row in data)
	total_first_order_amount = sum((row.get("first_order_received") or 0) for row in data)
	total_monthly_target = sum((row.get("monthly_target") or 0) for row in data)

	return [
		{
			"value": total_records,
			"label": _("Total Records"),
			"datatype": "Int",
		},
		{
			"value": total_deposit_amount,
			"label": _("Total Deposit Received"),
			"datatype": "Currency",
		},
		{
			"value": total_first_order_amount,
			"label": _("Total First Order Received"),
			"datatype": "Currency",
		},
		{
			"value": total_monthly_target,
			"label": _("Total Monthly Target"),
			"datatype": "Float",
		},
	]

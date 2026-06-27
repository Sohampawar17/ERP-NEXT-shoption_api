import frappe
from frappe import _
from frappe.utils import flt, getdate, is_invalid_date_string, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	from_date, to_date = get_date_range(filters)
	columns = get_columns()
	data = get_data(filters, from_date, to_date)
	return columns, data


def get_columns():
	return [
     		{"label": _("Dealer ID"), "fieldname": "dealer_id", "fieldtype": "Data", "width": 130},

		{"label": _("Dealer Name"), "fieldname": "dealer_name", "fieldtype": "Data", "width": 180},
		{"label": _("Number"), "fieldname": "number", "fieldtype": "Data", "width": 130},
		{"label": _("Shop Name"), "fieldname": "shop_name", "fieldtype": "Data", "width": 190},
  {
    "label": _("Address Line 1"),
    "fieldname": "address_line_1",
    "fieldtype": "Data",
    "width": 250,
},
  {
    "label": _("Marketplace"),
    "fieldname": "marketplace",
    "fieldtype": "Data",
    "width": 150,
},
  {
    "label": _("Tehsil"),
    "fieldname": "tehsil",
    "fieldtype": "Data",
    "width": 150,
},
  {
    "label": _("District"),
    "fieldname": "district",
    "fieldtype": "Data",
    "width": 150,
},

  {
    "label": _("State"),
    "fieldname": "state",
    "fieldtype": "Data",
    "width": 120,
},


{
    "label": _("Pincode"),
    "fieldname": "pincode",
    "fieldtype": "Data",
    "width": 100,
},

{
    "label": _("Full Address"),
    "fieldname": "full_address",
    "fieldtype": "Small Text",
    "width": 350,
},
		{"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Small Text", "width": 220},
		{"label": _("Tags"), "fieldname": "tags", "fieldtype": "Small Text", "width": 180},
		{"label": _("Multi / Single"), "fieldname": "multi_single", "fieldtype": "Data", "width": 120},
		{"label": _("Revenue - Invoice"), "fieldname": "revenue_invoice", "fieldtype": "Currency", "width": 150},
		{"label": _("Target"), "fieldname": "target", "fieldtype": "Currency", "width": 130},
		{"label": _("Achieved"), "fieldname": "achieved", "fieldtype": "Currency", "width": 130},
		{"label": _("Deposit"), "fieldname": "deposit", "fieldtype": "Currency", "width": 130},
	]


def get_date_range(filters):
	from_date = parse_date(filters.get("from_date"))
	to_date = parse_date(filters.get("to_date"))

	if not from_date and not to_date:
		today = getdate(nowdate())
		return today, today
	if not from_date:
		from_date = to_date
	if not to_date:
		to_date = from_date
	if from_date > to_date:
		from_date, to_date = to_date, from_date

	return from_date, to_date


def parse_date(value):
	if not value or is_invalid_date_string(value):
		return None
	return getdate(value)


def get_data(filters, from_date, to_date):
	scope_users = get_hierarchy_users(frappe.session.user)
	allowed_tehsils = get_allowed_tehsils(scope_users)
	unrestricted_access = has_unrestricted_access()

	if not allowed_tehsils and not unrestricted_access:
		return []

	params = {
		"from_date": from_date,
		"to_date": to_date,
	}

	conditions = [
		"""(
			LOWER(IFNULL(c.customer_group, '')) LIKE '%%dealer%%'
			OR dr_doc.name IS NOT NULL
		)"""
	]

	if allowed_tehsils and not unrestricted_access:
		conditions.append("COALESCE(dr_doc.tahshil, addr.custom_tahshil) IN %(allowed_tehsils)s")
		params["allowed_tehsils"] = tuple(allowed_tehsils)

	if filters.get("dealer_id"):
		conditions.append("dr_doc.name = %(dealer_id)s")
		params["dealer_id"] = filters.get("dealer_id")

	rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(dr_doc.name, ''), c.custom_document_value) AS dealer_id,
			COALESCE(NULLIF(dr_doc.party_name, ''), c.customer_name) AS dealer_name,
			COALESCE(NULLIF(dr_doc.mobile_number, ''), c.mobile_no) AS number,
			COALESCE(NULLIF(dr_doc.shop_name, ''), ad.shop_name, c.customer_name) AS shop_name,
			COALESCE(dr_doc.tahshil, addr.custom_tahshil) AS dealer_tehsil_id,
dr_doc.state,
th.tahshil AS tehsil,
d.district_name AS district,
m.marketplace_name AS marketplace,
dr_doc.pincode,
dr_doc.address_line_1,

CONCAT_WS(
    ', ',
    dr_doc.address_line_1,
    m.marketplace_name,
    th.tahshil,
    d.district_name,
addr.state,
dr_doc.pincode
) AS full_address,
			IFNULL(sp_map.sales_persons, '') AS sales_person,
			IFNULL(tags.tags, '') AS tags,
			CASE
				WHEN IFNULL(so.order_count, 0) = 0 THEN 'Authorized'
				WHEN IFNULL(so.order_count, 0) = 1 THEN 'Single Ordering'
				ELSE 'Multiple Ordering'
			END AS multi_single,
			IFNULL(inv.revenue_invoice, 0) AS revenue_invoice,
			0 AS target,
			0 AS achieved,
			IFNULL(ad.deposit_amount, 0) AS deposit
		FROM `tabCustomer` c
		LEFT JOIN `tabDelear Registration` dr_doc
			ON dr_doc.name = c.custom_document_value
		LEFT JOIN `tabAddress` addr
				ON addr.name = c.customer_primary_address
		LEFT JOIN `tabTahshil` th
			ON th.name = COALESCE(dr_doc.tahshil, addr.custom_tahshil)

		LEFT JOIN `tabDistrict` d
			ON d.name = dr_doc.district

		LEFT JOIN `tabMarketplace` m
			ON m.name = dr_doc.marketplace
		LEFT JOIN (
				SELECT
					customer,
					COUNT(name) AS order_count
				FROM `tabSales Order`
				WHERE docstatus != 2
				GROUP BY customer
			) so
				ON so.customer = c.name
			LEFT JOIN (
				SELECT x.*
			FROM `tabApply Dealership` x
			INNER JOIN (
				SELECT dealer_id, MAX(creation) AS creation
				FROM `tabApply Dealership`
				WHERE docstatus != 2
				AND IFNULL(approved_amount, 0) > 0
				GROUP BY dealer_id
			) latest
				ON latest.dealer_id = x.dealer_id
				AND latest.creation = x.creation
			WHERE x.docstatus != 2
   AND IFNULL(approved_amount, 0) > 0
		) ad
			ON ad.dealer_id = COALESCE(dr_doc.name)
		LEFT JOIN (
			SELECT
				customer,
				SUM(
					CASE
						WHEN IFNULL(is_return, 0) = 0 THEN grand_total
						ELSE 0
					END
				) AS revenue_invoice
			FROM `tabSales Invoice`
			WHERE docstatus = 1
				AND posting_date BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY customer
			) inv
				ON inv.customer = c.name
			LEFT JOIN (
				SELECT
					tagged.customer,
					GROUP_CONCAT(DISTINCT tagged.tag ORDER BY tagged.tag SEPARATOR ', ') AS tags
				FROM (
					SELECT
						document_name AS customer,
						tag
					FROM `tabTag Link`
					WHERE document_type = 'Customer'

					UNION ALL

					SELECT
						cust.name AS customer,
						tl.tag
					FROM `tabTag Link` tl
					INNER JOIN `tabCustomer` cust
						ON cust.custom_document_value = tl.document_name
					WHERE tl.document_type = 'Delear Registration'
				) tagged
				GROUP BY tagged.customer
			) tags
				ON tags.customer = c.name
			LEFT JOIN (
				SELECT
					upt.tehsil,
					GROUP_CONCAT(DISTINCT sp.sales_person_name ORDER BY sp.sales_person_name SEPARATOR ', ') AS sales_persons
				FROM `tabUser Permission Tehsil` upt
				INNER JOIN `tabSales Person` sp
					ON sp.name = upt.parent
					AND IFNULL(sp.enabled, 1) = 1
					AND IFNULL(sp.is_group, 0) = 0
				GROUP BY upt.tehsil
			) sp_map
				ON sp_map.tehsil = COALESCE(dr_doc.tahshil, addr.custom_tahshil)
			WHERE {' AND '.join(conditions)}
		ORDER BY dealer_name, shop_name
		""",
		params,
		as_dict=True,
	)

	target_map = get_apply_dealership_target_map(rows, from_date, to_date)

	for row in rows:
		row.revenue_invoice = flt(row.revenue_invoice)
		row.target = flt(target_map.get(row.get("dealer_id")) or 0)
		row.achieved = row.revenue_invoice if row.target > 0 else 0
		row.deposit = flt(row.deposit)

	return rows


def get_apply_dealership_target_map(rows, from_date, to_date):
	dealer_ids = sorted({row.get("dealer_id") for row in rows if row.get("dealer_id")})
	if not dealer_ids:
		return {}

	from_dt = getdate(from_date) if from_date else getdate(nowdate())
	to_dt = getdate(to_date) if to_date else getdate(nowdate())
	if from_dt and to_dt and from_dt > to_dt:
		from_dt, to_dt = to_dt, from_dt

	ad_rows = frappe.db.sql(
		"""
		SELECT
			ad.dealer_id,
			ad.dealership_target,
			DATE(ad.valid_from) AS valid_from,
			DATE(ad.valid_to) AS valid_to
		FROM `tabApply Dealership` ad
		WHERE ad.docstatus != 2
			   AND IFNULL(approved_amount, 0) > 0

			AND ad.dealer_id IN %(dealer_ids)s
			AND ad.valid_from IS NOT NULL
			AND ad.valid_to IS NOT NULL
			AND DATE(ad.valid_from) <= %(to_dt)s
			AND DATE(ad.valid_to) >= %(from_dt)s
		""",
		{
			"dealer_ids": tuple(dealer_ids),
			"from_dt": from_dt,
			"to_dt": to_dt,
		},
		as_dict=True,
	)

	target_map = {}
	for row in ad_rows:
		dealer_id = row.get("dealer_id")
		doc_target = flt(row.get("dealership_target") or 0)
		valid_from = getdate(row.get("valid_from"))
		valid_to = getdate(row.get("valid_to"))

		if not dealer_id or doc_target <= 0 or not valid_from or not valid_to or valid_to < valid_from:
			continue

		overlap_start = max(valid_from, from_dt)
		overlap_end = min(valid_to, to_dt)
		if overlap_end < overlap_start:
			continue

		overlap_days = (overlap_end - overlap_start).days + 1
		total_days = (valid_to - valid_from).days + 1
		prorated_target = doc_target * (overlap_days / total_days)
		target_map[dealer_id] = flt(target_map.get(dealer_id) or 0) + prorated_target

	return target_map


def get_hierarchy_users(root_user):
	employees = frappe.get_all(
		"Employee",
		fields=["name", "user_id", "reports_to"],
		filters={"status": "Active"},
		limit_page_length=0,
	)

	employees_by_user = {}
	employees_by_name = {}
	children_map = {}

	for emp in employees:
		employees_by_name[emp.name] = emp
		if emp.user_id:
			employees_by_user[emp.user_id] = emp
		children_map.setdefault(emp.reports_to or "", []).append(emp.name)

	root_employee = employees_by_user.get(root_user)
	if not root_employee:
		return [root_user]

	users = []
	visited = set()

	def collect(emp_name):
		if emp_name in visited:
			return
		visited.add(emp_name)

		emp = employees_by_name.get(emp_name)
		if not emp:
			return
		if emp.user_id:
			users.append(emp.user_id)

		for child in children_map.get(emp.name, []):
			collect(child)

	collect(root_employee.name)

	if root_user not in users:
		users.insert(0, root_user)

	return list(dict.fromkeys(users))


def get_allowed_tehsils(users):
	if not users:
		return []

	user_permission_rows = frappe.db.sql(
		"""
		SELECT DISTINCT for_value
		FROM `tabUser Permission`
		WHERE user IN %(users)s
			AND allow = 'Tahshil'
			AND IFNULL(applicable_for, '') IN ('', 'Customer', 'Address', 'Delear Registration')
		""",
		{"users": tuple(users)},
		as_list=True,
	)

	sales_person_rows = frappe.db.sql(
		"""
		SELECT DISTINCT upt.tehsil
		FROM `tabSales Person` sp
		INNER JOIN `tabUser Permission Tehsil` upt
			ON upt.parent = sp.name
		WHERE sp.custom_user IN %(users)s
			AND IFNULL(sp.enabled, 1) = 1
			AND IFNULL(sp.is_group, 0) = 0
		""",
		{"users": tuple(users)},
		as_list=True,
	)

	tehsils = [row[0] for row in user_permission_rows if row and row[0]]
	tehsils.extend(row[0] for row in sales_person_rows if row and row[0])

	return list(dict.fromkeys(tehsils))


def has_unrestricted_access():
	return frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()

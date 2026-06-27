# Copyright (c) 2025, Abhishek and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import base64
import urllib.parse

class PayUPaymentTest(Document):

	def before_save(self):
		# data = {
		# 	"ProductInfo": self.product_info,
		# 	"FirstName": self.first_name,
		# 	"Email": self.email,
		# 	"Amount": self.amount,
		# 	"Phone": self.phone,
		# 	"UserId": self.user_id,
		# 	"Order_id": self.order_id,
		# 	"Call_Back_URL": self.callback_url
		# }

		# query_string = urllib.parse.urlencode(data)
		# token = base64.b64encode(query_string.encode()).decode()

		# self.payu_token = token
  
		import frappe
		from frappe.permissions import add_permission, update_permission_property

		DOCTYPE = "Payment Gateway Transaction"
		MODULE = "Shoption test api"

		# -------------------------------------------------
		# 1. Ensure Module Def exists
		# -------------------------------------------------
		if not frappe.db.exists("Module Def", MODULE):
			frappe.get_doc({
				"doctype": "Module Def",
				"module_name": MODULE,
				"app_name": frappe.get_installed_apps()[0],
				"custom": 1
			}).insert(ignore_permissions=True)

		frappe.db.commit()

		# -------------------------------------------------
		# 2. Create DocType (ONLY if not exists)
		# -------------------------------------------------
		if not frappe.db.exists("DocType", DOCTYPE):
			doc = frappe.get_doc({
				"doctype": "DocType",
				"name": DOCTYPE,
				"module": MODULE,
				"custom": 1,
				"istable": 0,
				"is_submittable": 0,
				"allow_rename": 0,
				"track_changes": 1,
				"autoname": "hash",
				"in_create": 1,
				"allow_import": 1,

				"fields": [

					{"fieldname": "txn_section", "label": "Transaction Details", "fieldtype": "Section Break"},
					{"fieldname": "txn_id", "label": "Txn ID", "fieldtype": "Data"},
					{"fieldname": "order_id", "label": "Order ID", "fieldtype": "Data"},
					{"fieldname": "userid", "label": "User ID", "fieldtype": "Data"},
					{"fieldname": "amount", "label": "Amount", "fieldtype": "Data"},
					{"fieldname": "status", "label": "Status", "fieldtype": "Data"},
					{"fieldname": "entrytype", "label": "Entry Type", "fieldtype": "Data"},
					{"fieldname": "created_at", "label": "Created At", "fieldtype": "Datetime"},
					{"fieldname": "statusupdateddate", "label": "Status Updated Date", "fieldtype": "Datetime"},

					{"fieldname": "customer_section", "label": "Customer Details", "fieldtype": "Section Break"},
					{"fieldname": "firstname", "label": "First Name", "fieldtype": "Data"},
					{"fieldname": "email", "label": "Email", "fieldtype": "Data"},
					{"fieldname": "phone", "label": "Phone", "fieldtype": "Data"},

					{"fieldname": "request_section", "label": "Request Data", "fieldtype": "Section Break"},
					{"fieldname": "productinfo", "label": "Product Info", "fieldtype": "Long Text"},
					{"fieldname": "callbackurl", "label": "Callback URL", "fieldtype": "Data"},
					{"fieldname": "request_token", "label": "Request Token", "fieldtype": "Long Text"},
					{"fieldname": "request_decodedtoken", "label": "Decoded Token", "fieldtype": "Long Text"},
					{"fieldname": "request_cleanedtoken", "label": "Cleaned Token", "fieldtype": "Long Text"},
					{"fieldname": "request_hashstring", "label": "Hash String", "fieldtype": "Long Text"},
					{"fieldname": "request_hash", "label": "Request Hash", "fieldtype": "Data"},

					{"fieldname": "response_section", "label": "Payment Gateway Response", "fieldtype": "Section Break"},
					{"fieldname": "response_mihpayid", "label": "MIHPay ID", "fieldtype": "Data"},
					{"fieldname": "response_mode", "label": "Payment Mode", "fieldtype": "Data"},
					{"fieldname": "response_unmappedstatus", "label": "Unmapped Status", "fieldtype": "Data"},
					{"fieldname": "response_key", "label": "Key", "fieldtype": "Data"},
					{"fieldname": "response_discount", "label": "Discount", "fieldtype": "Data"},
					{"fieldname": "response_net_amount_debit", "label": "Net Amount Debit", "fieldtype": "Data"},
					{"fieldname": "response_addedon", "label": "Added On", "fieldtype": "Data"},
					{"fieldname": "response_payment_source", "label": "Payment Source", "fieldtype": "Data"},
					{"fieldname": "response_pg_type", "label": "PG Type", "fieldtype": "Data"},
					{"fieldname": "response_bank_ref_num", "label": "Bank Ref No", "fieldtype": "Data"},
					{"fieldname": "response_bankcode", "label": "Bank Code", "fieldtype": "Data"},
					{"fieldname": "response_error", "label": "Error Code", "fieldtype": "Data"},
					{"fieldname": "response_error_message", "label": "Error Message", "fieldtype": "Long Text"},
					{"fieldname": "response_splitinfo", "label": "Split Info", "fieldtype": "Long Text"},

					{"fieldname": "response_payu_section", "label": "PayU Response", "fieldtype": "Section Break"},
					{"fieldname": "response_payuamount", "label": "PayU Amount", "fieldtype": "Data"},
					{"fieldname": "response_payu_productinfo", "label": "PayU Product Info", "fieldtype": "Long Text"},
					{"fieldname": "response_payu_firstname", "label": "PayU First Name", "fieldtype": "Data"},
					{"fieldname": "response_payu_email", "label": "PayU Email", "fieldtype": "Data"},
					{"fieldname": "response_payu_phone", "label": "PayU Phone", "fieldtype": "Data"},
					{"fieldname": "response_payu_txnid", "label": "PayU Txn ID", "fieldtype": "Data"},
					{"fieldname": "response_payu_hash", "label": "PayU Hash", "fieldtype": "Long Text"}
				]
			})

			doc.insert(ignore_permissions=True)
			frappe.db.commit()

		# -------------------------------------------------
		# 3. Add System Manager permissions
		# -------------------------------------------------
		if not frappe.get_all("DocPerm", filters={"parent": DOCTYPE}):
			add_permission(DOCTYPE, "System Manager", 0)

		update_permission_property(DOCTYPE, "System Manager", 0, "read", 1)
		update_permission_property(DOCTYPE, "System Manager", 0, "write", 1)
		update_permission_property(DOCTYPE, "System Manager", 0, "create", 1)
		update_permission_property(DOCTYPE, "System Manager", 0, "delete", 1)

		frappe.db.commit()

		# -------------------------------------------------
		# 4. Rebuild Desk
		# -------------------------------------------------
		frappe.clear_cache()
		frappe.setup_module_map()

		# -------------------------------------------------
		# 5. Final confirmation
		# -------------------------------------------------
		{
			"doctype_created": frappe.db.exists("DocType", DOCTYPE),
			"table_created": frappe.db.table_exists("tabPayment Gateway Transaction"),
			"module": MODULE
		}



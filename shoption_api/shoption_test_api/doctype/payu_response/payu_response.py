# Copyright (c) 2025, Abhishek and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, now
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

class PayUResponse(Document):
	def after_insert(self):
		if (self.status or "").lower() == "success":
			self.create_payment_entry()

	def validate(self):
		if self.txnid and frappe.db.exists(
			"PayU Response",
			{"txnid": self.txnid, "name": ["!=", self.name]},
		):
			frappe.throw(_("PayU Response already exists for txnid {0}.").format(self.txnid))
		if not self.createdat:
			self.createdat = now()
		self.lastupdated_at = now()


	def create_payment_entry(self):
		existing_pe = frappe.db.get_value(
			"Payment Entry",
			{
				"reference_no": self.txnid,
				"docstatus": ["!=", 2],
			},
			"name",
		)
		if existing_pe:
			return existing_pe

		# Get order_id linked to this transaction
		order_id = None

		if self.txnid:
			# 1️⃣ FIRST: Payment Link
			order_id = frappe.db.get_value(
				"Payment Link",
				{"transactionid": self.txnid},
				"order_id"
			)

			# 2️⃣ FALLBACK: Payment Gateway Transaction
			if not order_id:
				order_id = frappe.db.get_value(
					"Payment Gateway Transaction",
					{"txn_id": self.txnid},
					"order_id"
				)


		if not order_id:
			frappe.throw("Sales Order not found for this transaction")

		so = frappe.get_doc("Sales Order", order_id)
		if cint(so.docstatus) == 0:
			so.submit()
		account, currency = frappe.db.get_value("Payu Setting",None,["account_for_payment_entry","paid_to_account_currency"])
		mode="UPI"
		# Create Payment Entry from ERPNext standard helper
		pe = get_payment_entry("Sales Order", so.name, ignore_permissions=True)
		date= getdate(self.addedon.replace("+", " "))
		pe.posting_date = date
		pe.mode_of_payment = mode # change if needed
		pe.target_exchange_rate= 1
		pe.paid_to=account
		pe.paid_to_account_currency=currency
		payment_amount = flt(self.netamountdebit)
		outstanding_amount = flt(pe.references[0].outstanding_amount) if pe.references else 0
		allocated_amount = max(0, min(payment_amount, outstanding_amount))
		pe.paid_amount = payment_amount
		pe.received_amount = payment_amount
		pe.reference_no = self.txnid
		pe.reference_date =  date
		if pe.references:
			pe.references[0].allocated_amount = allocated_amount
		pe.insert(ignore_permissions=True)
		
		pe.submit()
		return pe.name

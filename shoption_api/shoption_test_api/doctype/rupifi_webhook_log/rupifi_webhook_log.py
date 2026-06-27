import json
import frappe
from frappe.model.document import Document
from frappe.utils import now, get_datetime,flt,today


class RupifiWebhookLog(Document):

	def before_insert(self):
		# Only set created timestamp here
		self.createdat = now()

	def before_save(self):
		# Update fields once (before_insert already triggers before_save)
		if self.status and self.status.lower() == "captured":
				self.create_payment_entry()
		self.lastupdatedat = now()		

	
	def create_payment_entry(self):
		"""
		Create Payment Entry when payment is CAPTURED
		"""

		# --------------------------
		# Idempotency check
		# --------------------------
		existing_pe = frappe.db.exists(
			"Payment Entry",
			{"reference_no": self.payment_id,"docstatus":1}
		)
		if existing_pe:
			return  # Payment Entry already created

		# --------------------------
		# Get Sales Order
		# --------------------------
		if not self.order_id:
			frappe.throw("Sales Order not linked to this payment")

		so = frappe.get_doc("Sales Order", self.order_id)

		# Auto-submit Sales Order if needed
		if so.docstatus == 0:
			so.submit()

		# --------------------------
		# Get Payment Account
		# --------------------------
		account, currency = frappe.db.get_value(
			"Payu Setting",
			None,
			["account_for_payment_entry", "paid_to_account_currency"]
		)

		if not account:
			frappe.throw("Payment account not configured in Payu Setting")

		# --------------------------
		# Create Payment Entry
		# --------------------------
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.party_type = "Customer"
		pe.party = so.customer
		pe.company = so.company
		pe.posting_date = today()
		pe.mode_of_payment = "Shoption Credit"
		pe.paid_to = account
		pe.paid_to_account_currency = currency
		pe.paid_amount = flt(self.amount_value)
		pe.received_amount = flt(self.amount_value)
		pe.reference_no = self.merchant_payment_ref_id
		pe.reference_date = today()

		pe.append("references", {
			"reference_doctype": "Sales Order",
			"reference_name": so.name,
			"allocated_amount": flt(self.amount_value)
		})

		pe.insert(ignore_permissions=True)
		pe.submit()
import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, get_datetime,flt,today


class RupifiWebhookLog(Document):

	def before_insert(self):
		# Only set created timestamp here
		if not self.createdat:
			self.createdat = now()

	def validate(self):
		if self.merchant_payment_ref_id and frappe.db.exists(
			"Rupifi Webhook Log",
			{
				"merchant_payment_ref_id": self.merchant_payment_ref_id,
				"name": ["!=", self.name],
			},
		):
			frappe.throw(
				_("Rupifi Webhook Log already exists for merchant payment ref id {0}.").format(
					self.merchant_payment_ref_id
				)
			)
		if self.payment_id and frappe.db.exists(
			"Rupifi Webhook Log",
			{"payment_id": self.payment_id, "name": ["!=", self.name]},
		):
			frappe.throw(_("Rupifi Webhook Log already exists for payment id {0}.").format(self.payment_id))
		self.lastupdatedat = now()

	def _get_existing_payment_entry(self):
		reference_numbers = [
			ref for ref in {
				(self.merchant_payment_ref_id or "").strip(),
				(self.payment_id or "").strip(),
			}
			if ref
		]
		if not reference_numbers:
			return None

		return frappe.db.get_value(
			"Payment Entry",
			{
				"reference_no": ["in", reference_numbers],
				"docstatus": ["!=", 2],
			},
			"name",
		)

	
	def create_payment_entry(self):
		"""
		Create Payment Entry when payment is CAPTURED
		"""

		# --------------------------
		# Idempotency check
		# --------------------------
		existing_pe = self._get_existing_payment_entry()
		if existing_pe:
			return existing_pe

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
		return pe.name

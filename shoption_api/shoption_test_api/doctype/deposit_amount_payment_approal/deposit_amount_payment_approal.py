# Copyright (c) 2026, Abhishek and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now
from frappe.utils import flt
from frappe.model.document import Document
from shoption_api.shoption_test_api.utr_validation import (
	normalize_utr,
	validate_unique_utr_number,
)


class DepositAmountPaymentApproal(Document):

	def validate(self):
		if self.utr__check_no:
			self.utr__check_no = normalize_utr(self.utr__check_no)
			validate_unique_utr_number(
				self.utr__check_no,
				current_doctype=self.doctype,
				current_name=self.name,
			)


	def on_submit(self):
		if not self.view_dealership:
			return
		self.mandatory()
		self.validate_amount()
		if not self.approval_amount:
			self.approval_date=now()
		# Fetch only needed fields (fast)
		deposit, deposit_amount, first_order_value = frappe.db.get_value(
			"Apply Dealership",
			self.view_dealership,
			["plan_deposit_amount", "deposit_amount", "first_order_value"]
		) or (0, 0, 0)
		dealership_doc=frappe.get_doc("Apply Dealership", self.view_dealership)
		dealership_doc.bank_transaction_id=self.bank_transaction_id
		dealership_doc.approved_amount=self.approval_amount
		dealership_doc.approval_date=self.approval_date
		dealership_doc.attach_slip=self.slip_attach
		dealership_doc.remark=self.remark
		dealership_doc.save(ignore_permissions=True)
		# deposit = flt(deposit or 0)
		# deposit_amount = flt(deposit_amount or 0)  # kept in case you need later
		# first_order_value = flt(first_order_value or 0)
		# approved_amount = flt(self.approval_amount or 0)

		# update_values = {
		# 	"bank_transaction_id": self.bank_transaction_id,
		# 	"approved_amount": self.approval_amount,
		# 	"approval_date": self.approval_date,   # will get overridden below where needed
		# 	"attach_slip": self.slip_attach,
		# 	"remark": self.remark,
		# }

		# -----------------------------
		# STATUS / FORM LOGIC
		# -----------------------------
		# if deposit <= 0 and first_order_value <= 0:
		# 	update_values.update({
		# 		"approval_status": "Override",
		# 		"form_status": "Aggreement",
		# 		"approval_date": now(),
		# 	})

		# elif deposit <= 0 and first_order_value > 0:
		# 	update_values.update({
		# 		"approval_status": "Pending for Approval",
		# 		"form_status": "First Order",
		# 		"approval_date": now(),
		# 	})

		# elif deposit > 0 and first_order_value <= 0 and approved_amount > 0:
		# 	update_values.update({
		# 		"approval_status": "Override",
		# 		"form_status": "Aggreement",
		# 	})

		# # -----------------------------
		# # APPLY UPDATE (single write)
		# # -----------------------------
		# frappe.db.set_value(
		# 	"Apply Dealership",
		# 	self.view_dealership,
		# 	update_values,
		# 	update_modified=True
		# )

	def on_cancel(self):
		if not self.view_dealership:
			return

		# Reset fields in Apply Dealership on cancellation
		frappe.db.set_value(
			"Apply Dealership",
			self.view_dealership,
			{
				"bank_transaction_id": None,
				"approved_amount": 0,
				"approval_date": None,
				"attach_slip": None,
				"remark": None,
			},
			update_modified=True
		)
  
	def validate_amount(self):	
		self.deposit_amount = flt(self.deposit_amount)
		self.approval_amount = flt(self.approval_amount)
		if self.deposit_amount <= 0 or self.approval_amount <= 0:
			frappe.throw("Approval Amount must be greater than zero")
		if self.deposit_amount < self.approval_amount:
			frappe.throw(
				f"Approval Amount ({self.approval_amount}) cannot be greater than Requested Amount ({self.deposit_amount})"
			)
   
	def mandatory(self):
		is_exists=frappe.get_all("Deposit Amount Payment Approal", filters={"bank_transaction_id": self.bank_transaction_id, "name": ["!=", self.name],"docstatus": 1})
		if is_exists:
			frappe.throw("Bank Transaction ID already exists for another approved Bank Transfer Request")
		missing = []
		if not self.slip_attach:
			missing.append("Payment Proof")
		if not self.bank_transaction_id:
			missing.append("Bank Transaction ID")
		if not self.company_bank_account:
			missing.append("Company Bank Account")
		if missing:
			frappe.throw(
				"Please fill mandatory fields: " + ", ".join(missing)
			)

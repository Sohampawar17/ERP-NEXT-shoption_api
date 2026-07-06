# Copyright (c) 2025, Abhishek and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate,nowdate, today,now
from shoption_api.shoption_test_api.utr_validation import (
	normalize_utr,
	validate_unique_utr_number,
)


class BankTransferRequest(Document):


	def before_save(self):
		if not self.transaction_date:
			self.transaction_date = today()
		if self.utr_number:
			self.utr_number = normalize_utr(self.utr_number)
			validate_unique_utr_number(
				self.utr_number,
				current_doctype=self.doctype,
				current_name=self.name,
			)
			is_exists = frappe.db.get_value(
				"Sales Invoice",
				{
					"name": self.utr_number,
					"is_return": 1
				},
				["name", "grand_total","rounded_total"],
				as_dict=True
			)

			if is_exists:
				self.transfer_type = "Credit Note"
				self.approved_amount = abs(is_exists.get("rounded_total")) or abs(is_exists.get("grand_total")) or 0

	def validate_amount(self):	
		self.amount = flt(self.amount)
		self.approved_amount = flt(self.approved_amount)
		if self.amount <= 0 or self.approved_amount <= 0:
			frappe.throw("Amount must be greater than zero")
		if self.amount < self.approved_amount:
			frappe.throw(
				f"Approved Amount ({self.approved_amount}) cannot be greater than Requested Amount ({self.amount})"
			)


	def on_submit(self):
		self.validate_amount()
		self.mandatory()
		if self.workflow_state == "Approved":
			self.approved_on=now()
		self._create_accounting_entry_if_needed()

	def _create_accounting_entry_if_needed(self):
		transfer_type = (self.transfer_type or "Bank Transfer").strip()

		if transfer_type == "Credit Note":
			self._create_journal_entry_if_needed()
		else:
			self.create_payment_entry()

	def create_payment_entry(self):

		if self.payment_entry:
			frappe.throw("Payment Entry already created")

		# Ensure Sales Order is submitted
		if frappe.db.get_value("Sales Order", self.sales_order, "docstatus") == 0:
			doc = frappe.get_doc("Sales Order", self.sales_order)
			doc.submit()

		# Get Account Config
		account, currency = frappe.db.get_value(
			"Payu Setting",
			None,
			["account_for_payment_entry", "paid_to_account_currency"]
		)

		company = frappe.defaults.get_user_default("company")
		paid_from = frappe.db.get_value("Company", company, "default_receivable_account")

		if not paid_from:
			frappe.throw("Default Receivable Account not set in Company")
		# ==========================================
		# STEP 3: FETCH ONLY VALID INVOICES
		# ==========================================
		invoices = frappe.db.sql("""
			SELECT DISTINCT si.name
			FROM `tabSales Invoice` si
			INNER JOIN `tabSales Invoice Item` sii
				ON sii.parent = si.name
			WHERE
				si.docstatus = 1
				AND si.status != 'Cancelled'
				AND sii.sales_order = %s
				AND si.outstanding_amount > 0   -- ✅ IMPORTANT FIX
			ORDER BY si.posting_date ASC
		""", (self.sales_order,), as_dict=1)

		references = []
		remaining_amount = self.approved_amount

		# ==========================================
		# STEP 4: ALLOCATE PAYMENT
		# ==========================================
		for inv in invoices:
			if remaining_amount <= 0:
				break

			latest_outstanding = frappe.db.get_value(
				"Sales Invoice",
				inv.name,
				"outstanding_amount"
			)

			if not latest_outstanding or latest_outstanding <= 0:
				continue

			allocated = min(remaining_amount, latest_outstanding)

			references.append({
				"reference_doctype": "Sales Invoice",
				"reference_name": inv.name,
				"allocated_amount": allocated
			})

			remaining_amount -= allocated

		# ==========================================
		# STEP 5: FALLBACK ONLY IF AMOUNT LEFT
		# ==========================================
		if remaining_amount > 0:
			references.append({
				"reference_doctype": "Sales Order",
				"reference_name": self.sales_order,
				"allocated_amount": remaining_amount
			})

		# ==========================================
		# STEP 6: FINAL CLEAN (CRITICAL FIX)
		# ==========================================
		valid_references = []

		for ref in references:
			if ref["reference_doctype"] == "Sales Invoice":
				outstanding = frappe.db.get_value(
					"Sales Invoice",
					ref["reference_name"],
					"outstanding_amount"
				)

				if outstanding and outstanding > 0:
					ref["allocated_amount"] = min(ref["allocated_amount"], outstanding)
					valid_references.append(ref)
			else:
				valid_references.append(ref)

		references = [r for r in valid_references if r.get("allocated_amount", 0) > 0]

		if not references:
			frappe.throw("All invoices are already fully paid. Cannot create Payment Entry.")

		# ==========================================
		# STEP 7: CREATE PAYMENT ENTRY
		# ==========================================
		pe = frappe.get_doc({
			"doctype": "Payment Entry",
			"payment_type": "Receive",
			"party_type": "Customer",
			"posting_date": getdate(self.approved_on),
			"party": self.customer,
			"paid_amount": self.approved_amount,
			"received_amount": self.approved_amount,
			"mode_of_payment": "Bank Transfer",
			"target_exchange_rate": 1,
			"paid_from": paid_from,
			"paid_to": account,
			"paid_to_account_currency": currency,
			"bank_account": self.company_bank_account,
			"reference_no": self.utr_number,
			"reference_date": getdate(self.approved_on),
			"custom_sales_order": self.sales_order,

			"references": references
		})

		# SAFE INSERT
		try:
			pe.insert(ignore_permissions=True)
			pe.submit()

		except Exception as e:
			frappe.log_error(
				message=frappe.get_traceback(),
				title="PAYMENT ENTRY ERROR"
			)
			frappe.throw(f"Payment Entry Failed: {str(e)}")

		# Update
		frappe.db.set_value(self.doctype, self.name, "payment_entry", pe.name)
		frappe.db.set_value(self.doctype, self.name, "status", "Approved")


	def on_cancel(self):
		if self.payment_entry:
			pe = frappe.get_doc("Payment Entry", self.payment_entry)
			if pe.docstatus == 1:
				pe.cancel()

		self.status = "Cancelled"

	# -------------------------------------------------------
	# Journal Entry (Credit Note)
	# -------------------------------------------------------
	def _get_receivable_account(self):

		company = self.company or frappe.defaults.get_user_default("Company")
		acc = frappe.db.get_value("Company", company, "default_receivable_account")
		return acc

	def _create_journal_entry_if_needed(self):
		# Need a separate field: journal_entry
		if getattr(self, "journal_entry", None):
			return  # idempotent

		if not self.customer:
			frappe.throw("Customer is required")
		if not self.company:
			frappe.throw("Company is required")

		# # Get credit note account from settings
		# credit_note_account = frappe.db.get_value("Payu Setting", None, "credit_note_account")
		# if not credit_note_account:
		# 	frappe.throw("Payu Setting missing: credit_note_account (Account to Debit for Credit Note)")

		receivable_account = self._get_receivable_account()
		if not receivable_account:
			frappe.throw("Receivable account not found (Customer/Company default receivable account missing)")

		amount = flt(abs(frappe.db.get_value(
				"Sales Invoice",
				{
					"name": self.utr_number,
					"is_return": 1
				},
				"grand_total"
			))) or 0

		je = frappe.get_doc({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"company": self.company,
			"posting_date": today(),
			"user_remark": f"Credit Note against SO {self.sales_order} via Bank Transfer Request {self.name}",
			"accounts": [
				# Debit: Credit Note / Sales Return / Discount type account
				{
					"account": receivable_account,
					"party_type": "Customer",
					"party": self.customer,
					"debit_in_account_currency": amount,
					"credit_in_account_currency": 0,
					"reference_type": "Sales Invoice",
					"reference_name": self.utr_number
				},
				# Credit: Customer receivable (reduces receivable)
				{
					"account": receivable_account,
					"party_type": "Customer",
					"party": self.customer,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": amount,
					"is_advance": "Yes",
					"reference_type": "Sales Order",
					"reference_name": self.sales_order
				}
			]
		})

		je.insert(ignore_permissions=True)
		je.submit()

		# save back
		if frappe.get_meta(self.doctype).has_field("journal_entry"):
			self.db_set("journal_entry", je.name, update_modified=False)

		self.db_set("status", "Approved", update_modified=False)

	# -------------------------------------------------------
	# Cancel entry (PE / JE)
	# -------------------------------------------------------
	def _cancel_accounting_entry_if_exists(self):
		# cancel payment entry
		if self.payment_entry and frappe.db.exists("Payment Entry", self.payment_entry):
			pe = frappe.get_doc("Payment Entry", self.payment_entry)
			if pe.docstatus == 1:
				pe.cancel()

		# cancel journal entry
		je_name = getattr(self, "journal_entry", None)
		if je_name and frappe.db.exists("Journal Entry", je_name):
			je = frappe.get_doc("Journal Entry", je_name)
			if je.docstatus == 1:
				je.cancel()

	def mandatory(self):
		is_exists=frappe.get_all("Bank Transfer Request", filters={"bank_transaction_id": self.bank_transaction_id, "name": ["!=", self.name],"status": "Approved","docstatus": 1})
		if is_exists and self.bank_transaction_id and self.transfer_type != "Credit Note":
			frappe.throw("Bank Transaction ID already exists for another approved Bank Transfer Request")
		action = self.workflow_state
		if not self.transfer_type != "Credit Note" and not self.sales_order:
			frappe.throw("Sales Order is required for Bank Transfer")
		# frappe.throw(str(action))
		missing = []
		if action == "Approved" and self.transfer_type != "Credit Note":
			if not self.payment_proof:
				missing.append("Payment Proof")
			if not self.bank_transaction_id:
				missing.append("Bank Transaction ID")
			if not self.company_bank_account:
				missing.append("Company Bank Account")
		if missing:
			frappe.throw(
				"Please fill mandatory fields: " + ", ".join(missing)
			)

# Copyright (c) 2025, Abhishek and contributors
# For license information, please see license.txt

from pydoc import doc
import frappe
from frappe.model.document import Document
from frappe.utils import flt



class ApplyDealership(Document):

	def before_save(self):
		if self.amended_from and self.get("__islocal"):
			return
		self.reset_approval_process_if_plan_changed_on_amend()
		
		deposit = flt(self.plan_deposit_amount)
		deposit_amount = flt(self.deposit_amount)
		first_order_value = flt(self.first_order_value)
		approved_amount = flt(self.approved_amount)
		if self.override and approved_amount <= 0:
			frappe.throw("Approval Amount is required before enabling Override.")
		if self.order_override and not self.get("dealership_sales_order"):
			frappe.throw("At least one order is required in Dealership's orders before enabling Order Override.")

		# -----------------------------------------
		# STEP 1 → STEP 2
		# Pending for Review → Pending for Activation
		# (Valid dates filled)
		# -----------------------------------------

		if deposit > 0 and deposit_amount > 0 and self.has_value_changed("deposit_amount"):
			self.add_account_process()

		if (not self.valid_from) or (not self.valid_to):
			self.approval_status = "Pending for Review"
			self.form_status = "Dealership Deposit"
			return
		if (
			self.approval_status == "Override"
			and deposit_amount <= 0
			and approved_amount <= 0
			and self.valid_from
			and self.valid_to
		):
			self.approval_status = "Pending for Activation"
			self.form_status = "Dealership Deposit"
			return

		if (
			self.approval_status == "Pending for Review"
			and self.form_status == "Dealership Deposit"
			and self.valid_from
			and self.valid_to
		):
			self.approval_status = "Pending for Activation"
			return
		if self.approval_status == "Active" and self.docstatus == 0 and self.name:
			self.docstatus = 1
			self.create_dealership_profile()
			return
		# -----------------------------------------
		# STEP 2 → STEP 3
		# Pending for Activation → Pending for Approval
		# -----------------------------------------
		if (deposit <= 0) and (first_order_value <= 0):
			self.approval_status="Override"
			self.form_status="Aggreement"
			self.approval_date = frappe.utils.now()
		elif (deposit<=0) and (first_order_value>0):
			self.approval_status="Pending for Approval"
			self.form_status="First Order"
			self.approval_date = frappe.utils.now()
		elif deposit>0 and approved_amount>0 and approved_amount<deposit and not self.override:
			self.approval_status="Pending for Approval"
			self.form_status="Dealership Deposit"
		elif self.override and deposit_amount>=deposit and first_order_value>0 and not self.order_override and not self.total_paid_order_amount >= first_order_value:
			self.approval_status="Pending for Approval"
			self.form_status="First Order"
		# elif deposit>0 and first_order_value>0 and approved_amount>0 and not self.order_override:
		# 	self.approval_status="Pending for Approval"
		# 	self.form_status="First Order"
		elif not self.order_override and self.total_paid_order_amount >= first_order_value:
			self.approval_status = "Pending for Approval"
			self.form_status = "Aggreement"
		elif self.order_override and self.total_paid_order_amount <= first_order_value:
			self.approval_status = "Override"
			self.form_status = "Aggreement"
		elif deposit>0 and first_order_value<=0 and approved_amount>0:
			self.approval_status="Override"
			self.form_status="Aggreement"
		
		# -----------------------------------------
		# STEP 5 → Auto Submit
		# -----------------------------------------

	def reset_approval_process_if_plan_changed_on_amend(self):
		if not self.amended_from:
			return
		name=self.name or self.amended_from
		previous_plan = frappe.db.get_value(
			"Apply Dealership",
			name,
			"delership_plan",
		)
		if previous_plan == self.delership_plan:
			return

		self._clear_deposit_approval_docs()
		self._reset_approval_fields()

	def _clear_deposit_approval_docs(self):
		linked_docs = [self.name]
		if self.amended_from:
			linked_docs.append(self.amended_from)

		approvals = frappe.get_all(
			"Deposit Amount Payment Approal",
			filters={"view_dealership": ["in", linked_docs]},
			fields=["name"],
		)
		for approval in approvals:
			frappe.delete_doc(
				"Deposit Amount Payment Approal",
				approval.name,
				ignore_permissions=True,
				force=1,
			)

	def _reset_approval_fields(self):
		self.approval_status = "Pending for Review"
		self.form_status = "Dealership Deposit"
		self.deposit_amount = 0
		self.override=0
		self.order_override=0
		self.utr_check_no = None
		self.slip_attach = None
		self.current_date =None
		self.bank_transaction_id = None
		self.approved_amount = 0
		self.approval_date = None
		self.attach_slip = None
		self.remark = None

	def add_account_process(self):
		if not (self.plan_deposit_amount and self.deposit_amount and self.name):
			return
		if self.is_new():
			return

		# On amend-before-first-save, current doc may not exist in DB yet.
		# Always point approval to an existing Apply Dealership record.
		current_exists = frappe.db.exists("Apply Dealership", self.name)
		link_target = self.name if current_exists else (self.amended_from or self.name)
		key = self.amended_from or self.name

		# Find existing approval linked to original (or current)
		existing = frappe.db.get_value(
			"Deposit Amount Payment Approal",
			{"view_dealership": key},
			"name"
		)

		if existing:
			# Keep link valid even before amended doc is inserted.
			frappe.db.set_value(
				"Deposit Amount Payment Approal",
				existing,
				"view_dealership",
				link_target
			)
			return

		try:
			doc = frappe.get_doc({
				"doctype": "Deposit Amount Payment Approal",
				"view_dealership": link_target,
				"deposit_date": self.current_date,
				"utr__check_no": self.utr_check_no,
				"plan_deposit_amount": self.plan_deposit_amount,
				"deposit_amount": self.deposit_amount,
				"deposit_slip_attachment": self.slip_attach,
			})

			doc.insert(ignore_permissions=True)

		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				"Deposit Amount Payment Approval Creation"
			)
			raise

	def before_submit(self):
		# frappe.throw("Cannot submit the Dealership Application. Please contact support.")
		if not self.dealership_aggrement:
			frappe.throw("Agreement is required to submit this dealership")
		self.create_dealership_profile()

	def create_dealership_profile(self):
		if frappe.db.exists("Dealership Profile", {"dealership": self.name}):
			return

		try:
			profile = frappe.new_doc("Dealership Profile")
			profile.dealership = self.name
			profile.dealership_aggrement=self.dealership_aggrement
			# ✅ This will trigger before_save
			profile.save(ignore_permissions=True)

		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				"Dealership Profile Creation Failed"
			)
			frappe.throw("Failed to create Dealership Profile")
   
	def on_cancel(self):
		self.handle_dealership_profile_on_cancel()

	def handle_dealership_profile_on_cancel(self):

		profile_name = frappe.db.get_value(
			"Dealership Profile",
			{"dealership": self.name},
			"name"
		)

		if not profile_name:
			return

		profile = frappe.get_doc("Dealership Profile", profile_name)

		# Draft → delete
		if profile.docstatus == 0:
			frappe.delete_doc(
				"Dealership Profile",
				profile.name,
				ignore_permissions=True,
				force=1
			)

		# Submitted → cancel
		elif profile.docstatus == 1:
			profile.cancel()

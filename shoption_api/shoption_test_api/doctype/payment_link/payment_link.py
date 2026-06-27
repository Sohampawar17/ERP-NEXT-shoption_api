# Copyright (c) 2026, Abhishek and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class PaymentLink(Document):
	def before_insert(self):
		self.payment_link_status=1





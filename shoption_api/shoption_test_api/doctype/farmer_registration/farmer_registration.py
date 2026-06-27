# Copyright (c) 2025, Abhishek and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from shoption_api.dealer.api import generate_username
from frappe.desk.doctype.tag.tag import add_tag, remove_tag, get_tags

class FarmerRegistration(Document):
	def before_submit(self):
		self._create_user_and_customer_or_throw()

	def _create_user_and_customer_or_throw(self):
		try:
			mobile_no = str(self.mobile_number or "").strip()
			role = "Farmer"

			# choose display name source
			display_name = (self.party_name or self.first_name or "").strip()
			if not mobile_no or not display_name:
				frappe.throw("mobile_number and name are required")

			final_email = (self.email_id or f"{mobile_no}@gmail.com").strip().lower()
			lead_id = self.from_document
			registration_id = self.name

			# ---------------- USER: create or update ----------------
			user_name = frappe.db.exists("User", {"email": final_email})

			if user_name:
				# Email already used by another user
				final_email = f"{mobile_no}@gmail.com"

				counter = 1
				while frappe.db.exists("User", {"email": final_email}):
					final_email = f"{mobile_no}_{counter}@gmail.com"
					counter += 1

			# Always create a new user
			user = frappe.get_doc({
				"doctype": "User",
				"email": final_email,
				"first_name": display_name,
				"full_name": display_name,
				"mobile_no": mobile_no,
				"send_welcome_email": 0,
				"username": generate_username(),
				"role_profile_name": role
			})

			user.flags.ignore_permissions = True
			user.new_password = frappe.generate_hash(length=10)

			user.insert(ignore_permissions=True)

			api_secret = frappe.generate_hash(length=15)
			user.api_key = frappe.generate_hash(length=15)
			user.api_secret = api_secret

			user.save(ignore_permissions=True)
			# ---------------- CUSTOMER: create or update ----------------
			customer_name = (
				frappe.db.exists("Customer", {
					"custom_document_type": self.doctype,
					"custom_document_value": registration_id
				})
				or frappe.db.exists("Customer", {"mobile_no": mobile_no})
			)

			if customer_name:
				customer = frappe.get_doc("Customer", customer_name)

				# update fields
				customer.customer_name = display_name
				customer.mobile_no = mobile_no
				customer.customer_type = customer.customer_type or "Individual"
				customer.customer_group = customer.customer_group or role

				# keep lead if missing / update if you want always
				if lead_id:
					customer.lead_name = lead_id

				# ensure custom linkage exists
				customer.custom_document_type = self.doctype
				customer.custom_document_value = registration_id

				customer.save(ignore_permissions=True)

			else:
				if not frappe.db.exists("Customer Group", role):
					frappe.throw(f"Customer Group '{role}' does not exist")
				if lead_id and not frappe.db.exists("Lead", lead_id):
					frappe.throw(f"Lead '{lead_id}' does not exist")

				customer = frappe.get_doc({
					"doctype": "Customer",
					"customer_name": display_name,
					"mobile_no": mobile_no,
					"customer_type": "Individual",
					"customer_group": role,
					"lead_name": lead_id,
					"custom_document_type": self.doctype,
					"custom_document_value": registration_id
				})
				customer.insert(ignore_permissions=True)
			if lead_id:
				lead_tags = get_tags("Lead", lead_id)

			for tag in lead_tags:
				add_tag(tag, "Customer", customer.name)
			# ---------------- Portal user link: ensure ----------------
			if not any(pu.user == user.name for pu in (customer.portal_users or [])):
				customer.append("portal_users", {"user": user.name})
				customer.save(ignore_permissions=True)

			# ---------------- ADDRESSES: create or update ----------------
			address_data = {
				"address_title": display_name,
				"address_line1": self.address_line_1,
				"address_line2": self.address_line_2,
				"city": str(self.marketplace) if self.marketplace else None,
				"custom_tahshil": str(self.tahshil) if self.tahshil else None,
				"custom_district": str(self.district) if self.district else None,
				"state": self.state,
				"country": self.country,
				"pincode": str(self.pincode).strip() if self.pincode else None,
				"phone": mobile_no,
				"email_id": final_email,
			}

			def get_address_name(address_type):
				res = frappe.db.sql("""
					select a.name
					from `tabAddress` a
					join `tabDynamic Link` dl on dl.parent = a.name
					where dl.link_doctype='Customer'
					and dl.link_name=%s
					and a.address_type=%s
					limit 1
				""", (customer.name, address_type))
				return res[0][0] if res else None

			def upsert_address(address_type, is_primary, is_shipping):
				addr_name = get_address_name(address_type)
				if addr_name:
					addr = frappe.get_doc("Address", addr_name)
					addr.update({
						"address_type": address_type,
						"is_primary_address": 1 if is_primary else 0,
						"is_shipping_address": 1 if is_shipping else 0,
						**address_data
					})
					addr.save(ignore_permissions=True)
				else:
					frappe.get_doc({
						"doctype": "Address",
						"address_type": address_type,
						"is_primary_address": 1 if is_primary else 0,
						"is_shipping_address": 1 if is_shipping else 0,
						**address_data,
						"links": [{"link_doctype": "Customer", "link_name": customer.name}],
					}).insert(ignore_permissions=True)

			upsert_address("Billing", is_primary=True, is_shipping=False)
			upsert_address("Shipping", is_primary=False, is_shipping=True)

			# Optional store refs
			# self.customer = customer.name
			# self.user_id = user.name

		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				message=frappe.get_traceback(),
				title="before_submit: create_user_and_customer failed"
			)
			frappe.throw("User/Customer creation failed. Please check Error Log.")

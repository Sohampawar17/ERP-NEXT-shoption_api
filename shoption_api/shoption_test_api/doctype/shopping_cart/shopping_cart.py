import frappe
import json
from frappe.model.document import Document
from erpnext.stock.get_item_details import get_item_details

class ShoppingCart(Document):

	def before_save(self):
		self.customer = self.get_customer_from_user().get("parent")
		self.customer_group = frappe.get_cached_value(
			"Customer", self.customer, "customer_group"
		)

		for row in self.items:
			item_details = self.get_item_details_for_cart(
				row.item, row.quantity, row.brand
			)
			gst_rate = frappe.db.get_value(
            "Item Tax Template",
            item_details.get("item_tax_template"),
            "gst_rate"
			) or 0

			
			row.uom = item_details.get("uom")
			row.selling_price_list = item_details.get("price_list")
			row.min_qty = self.get_item_moq(row.item, self.customer_group) or 0
			row.rate = float(item_details.get("price_list_rate") or 0)
			row.discount = frappe.db.get_value(
						"Item Price",
						{"item_code": row.item, "price_list": row.selling_price_list},
						"custom_discount"
					) or 0

			row.rate_with_gst  = round(
				row.rate + (row.rate * gst_rate / 100), 2
			)
			row.amount = float(item_details.get("amount") or 0)

		self.total_quantity = sum(item.quantity for item in self.items)
		self.total_amount = sum(item.amount for item in self.items)

		# self.create_order()

	@frappe.whitelist()
	def get_item_moq(self,item_code, customer_group):
		moqs = frappe.get_all(
			"MOQ Items",
			filters={
				"parent": item_code,
				"customer_group": customer_group
			},
			fields=["min_qty"]
		)
		return moqs[0].min_qty if moqs else None

	@frappe.whitelist()
	def get_item_details_for_cart(self, item_code, qty, brand=None):
		"""
		Fetch optimized item details for shopping cart
		"""
		# --------- VALIDATIONS ----------
		if not item_code:
			frappe.throw("Item Code is required")

		if not self.customer:
			frappe.throw("Customer is required")

		# --------- GET PRICE LIST ---------
		price_list = frappe.db.get_value(
			"Price List",
			{
				"custom_customer_group": self.customer_group,
				"custom_brand": brand,
				"enabled": 1,
				"selling": 1
			},
			"name"
		)

		# Fallback if no price list found
		if not price_list:
			price_list = frappe.get_cached_value("Selling Settings", None, "default_price_list")

		# --------- BUILD ARGS CLEANLY ---------
		args = {
			"item_code": item_code,
			"customer": self.customer,
			"currency": self.currency,
			"company": self.company,
			"qty": qty,
			"doctype": "Sales Order",
			"price_list": price_list,
			"price_list_currency": self.currency
		}

		# --------- FETCH DETAILS ----------
		
		from erpnext.stock.get_item_details import get_item_details
		item_details = get_item_details(args)
		gst_rate = frappe.db.get_value(
        "Item Tax Template",
        item_details.get("item_tax_template"),
        "gst_rate"
    	) or 0
		item_details["price_list"] = price_list
		item_details["rate_with_gst"] = round(item_details.get("price_list_rate", 0) + (item_details.get("price_list_rate", 0) * gst_rate / 100), 2)
		item_details["amount"] = item_details.get("price_list_rate", 0) * float(qty)
		item_details["discount"]=frappe.db.get_value("Item Price",{"item_code":item_code,"price_list":price_list},"custom_discount") or 0
		return item_details


	# ---------- SERVER API METHOD ----------
	@frappe.whitelist()
	def get_customer_from_user(self):
		"""Fetch customer linked with selected User"""
		customer = frappe.db.get_value(
			"Portal User",
			{"user": self.user},
			["name", "parent"],
			as_dict=True
		)

		if not customer:
			return {"error": "No customer linked with this user"}

		return customer

	@frappe.whitelist()
	def create_order(self):
		"""Create Sales Order from Shopping Cart & Remove Ordered Items"""
		if not self.items:
			frappe.throw("No items in the shopping cart to create an order.")

		# Create Sales Order
		sales_order = frappe.new_doc("Sales Order")
		sales_order.customer = self.customer
		sales_order.customer_group = self.customer_group
		sales_order.currency = self.currency
		sales_order.company = self.company
		sales_order.delivery_date = frappe.utils.nowdate()

		# Keep remaining items
		remaining_items = []

		for item in self.items:
			if item.checkout:
				# Add to Sales Order
				sales_order.append("items", {
					"delivery_date": frappe.utils.nowdate(),
					"item_code": item.item,
					"qty": item.quantity,
					"rate": item.rate,
					"amount": item.amount
				})
			else:
				# Keep in cart
				remaining_items.append(item)
		sales_order.run_method("set_missing_values")
		sales_order.run_method("calculate_taxes_and_totals")
		# FIX: Remove Payment Schedule
		sales_order.payment_terms_template = ""
		sales_order.payment_schedule = []

		sales_order.insert()
		# Save Sales Order
		updated_doc = frappe.get_doc("Shopping Cart", self.name)

		# Remove only checked-out items
		new_items = []
		for item in updated_doc.items:
			if not item.checkout:
				new_items.append(item)

		updated_doc.set("items", new_items)

		# Save clean Shopping Cart
		updated_doc.save(ignore_permissions=True)
		return sales_order.name


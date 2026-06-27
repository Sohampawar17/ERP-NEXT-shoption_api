# # # Copyright (c) 2025, Abhishek and contributors
# # # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document

# class DealershipProfile(Document):

	# @frappe.whitelist()
	# def get_dealership_plan_range(self):
	# 	rows=frappe.get_all("Dealership Plan Range",filters={"parent":self.dealerhsip_plan},fields=["*"])
	# 	# frappe.msgprint(str(rows))

  	# 	frappe.msgprint("appending rows")
	# 	for row in rows:
	# 		self.append("dealership_plan_range",{
	# 			"notation":row.get("notation"),
	# 			"value":row.get("value"),
	# 			"in__percentage":row.get("in__percentage")
	# 		})
  
	# 	self.flags.ignore_validate = True
  

#     @frappe.whitelist()
#     def get_tahsils_from_apply_dealership(self):
#         self.set("tahsils", [])

#         apply_doc = frappe.get_doc("Apply Dealership", self.dealership)

#         for row in apply_doc.tahsils:
#             self.append("tahsils", {
#                 "tehsil": row.tehsil
#             })

#         self.flags.ignore_validate = True


#     @frappe.whitelist()
#     def get_marketplaces_from_apply_dealership(self):
#         self.set("marketplaces", [])

#         apply_doc = frappe.get_doc("Apply Dealership", self.dealership)

#         for row in apply_doc.marketplaces:
#             self.append("marketplaces", {
#                 "marketplace": row.marketplace
#             })

#         self.flags.ignore_validate = True

import frappe
from frappe.model.document import Document

class DealershipProfile(Document):

	def before_save(self):
		self.get_dealership_plan_range()
	
	@frappe.whitelist()
	def get_dealership_plan_range(self):
		rows=frappe.get_all("Dealership Plan Range",filters={"parent":self.dealerhsip_plan},fields=["*"])
		# frappe.msgprint(str(rows))

		frappe.msgprint("appending rows")

		self.set("dealership_plan_range", [])
		for row in rows:
			self.append("dealership_plan_range",{
				"notation":row.get("notation"),
				"value":row.get("value"),
				"in__percentage":row.get("in__percentage")
			})

		self.set("tahsils", [])
		apply_doc = frappe.get_doc("Apply Dealership", self.dealership)

		for row in apply_doc.tehsil:
			self.append("tahsils", {
				"tehsil": row.tehsil
			})
   
		self.set("marketplaces", [])
		# apply_doc = frappe.get_doc("Apply Dealership", self.dealership)

		for row in apply_doc.marketplaces:
			self.append("marketplaces", {
				"marketplace": row.marketplace
			})

		self.flags.ignore_validate = True
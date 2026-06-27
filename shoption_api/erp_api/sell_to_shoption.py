# import frappe

# def fill_customer_details(doc, method):
#     if not doc.user_id:
#         return

#     # Get linked Customer
#     customer = frappe.db.get_value("Portal User", {"user": doc.user_id}, "parent")
#     if not customer:
#         frappe.throw("No Customer linked to this User ID")

#     doc.customer_id = customer
#     doc.customer_name = frappe.db.get_value("Customer", customer, "customer_name")

#     # Fetch Registration
#     reg_type = frappe.db.get_value("Customer", customer, "custom_document_type")
#     reg_value = frappe.db.get_value("Customer", customer, "custom_document_value")

#     if not (reg_type and reg_value):
#         return

#     reg = frappe.get_doc(reg_type, reg_value)

#     # Auto-fill fields
#     doc.state = reg.state
#     doc.district = reg.district
#     doc.tahshil = reg.tahshil

import frappe

def fill_details(doc, method):

    # Step 1: Validate User ID
    if not doc.user_id:
        return

    # Step 2: Find linked customer from Portal Users
    customer = frappe.db.get_value(
        "Portal User", 
        {"user": doc.user_id}, 
        "parent"
    )

    if not customer:
        frappe.throw("No Customer linked with this User ID")

    doc.customer_id = customer
    doc.customer_name = frappe.db.get_value("Customer", customer, "customer_name")

    # Step 3: Get Registration Doc
    reg_type, reg_value = frappe.db.get_value(
        "Customer",
        customer,
        ["custom_document_type", "custom_document_value"]
    ) or (None, None)

    if not reg_type or not reg_value:
        return

    reg = frappe.get_doc(reg_type, reg_value)

    # Step 4: Auto-fill Address Fields
    doc.state = getattr(reg, "state", "")
    doc.district = getattr(reg, "district", "")
    doc.tahshil = getattr(reg, "tahshil", "")

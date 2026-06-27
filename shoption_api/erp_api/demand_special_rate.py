import frappe

def fill_details(doc, method):
    if not doc.user_id:
        return

    customer = frappe.db.get_value(
        "Portal User",
        {"user": doc.user_id},
        "parent"
    )

    if not customer:
        frappe.throw("No Customer linked with this User ID")

    doc.customer_id = customer
    doc.customer_name = frappe.db.get_value("Customer", customer, "customer_name")

    reg_type, reg_value = frappe.db.get_value(
        "Customer",
        customer,
        ["custom_document_type", "custom_document_value"]
    ) or (None, None)

    if not reg_type or not reg_value:
        return

    reg = frappe.get_doc(reg_type, reg_value)

    doc.state = getattr(reg, "state", "")
    doc.district = getattr(reg, "district", "")
    doc.tahshil = getattr(reg, "tahshil", "")

import frappe

def create_customer_address(doc, method):

    
    # If no linked registration, skip entirely (manual customer creation)
    if not getattr(doc, "custom_document_type", None) or not getattr(doc, "custom_document_value", None):
        return

    # Load linked Registration Doc
    reg = frappe.get_doc(doc.custom_document_type, doc.custom_document_value)

    # Address Title
    address_title = (
        getattr(reg, "first_name", None) 
        or getattr(reg, "shop_name", None) 
        or doc.customer_name 
        or f"Address-{doc.name}"
    )


    address = frappe.get_doc({
        "doctype": "Address",
        "address_title": address_title,
        "address_type": "Billing",

        "address_line1": reg.address_line_1,
        "address_line2": reg.address_line_2,

        "pincode": str(reg.pincode) if reg.pincode else "",   # <-- FIXED

        "country": reg.country,
        "state": reg.state,
        "custom_district": reg.district,
        "custom_tahshil": reg.tahshil,
        "city": reg.marketplace,

        # "custom_document": "Customer",
        # "custom_document_value": doc.name
    })

    # Link to Customer
    address.append("links", {
        "link_doctype": "Customer",
        "link_name": doc.name
    })

    address.insert(ignore_permissions=True)
    frappe.db.commit()



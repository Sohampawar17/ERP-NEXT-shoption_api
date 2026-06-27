@frappe.whitelist()
def create_user_and_customer(mobile_no, name, role):

    if not mobile_no:
        return {"status": False, "message": "mobile_no is required"}

    if not name:
        return {"status": False, "message": "name is required"}

    # ✅ Check Customer Already Exists
    existing = frappe.db.exists("Customer", {"mobile_no": mobile_no})
    if existing:
        return {
            "status": False,
            "message": "Customer already exists",
            "customer_id": existing
        }

    # ✅ Create User WITH Role Profile
    user = frappe.get_doc({
        "doctype": "User",
        "email": f"{mobile_no}@demo.com",
        "first_name": name,
        "mobile_no": mobile_no,
        "send_welcome_email": 0,
        "role_profile_name": role     #  "Farmer" / "Dealer"
    })
    user.insert(ignore_permissions=True)

    # ✅ Create Customer
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": name,
        "mobile_no": mobile_no,
        "customer_group": role        #  Same mapping
    })
    customer.insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "status": True,
        "message": "User & Customer Created Successfully",
        "user_id": user.name,
        "customer_id": customer.name,
        "role": role
    }

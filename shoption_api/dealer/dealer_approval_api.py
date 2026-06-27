import frappe

def _auth():
    cfg = frappe.get_site_config()
    key = cfg.get("shoption_api_key")
    secret = cfg.get("shoption_api_secret")

    incoming_key = frappe.get_request_header("X-API-KEY")
    incoming_secret = frappe.get_request_header("X-API-SECRET")

    if incoming_key != key or incoming_secret != secret:
        return False, {"status": False, "message": "Unauthorized"}

    return True, None


@frappe.whitelist(allow_guest=True)
def manager_approval(mobile_no=None, action=None, remarks=None):
    ok, err = _auth()
    if not ok: return err

    if not mobile_no:
        return {"status": False, "message": "mobile_no is required"}

    if action not in ["Approved", "Rejected"]:
        return {"status": False, "message": "Invalid action"}

    customer_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
    if not customer_name:
        return {"status": False, "message": "Customer not found"}

    customer = frappe.get_doc("Customer", customer_name)

    # Update dealer status
    customer.custom_dealer_status = action
    if remarks:
        customer.custom_dealer_remarks = remarks

    customer.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": True,
        "message": f"Dealer {action} successfully",
        "dealer_status": customer.custom_dealer_status
    }


@frappe.whitelist(allow_guest=True)
def product_manager_approval(mobile_no=None, action=None):
    """
    Product Manager Approval
    action = "approve" or "reject"
    """

    # ---- Header Auth ----
    cfg = frappe.get_site_config()
    expected_key = cfg.get("shoption_api_key")
    expected_secret = cfg.get("shoption_api_secret")

    incoming_key = frappe.get_request_header("X-API-KEY")
    incoming_secret = frappe.get_request_header("X-API-SECRET")

    if incoming_key != expected_key or incoming_secret != expected_secret:
        return {"status": False, "message": "Unauthorized"}

    # ---- Validate Input ----
    if not mobile_no:
        return {"status": False, "message": "mobile_no is required"}

    if action not in ["approve", "reject"]:
        return {"status": False, "message": "Invalid action"}

    # ---- Get Customer ----
    customer_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
    if not customer_name:
        return {"status": False, "message": "Customer not found"}

    customer = frappe.get_doc("Customer", customer_name)

    # ---- Apply Approval ----
    if action == "approve":
        customer.custom_product_access = 1
        msg = "Product access granted"
    else:
        customer.custom_product_access = 0
        msg = "Product access rejected"

    customer.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": True,
        "message": msg,
        "product_access": customer.custom_product_access
    }

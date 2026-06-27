import frappe
from frappe.utils.file_manager import save_file

# Utility: Header Authentication
def _check_api_auth():
    cfg = frappe.get_site_config()
    expected_key = cfg.get("shoption_api_key")
    expected_secret = cfg.get("shoption_api_secret")

    incoming_key = frappe.get_request_header("X-API-KEY")
    incoming_secret = frappe.get_request_header("X-API-SECRET")

    if not incoming_key or not incoming_secret:
        return False, {"status": False, "message": "Missing authentication headers"}

    if incoming_key != expected_key or incoming_secret != expected_secret:
        return False, {"status": False, "message": "Unauthorized"}

    return True, None


# 1️⃣ GST DOCUMENT UPLOAD (FRONT/BACK)
@frappe.whitelist(allow_guest=True)
def upload_gst_document(mobile_no=None, doc_type=None, file=None):
    """
    Upload GST related documents:
    doc_type -> 'gst_front', 'gst_back', 'shop_photo', 'visiting_card', 'passbook'
    """

    # ---- AUTH CHECK ----
    ok, err = _check_api_auth()
    if not ok:
        return err

    # ---- VALIDATE INPUTS ----
    if not mobile_no:
        return {"status": False, "message": "mobile_no is required"}

    if not doc_type:
        return {"status": False, "message": "doc_type is required"}

    if not file:
        return {"status": False, "message": "file is required"}

    allowed_types = ["gst_front", "gst_back", "shop_photo", "visiting_card", "passbook"]

    if doc_type not in allowed_types:
        return {"status": False, "message": f"Invalid doc_type. Allowed: {allowed_types}"}

    # ---- GET CUSTOMER ----
    customer_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
    if not customer_name:
        return {"status": False, "message": "Customer not found"}

    customer = frappe.get_doc("Customer", customer_name)

    # ---- SAVE FILE ----
    try:
        saved_file = save_file(
            f"{doc_type}_{mobile_no}.jpg",
            file,
            "Customer",
            customer.name,
            is_private=1
        )

        # store file URL in Customer custom field
        field_map = {
            "gst_front": "custom_gst_front",
            "gst_back": "custom_gst_back",
            "shop_photo": "custom_shop_photo",
            "visiting_card": "custom_visiting_card",
            "passbook": "custom_passbook"
        }

        fieldname = field_map.get(doc_type)
        setattr(customer, fieldname, saved_file.file_url)

        # document upload means GST verification required
        customer.custom_gst_status = "Pending"
        customer.custom_dealer_status = "Pending"

        customer.save(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"GST Document Upload Error: {e}", "upload_gst_document")
        return {"status": False, "message": "Upload failed"}

    return {
        "status": True,
        "message": f"{doc_type} uploaded successfully",
        "file_url": saved_file.file_url,
        "gst_status": customer.custom_gst_status,
        "dealer_status": customer.custom_dealer_status
    }


# ------------------------------------------------------
# 2️⃣ GET GST DOCUMENT STATUS (all uploaded docs)
# ------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def get_gst_documents(mobile_no=None):
    ok, err = _check_api_auth()
    if not ok:
        return err

    if not mobile_no:
        return {"status": False, "message": "mobile_no is required"}

    customer_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
    if not customer_name:
        return {"status": False, "message": "Customer not found"}

    customer = frappe.get_doc("Customer", customer_name)

    return {
        "status": True,
        "documents": {
            "gst_front": customer.custom_gst_front,
            "gst_back": customer.custom_gst_back,
            "shop_photo": customer.custom_shop_photo,
            "visiting_card": customer.custom_visiting_card,
            "passbook": customer.custom_passbook,
        },
        "gst_status": customer.custom_gst_status,
        "dealer_status": customer.custom_dealer_status
    }


# ------------------------------------------------------
# 3️⃣ PLACEHOLDER: GST OTP VERIFY (provider API pending)
# ------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def verify_gst_otp(mobile_no=None, gst_number=None, otp=None):
    """
    This function will be updated once GST provider gives API access.
    For now: only records data.
    """

    ok, err = _check_api_auth()
    if not ok:
        return err

    if not mobile_no or not gst_number:
        return {"status": False, "message": "mobile_no and gst_number required"}

    customer_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
    if not customer_name:
        return {"status": False, "message": "Customer not found"}

    customer = frappe.get_doc("Customer", customer_name)

    # store gst number
    customer.custom_gst_number = gst_number

    # TEMPORARY UNTIL API IS PROVIDED
    customer.custom_get_status = "Pending OTP Verification"

    customer.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": True,
        "message": "GST OTP verification pending (API access required)",
        "gst_status": customer.custom_get_status
    }

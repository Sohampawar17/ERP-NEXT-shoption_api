import frappe
import json
import requests

# Disable all Frappe login/auth enforcement
no_cache = True
no_login_required = True
allow_guest = True

@frappe.whitelist(allow_guest=True)
def send_gst_otp(gst_number=None):

    if not gst_number:
        return {"status": False, "message": "gst_number required"}

    site_cfg = frappe.get_site_config()
    gst_token = site_cfg.get("gst_api_token")

    headers = {
        "Authorization": gst_token,
        "Content-Type": "application/json"
    }

    payload = {"id_number": gst_number}

    try:
        resp = requests.post(
            "https://kyc-api.aadhaarkyc.io/api/v1/corporate-otp/gstin/init",
            headers=headers,
            data=json.dumps(payload),
            timeout=12
        )
        data = resp.json()
    except:
        return {"status": False, "message": "Provider API Error"}

    if not data.get("success"):
        return {"status": False, "message": data.get("message")}

    client_id = data.get("data", {}).get("client_id")

    return {
        "status": True,
        "message": "OTP Sent Successfully",
        "client_id": client_id
    }

@frappe.whitelist(allow_guest=True)
def verify_gst_otp(client_id=None, otp=None):

    if not client_id or not otp:
        return {"status": False, "message": "client_id and otp required"}

    site_cfg = frappe.get_site_config()
    gst_token = site_cfg.get("gst_api_token")

    headers = {"Authorization": gst_token, "Content-Type": "application/json"}
    payload = {"client_id": client_id, "otp": str(otp)}

    try:
        resp = requests.post(
            "https://kyc-api.aadhaarkyc.io/api/v1/corporate-otp/gstin/submit-otp",
            headers=headers,
            data=json.dumps(payload),
            timeout=12
        )
        response_json = resp.json()
    except:
        return {"status": False, "message": "Provider API Error"}

    verified = response_json.get("data", {}).get("verified", False)

    return {
        "status": True,
        "verified": verified,
        "message": "GST Verified Successfully" if verified else "Invalid GST / OTP"
    }


# @frappe.whitelist(allow_guest=True) 
# def _check_api_auth():
#     frappe.local.no_login_required = True
#     frappe.local.no_cache = True

#     cfg = frappe.get_site_config()
#     expected_key = cfg.get("shoption_api_key")
#     expected_secret = cfg.get("shoption_api_secret")

#     incoming_key = frappe.get_request_header("X-API-KEY")
#     incoming_secret = frappe.get_request_header("X-API-SECRET")

#     if not incoming_key or not incoming_secret:
#         return False, {
#             "status": False,
#             "message": "Missing authentication headers"
#         }

#     if incoming_key != expected_key or incoming_secret != expected_secret:
#         frappe.log_error("Invalid API authentication attempt", "shoption_api.auth_failure")
#         return False, {"status": False, "message": "Unauthorized"}

#     return True, None

# @frappe.whitelist(allow_guest=True)
# def _safe_set_customer_field(customer, fieldname, value):
#     frappe.local.no_login_required = True
#     frappe.local.no_cache = True

#     try:
#         setattr(customer, fieldname, value)
#         customer.save(ignore_permissions=True)
#     except:
#         try:
#             frappe.db.set_value("Customer", customer.name, fieldname, value, update_modified=False)
#         except:
#             pass


# @frappe.whitelist(allow_guest=True)
# def send_gst_otp(mobile_no=None, gst_number=None):
#     frappe.local.no_login_required = True
#     frappe.local.no_cache = True

#     ok, err = _check_api_auth()
#     if not ok:
#         return err

#     if not mobile_no or not gst_number:
#         return {"status": False, "message": "mobile_no and gst_number required"}

#     cust_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
#     if not cust_name:
#         return {"status": False, "message": "Customer not found"}

#     customer = frappe.get_doc("Customer", cust_name)

#     site_cfg = frappe.get_site_config()
#     gst_token = site_cfg.get("gst_api_token")

#     headers = {
#         "Authorization": gst_token,
#         "Content-Type": "application/json"
#     }

#     payload = {"id_number": gst_number}

#     try:
#         resp = requests.post(
#             "https://kyc-api.aadhaarkyc.io/api/v1/corporate-otp/gstin/init",
#             headers=headers,
#             data=json.dumps(payload),
#             timeout=12
#         )
#         data = resp.json()
#     except Exception as e:
#         frappe.log_error(f"GST INIT failed: {e}", "gst_api.send_gst_otp")
#         return {"status": False, "message": "Provider API error"}

#     if not data.get("success"):
#         return {"status": False, "message": data.get("message"), "data": data}

#     resp_data = data.get("data") or {}
#     client_id = resp_data.get("client_id")

#     _safe_set_customer_field(customer, "custom_gst_number", gst_number)
#     _safe_set_customer_field(customer, "custom_gst_client_id", client_id)
#     _safe_set_customer_field(customer, "custom_get_status", "OTP Sent")

#     frappe.db.commit()

#     return {
#         "status": True,
#         "message": "GST INIT success",
#         "client_id": client_id,
#         "raw": resp_data
#     }

# @frappe.whitelist(allow_guest=True)
# def verify_gst_otp(mobile_no=None, otp=None):
#     frappe.local.no_login_required = True
#     frappe.local.no_cache = True

#     ok, err = _check_api_auth()
#     if not ok:
#         return err

#     if not mobile_no or not otp:
#         return {"status": False, "message": "mobile_no and otp required"}

#     cust_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
#     if not cust_name:
#         return {"status": False, "message": "Customer not found"}

#     customer = frappe.get_doc("Customer", cust_name)
#     client_id = customer.custom_gst_client_id

#     if not client_id:
#         return {"status": False, "message": "Run send_gst_otp first"}

#     site_cfg = frappe.get_site_config()
#     gst_token = site_cfg.get("gst_api_token")

#     headers = {"Authorization": gst_token, "Content-Type": "application/json"}
#     payload = {"client_id": client_id, "otp": str(otp)}

#     try:
#         resp = requests.post(
#             "https://kyc-api.aadhaarkyc.io/api/v1/corporate-otp/gstin/submit-otp",
#             headers=headers,
#             data=json.dumps(payload),
#             timeout=12
#         )
#         response_json = resp.json()
#     except:
#         return {"status": False, "message": "Provider API error"}

#     data = response_json.get("data") or {}

#     # If provider returns no data
#     if not data:
#         return {
#             "status": False,
#             "message": "OTP verification failed",
#             "raw": response_json
#         }

#     verified = data.get("verified", False)

#     if verified:
#         _safe_set_customer_field(customer, "custom_get_status", "Verified")
#         _safe_set_customer_field(customer, "custom_gst_verified", 1)
#         _safe_set_customer_field(customer, "custom_dealer_status", "Pending Approval")
#     else:
#         _safe_set_customer_field(customer, "custom_get_status", "Rejected")

#     frappe.db.commit()

#     return {
#         "status": True,
#         "verified": bool(verified),
#         "gst_status": customer.custom_get_status,
#         "dealer_status": customer.custom_dealer_status,
#         "raw": data
#     }

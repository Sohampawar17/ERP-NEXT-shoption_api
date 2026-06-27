import frappe

# If you placed _check_api_auth elsewhere (e.g. otp/api.py), import it:
# from shoption_api.otp.api import _check_api_auth

def _check_api_auth_local():
    """Fallback: simple header auth check if not imported."""
    cfg = frappe.get_site_config()
    expected_key = cfg.get("shoption_api_key")
    expected_secret = cfg.get("shoption_api_secret")
    incoming_key = frappe.get_request_header("X-API-KEY")
    incoming_secret = frappe.get_request_header("X-API-SECRET")
    if not incoming_key or not incoming_secret:
        return False, {"status": False, "message": "Missing authentication headers"}
    if incoming_key != expected_key or incoming_secret != expected_secret:
        frappe.log_error("Invalid API auth attempt", "shoption_api.auth")
        return False, {"status": False, "message": "Unauthorized"}
    return True, None

@frappe.whitelist(allow_guest=True)
def get_dealer_status(mobile_no=None):
    """
    Input: mobile_no (string)
    Returns: json with status flags for onboarding flow.
    """
    # header auth (use the project-level check if available)
    ok, err = _check_api_auth_local()
    if not ok:
        return err

    if not mobile_no:
        return {"status": False, "message": "mobile_no required"}

    mobile = "".join(ch for ch in str(mobile_no) if ch.isdigit())
    if len(mobile) < 10:
        return {"status": False, "message": "Invalid mobile"}

    # Look for Customer
    cust_name = frappe.db.get_value("Customer", {"mobile_no": mobile}, "name")
    if not cust_name:
        # new user
        return {
            "status": True,
            "mobile_no": mobile,
            "exists": False,
            "profile_status": "new_dealer",
            "kyc_status": None,
            "marketplaces_assigned": []
        }

    # existing customer -> get related flags (change field names to match your doctype)
    # We expect a custom Dealer Profile doctype or custom fields on Customer:
    # - custom_is_profile_completed
    # - custom_kyc_status (pending/verified/rejected)
    # - custom_has_gbru_access (1/0)
    cust = frappe.get_doc("Customer", cust_name)

    profile_completed = getattr(cust, "custom_is_profile_completed", 0) or 0
    kyc_status = getattr(cust, "custom_kyc_status", "") or ""
    has_brand_access = getattr(cust, "custom_has_gbru_access", 0) or 0

    # marketplaces assigned - if using a child table or mapping doctype, adjust accordingly
    marketplaces = []
    try:
        # try child table name 'marketplace_mappings' with field 'marketplace'
        if hasattr(cust, "marketplace_mappings"):
            for row in cust.get("marketplace_mappings") or []:
                marketplaces.append(row.get("marketplace"))
        else:
            # fallback: query Marketplace Master linked to customer via a mapping doctype
            res = frappe.db.get_all("Dealer Marketplace", filters={"customer": cust.name}, fields=["marketplace"])
            marketplaces = [r.marketplace for r in res]
    except Exception:
        marketplaces = []

    # decide profile_status
    if not profile_completed:
        profile_status = "profile_pending"
    elif kyc_status and kyc_status.lower() in ("pending", "verified", "rejected"):
        if kyc_status.lower() == "pending":
            profile_status = "kyc_pending"
        elif kyc_status.lower() == "verified":
            profile_status = "kyc_verified"
        else:
            profile_status = "kyc_rejected"
    else:
        profile_status = "profile_completed"

    if has_brand_access:
        profile_status = "full_access"

    return {
        "status": True,
        "mobile_no": mobile,
        "exists": True,
        "profile_status": profile_status,
        "kyc_status": kyc_status,
        "marketplaces_assigned": marketplaces
    }

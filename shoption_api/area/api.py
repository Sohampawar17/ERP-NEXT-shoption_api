
import frappe

# AUTH CHECK
def _check_api_auth():
    cfg = frappe.get_site_config()

    if frappe.get_request_header("X-API-KEY") != cfg.get("shoption_api_key"):
        return False, {"status": False, "message": "Unauthorized"}

    if frappe.get_request_header("X-API-SECRET") != cfg.get("shoption_api_secret"):
        return False, {"status": False, "message": "Unauthorized"}

    return True, None


# HELPERS
def _ok(data, msg):
    return {"status": True, "message": msg, "data": data}


def _err(msg):
    return {"status": False, "message": msg}


# API 1: Countries
@frappe.whitelist(allow_guest=True)
def get_countries():
    
    frappe.set_user("Administrator")
    ok, err = _check_api_auth()
    if not ok:
        return err

    rows = frappe.get_list(
        "Country",
        fields=["name as id", "country_name as name"],
        order_by="country_name asc"
    )

    return _ok(rows, "Countries fetched")

# API 2: Get states
@frappe.whitelist(allow_guest=True)
def get_states(name=None):
    
    frappe.set_user("Administrator")
    
    ok, err = _check_api_auth()
    if not ok:
        return err

    if not name:
        return {"status": False, "message": "name is required"}

    rows = frappe.get_list(
        "Territory",
        filters={"custom_country": name},   # LINK FIELD to Country
        fields=["name as id", "territory_name as name"],
        order_by="territory_name asc"
    )

    return {"status": True, "message": "States fetched", "data": rows}



# API 3: Districts
@frappe.whitelist(allow_guest=True)
def get_districts(state_id=None):
    
    frappe.set_user("Administrator")
    ok, err = _check_api_auth()
    if not ok:
        return err

    if not state_id:
        return _err("state_id is required")

    rows = frappe.get_list(
        "District",
        filters={"state": state_id},
        fields=["name as id", "district_name as name"],
        order_by="district_name asc"
    )

    return _ok(rows, "Districts fetched")


# API 4: Tahshils
@frappe.whitelist(allow_guest=True)
def get_tahsils(district_id=None):
    
    frappe.set_user("Administrator")
    ok, err = _check_api_auth()
    if not ok:
        return err

    if not district_id:
        return _err("district_id is required")

    rows = frappe.get_list(
        "Tahshil",
        filters={"district": district_id},
        fields=["name as id", "tahshil as name"],
        order_by="tahshil asc"
    )

    return _ok(rows, "Tahshils fetched")

# API 5: Marketplaces
@frappe.whitelist(allow_guest=True)
def get_marketplaces(tehsil_id=None):

    frappe.set_user("Administrator")
    
    ok, err = _check_api_auth()
    if not ok:
        return err

    if not tehsil_id:
        return {"status": False, "message": "tehsil_id is required"}

    # since Tehsil ID = DocName
    tehsil_name = tehsil_id

    rows = frappe.get_list(
        "Marketplace",
        filters={"tahshil": tehsil_name, "status": "Approved"},
        fields=["name as id", "marketplace_name as name"],
        order_by="marketplace_name asc"
    )

    return {"status": True, "message": "Marketplaces fetched", "data": rows}

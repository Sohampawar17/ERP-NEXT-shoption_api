import frappe

# ------------------------------
# COMMON API AUTH
# ------------------------------
def api_auth():
    """Validate API KEY + SECRET (simple & strong)."""
    cfg = frappe.get_site_config()

    key = frappe.get_request_header("X-API-KEY")
    secret = frappe.get_request_header("X-API-SECRET")

    if not key or not secret:
        frappe.throw("Missing authentication headers")

    if key != cfg.get("shoption_api_key") or secret != cfg.get("shoption_api_secret"):
        frappe.throw("Unauthorized API Access")

    return True


# ------------------------------
# FORCE POST (optional but recommended)
# ------------------------------
def require_post():
    if frappe.request.method != "POST":
        frappe.throw("Method Not Allowed — Only POST allowed")


# ------------------------------
# SIMPLE FIELD VALIDATION (optional use)
# ------------------------------
def allowed_fields(input_data: dict, allowed_list: list):
    for key in input_data.keys():
        if key not in allowed_list:
            frappe.throw(f"Invalid field: {key}")


# ------------------------------
# CLEAN UNIFIED RESPONSE FORMAT
# ------------------------------
def api_response(status=True, message="", data=None, ispopup=False):
    return {
        "status": status,
        "message": message,
        "data": data or [],
        "ispopup": ispopup,
    }


# pagenation utility
def paginate(doctype, filters=None, fields=None, page=1, page_size=50, order_by="creation desc"):
    page = int(page)
    page_size = int(page_size)

    start = (page - 1) * page_size

    data = frappe.get_list(
        doctype,
        filters=filters,
        fields=fields,
        limit_start=start,
        limit_page_length=page_size,
        order_by=order_by
    )

    total = frappe.db.count(doctype, filters)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": data
    }

def get_employee_by_user(user, fields=["name"]):
    if isinstance(fields, str):
        fields = [fields]
    emp_data = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        fields,
        as_dict=1,
    )
    return emp_data
# import frappe
# from shoption_api.api.common import api_auth, make_response

# def api_auth():
#     cfg = frappe.get_site_config()
#     key = frappe.get_request_header("X-API-KEY")
#     secret = frappe.get_request_header("X-API-SECRET")

#     if key != cfg.get("shoption_api_key") or secret != cfg.get("shoption_api_secret"):
#         frappe.throw("Unauthorized API Access")

# def make_response(data):
#     return {
#         "status": True,
#         "count": len(data),
#         "data": data
#     }
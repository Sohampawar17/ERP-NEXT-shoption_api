# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_customers(search=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     meta = frappe.get_meta("Customer")
#     fields_available = {df.fieldname for df in meta.fields}

#     filters = {}

#     if search and "customer_name" in fields_available:
#         filters["customer_name"] = ["like", f"%{search}%"]

#     safe_fields = []
#     if "customer_name" in fields_available: safe_fields.append("customer_name")
#     if "mobile_no" in fields_available: safe_fields.append("mobile_no")
#     if "customer_group" in fields_available: safe_fields.append("customer_group")

#     try:
#         data = frappe.get_list(
#             "Customer",
#             filters=filters,
#             fields=["name as customer_id"] + safe_fields
#         )
#     except:
#         data = []

#     return api_response(True, "Customer list fetched", data)

# pagination update 29/11
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_customers(search=None, page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # Convert input safely
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page = 1
        page_size = 20

    meta = frappe.get_meta("Customer")
    fields_available = {df.fieldname for df in meta.fields}

    filters = {}

    if search and "customer_name" in fields_available:
        filters["customer_name"] = ["like", f"%{search}%"]

    # safe fields
    safe_fields = []
    if "customer_name" in fields_available: safe_fields.append("customer_name")
    if "mobile_no" in fields_available: safe_fields.append("mobile_no")
    if "customer_group" in fields_available: safe_fields.append("customer_group")

    start = (page - 1) * page_size

    try:
        data = frappe.get_list(
            "Customer",
            filters=filters,
            fields=["name as customer_id"] + safe_fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )
    except:
        data = []

    total_count = frappe.db.count("Customer", filters)
    total_pages = (total_count + page_size - 1) // page_size

    response = {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": data
    }

    return api_response(True, "Customer list fetched", response)

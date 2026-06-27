# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_price_list(price_list=None, item_code=None):
#     api_auth()
#     require_post()

#     frappe.set_user("Administrator")

#     if not price_list:
#         return api_response(False, "price_list is required")

#     meta = frappe.get_meta("Item Price")
#     fields_available = {df.fieldname for df in meta.fields}

#     filters = {"price_list": price_list}

#     if item_code and "item_code" in fields_available:
#         filters["item_code"] = item_code

#     safe_fields = []
#     if "item_code" in fields_available: safe_fields.append("item_code")
#     if "item_name" in fields_available: safe_fields.append("item_name")
#     if "price_list_rate" in fields_available: safe_fields.append("price_list_rate")

#     try:
#         data = frappe.get_list("Item Price", filters=filters, fields=safe_fields)
#     except:
#         data = []

#     return api_response(True, "Price list fetched", data)

# Pagination update 29/11
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_price_list(price_list=None, item_code=None, page=1, page_size=20):
    api_auth()
    require_post()

    frappe.set_user("Administrator")

    if not price_list:
        return api_response(False, "price_list is required")

    # safe convert
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page = 1
        page_size = 20

    meta = frappe.get_meta("Item Price")
    fields_available = {df.fieldname for df in meta.fields}

    filters = {"price_list": price_list}

    if item_code and "item_code" in fields_available:
        filters["item_code"] = item_code

    safe_fields = []
    if "item_code" in fields_available: safe_fields.append("item_code")
    if "item_name" in fields_available: safe_fields.append("item_name")
    if "price_list_rate" in fields_available: safe_fields.append("price_list_rate")

    start = (page - 1) * page_size

    try:
        data = frappe.get_list(
            "Item Price",
            filters=filters,
            fields=safe_fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        total = frappe.db.count("Item Price", filters)
        total_pages = (total + page_size - 1) // page_size

        response = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data
        }

        return api_response(True, "Price list fetched", response)

    except Exception:
        return api_response(True, "Price list fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

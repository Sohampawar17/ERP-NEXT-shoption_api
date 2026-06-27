# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_item_prices(item_code=None, price_list=None, company=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     if not item_code:
#         return api_response(False, "item_code is required")

#     meta = frappe.get_meta("Item Price")
#     fields_available = {df.fieldname for df in meta.fields}

#     filters = {"item_code": item_code}

#     if price_list and "price_list" in fields_available:
#         filters["price_list"] = price_list

#     if company and "company" in fields_available:
#         filters["company"] = company

#     safe_fields = []
#     for f in ["item_code", "item_name", "price_list", "price_list_rate",
#               "valid_from", "valid_upto", "currency", "uom"]:
#         if f in fields_available:
#             safe_fields.append(f)

#     try:
#         data = frappe.get_list("Item Price", filters=filters, fields=safe_fields)
#     except:
#         data = []

#     return api_response(True, "Item prices fetched", data)

# Pagination update 29/11
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_item_prices(item_code=None, price_list=None, company=None, page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not item_code:
        return api_response(False, "item_code is required")

    # safe conversion
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page = 1
        page_size = 20

    meta = frappe.get_meta("Item Price")
    fields_available = {df.fieldname for df in meta.fields}

    filters = {"item_code": item_code}

    if price_list and "price_list" in fields_available:
        filters["price_list"] = price_list

    if company and "company" in fields_available:
        filters["company"] = company

    safe_fields = []
    for f in ["item_code", "item_name", "price_list", "price_list_rate",
              "valid_from", "valid_upto", "currency", "uom"]:
        if f in fields_available:
            safe_fields.append(f)

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

        return api_response(True, "Item prices fetched", response)

    except Exception:
        return api_response(True, "Item prices fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

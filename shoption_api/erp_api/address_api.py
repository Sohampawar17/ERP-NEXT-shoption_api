# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_address(customer=None):
#     api_auth()
#     require_post()
    
#     frappe.set_user("Administrator")

#     if not customer:
#         return api_response(False, "customer is required")

#     try:
#         data = frappe.get_all(
#             "Address",
#             filters={"link_doctype": "Customer", "link_name": customer},
#             fields=[
#                 "name as address_id",
#                 "address_line1",
#                 "address_line2",
#                 "city",
#                 "state",
#                 "country",
#                 "pincode"
#             ]
#         )
#     except:
#         data = []

#     return api_response(True, "Address list fetched", data)

# pagination update 29/11
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_address(customer=None, page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not customer:
        return api_response(False, "customer is required")

    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page = 1
        page_size = 20

    start = (page - 1) * page_size

    try:
        # Dynamic Link join — safest ERPNext way
        data = frappe.db.get_list(
            "Address",
            fields=[
                "name as address_id",
                "address_line1",
                "address_line2",
                "city",
                "state",
                "country",
                "pincode"
            ],
            filters={
                "dynamic_links": {
                    "link_doctype": "Customer",
                    "link_name": customer
                }
            },
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        total = frappe.db.count(
            "Address",
            filters={
                "dynamic_links": {
                    "link_doctype": "Customer",
                    "link_name": customer
                }
            }
        )

    except Exception as e:
        # NEVER CRASH — always safe fallback
        return api_response(True, "Address list fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

    total_pages = (total + page_size - 1) // page_size

    return api_response(True, "Address list fetched", {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": data
    })

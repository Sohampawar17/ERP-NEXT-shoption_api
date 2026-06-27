# # import frappe
# # from shoption_api.erp_api.common import api_auth, require_post, api_response

# # @frappe.whitelist(allow_guest=True)
# # def get_categories(search=None):
# #     api_auth()
# #     require_post()
# #     frappe.set_user("Administrator")
    
# #     filters = {"is_group": 1}

# #     field_exists = "item_group_name" in [
# #         df.fieldname for df in frappe.get_meta("Item Group").fields
# #     ]

# #     if search and field_exists:
# #         filters["item_group_name"] = ["like", f"%{search}%"]

# #     try:
# #         data = frappe.get_list(
# #             "Item Group",
# #             filters=filters,
# #             fields=[
# #                 "name as category_id",
# #                 "item_group_name as category_name"
# #             ] if field_exists else ["name as category_id"]
# #         )
# #     except:
# #         data = []

# #     return api_response(True, "Category list fetched", data)

# # Pagination update 29/11
# # import frappe
# # from shoption_api.erp_api.common import api_auth, require_post, api_response

# # @frappe.whitelist(allow_guest=True)
# # def get_categories(search=None, page=1, page_size=20):
# #     api_auth()
# #     require_post()
# #     frappe.set_user("Administrator")

# #     # safe convert
# #     try:
# #         page = int(page)
# #         page_size = int(page_size)
# #     except:
# #         page = 1
# #         page_size = 20

# #     filters = {"is_group": 1}

# #     # check field existence
# #     meta = frappe.get_meta("Item Group")
# #     field_exists = "item_group_name" in [df.fieldname for df in meta.fields]

# #     if search and field_exists:
# #         filters["item_group_name"] = ["like", f"%{search}%"]

# #     start = (page - 1) * page_size

# #     try:
# #         data = frappe.get_list(
# #             "Item Group",
# #             filters=filters,
# #             fields=(
# #                 ["name as category_id", "item_group_name as category_name"]
# #                 if field_exists else
# #                 ["name as category_id"]
# #             ),
# #             limit_start=start,
# #             limit_page_length=page_size,
# #             order_by="creation desc"
# #         )

# #         total = frappe.db.count("Item Group", filters)
# #         total_pages = (total + page_size - 1) // page_size

# #         response = {
# #             "total": total,
# #             "page": page,
# #             "page_size": page_size,
# #             "total_pages": total_pages,
# #             "data": data
# #         }

# #         return api_response(True, "Category list fetched", response)

# #     except Exception:
# #         return api_response(True, "Category list fetched", {
# #             "total": 0,
# #             "page": page,
# #             "page_size": page_size,
# #             "total_pages": 0,
# #             "data": []
# #         })

# # updated id image 01/12
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_categories(search=None, page=1, page_size=20):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page = 1
#         page_size = 20

#     meta = frappe.get_meta("Item Group")
#     fields_available = {df.fieldname for df in meta.fields}

#     name_exists = "item_group_name" in fields_available
#     custom_id_exists = "custom_category_id" in fields_available
#     custom_image_exists = "custom_image_path" in fields_available

#     filters = {"is_group": 1}

#     if search and name_exists:
#         filters["item_group_name"] = ["like", f"%{search}%"]

#     start = (page - 1) * page_size

#     fields = ["name as category_id"]
#     if name_exists: fields.append("item_group_name as category_name")
#     if custom_id_exists: fields.append("custom_category_id")
#     if custom_image_exists: fields.append("custom_image_path")

#     try:
#         data = frappe.get_list(
#             "Item Group",
#             filters=filters,
#             fields=fields,
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         total = frappe.db.count("Item Group", filters)
#         total_pages = (total + page_size - 1) // page_size

#         return api_response(True, "Category list fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": data
#         })

#     except:
#         return api_response(True, "Category list fetched", {
#             "total": 0,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": 0,
#             "data": []
#         })

# working get categoriesz
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_categories(search=None, page=1, page_size=20):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page = 1
#         page_size = 20

#     meta = frappe.get_meta("Item Group")
#     fields_available = {df.fieldname for df in meta.fields}

#     name_exists = "item_group_name" in fields_available
#     custom_id_exists = "custom_category_id" in fields_available
#     custom_image_exists = "custom_image_path" in fields_available

#     # FIX: Fetch actual categories (is_group = 0)
#     filters = {"is_group": 0}

#     if search and name_exists:
#         filters["item_group_name"] = ["like", f"%{search}%"]
#     # # 09/12 improved search 
#     # if search and name_exists:
#     #     patterns = [
#     #         f"%{search}%",          # direct
#     #         f"%{search[::-1]}%",    # reversed (gbru → urbg)
#     #         f"%{search[:2]}%",      # first 2 chars
#     #         f"%{search[:3]}%",      # first 3 chars
#     #     ]

#     #     filter_list = [["Item Group", "is_group", "=", 0]]

#     #     for i, p in enumerate(patterns):
#     #         operator = "or" if i > 0 else None
#     #         condition = ["Item Group", "item_group_name", "like", p]
#     #         if operator:
#     #             condition.append(operator)
#     #         filter_list.append(condition)

#     # else:
#     #     filter_list = {"is_group": 0}

#     start = (page - 1) * page_size

#     fields = ["name as category_id"]
#     if name_exists: fields.append("item_group_name as category_name")
#     if custom_id_exists: fields.append("custom_category_id")
#     if custom_image_exists: fields.append("custom_image_path")

#     try:
#         data = frappe.get_list(
#             "Item Group",
#             filters=filters,
#             fields=fields,
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         total = frappe.db.count("Item Group", filters)
#         total_pages = (total + page_size - 1) // page_size

#         return api_response(True, "Category list fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": data
#         })

#     except:
#         return api_response(True, "Category list fetched", {
#             "total": 0,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": 0,
#             "data": []
#         })

# search priority update 09/12
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_categories(search=None, page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # Pagination safety
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page = 1
        page_size = 20

    start = (page - 1) * page_size

    # Meta checks
    meta = frappe.get_meta("Item Group")
    fields_available = {df.fieldname for df in meta.fields}

    name_exists = "item_group_name" in fields_available
    custom_id_exists = "custom_category_id" in fields_available
    custom_image_exists = "custom_image_path" in fields_available

    # Return fields
    fields = ["name as category_id"]
    if name_exists:
        fields.append("item_group_name as category_name")
    if custom_id_exists:
        fields.append("custom_category_id")
    if custom_image_exists:
        fields.append("custom_image_path")

    # -------------------------------------------
    # 1️⃣ EXACT MATCH (first priority)
    # -------------------------------------------

    if search and name_exists:
        exact = frappe.get_list(
            "Item Group",
            filters={"is_group": 0, "item_group_name": search,"custom_disabled": 0},
            fields=fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        if exact:
            return api_response(True, "Category list fetched", {
                "total": 1,
                "page": page,
                "page_size": page_size,
                "total_pages": 1,
                "data": exact
            })

    # -------------------------------------------
    # 2️⃣ SIMPLE LIKE SEARCH (same as ERPNext filters)
    # -------------------------------------------

    if search and name_exists:
        filters = [
            ["Item Group", "custom_disabled", "=", 0],
            ["Item Group", "is_group", "=", 0],
            ["Item Group", "item_group_name", "like", f"%{search}%"]
        ]
    else:
        filters = {"is_group": 0, "custom_disabled": 0}

    # Fetch data
    data = frappe.get_list(
        "Item Group",
        filters=filters,
        fields=fields,
        limit_start=start,
        limit_page_length=page_size,
        order_by="creation desc"
    )

    # Total count
    total = len(data)
    total_pages = (total + page_size - 1) // page_size

    return api_response(True, "Category list fetched", {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": data
    })

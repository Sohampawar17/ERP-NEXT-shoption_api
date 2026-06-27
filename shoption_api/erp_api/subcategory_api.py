# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_subcategories(category=None, search=None):
#     api_auth()
#     require_post()

#     frappe.set_user("Administrator")

#     if not category:
#         return api_response(False, "category is required")

#     meta = frappe.get_meta("Item Group")
#     name_exists = "item_group_name" in [df.fieldname for df in meta.fields]

#     filters = {"parent_item_group": category, "is_group": 0}

#     if search and name_exists:
#         filters["item_group_name"] = ["like", f"%{search}%"]

#     try:
#         data = frappe.get_list(
#             "Item Group",
#             filters=filters,
#             fields=[
#                 "name as subcategory_id",
#                 "item_group_name as subcategory_name"
#             ] if name_exists else ["name as subcategory_id"]
#         )
#     except:
#         data = []

#     return api_response(True, "Subcategory list fetched", data)

# Pagination update 29/11

# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_subcategories(category=None, search=None, page=1, page_size=20):
#     api_auth()
#     require_post()

#     frappe.set_user("Administrator")

#     if not category:
#         return api_response(False, "category is required")

#     # safe parse page values
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page = 1
#         page_size = 20

#     meta = frappe.get_meta("Item Group")
#     name_exists = "item_group_name" in [df.fieldname for df in meta.fields]

#     filters = {"parent_item_group": category, "is_group": 0}

#     if search and name_exists:
#         filters["item_group_name"] = ["like", f"%{search}%"]

#     start = (page - 1) * page_size

#     try:
#         data = frappe.get_list(
#             "Item Group",
#             filters=filters,
#             fields=[
#                 "name as subcategory_id",
#                 "item_group_name as subcategory_name"
#             ] if name_exists else ["name as subcategory_id"],
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         total = frappe.db.count("Item Group", filters)
#         total_pages = (total + page_size - 1) // page_size

#         response = {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": data
#         }

#         return api_response(True, "Subcategory list fetched", response)

#     except Exception:
#         return api_response(True, "Subcategory list fetched", {
#             "total": 0,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": 0,
#             "data": []
#         })

# updated id image 01/12
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_subcategories(category=None, search=None, page=1, page_size=20):
#     api_auth()
#     require_post()

#     frappe.set_user("Administrator")

#     if not category:
#         return api_response(False, "category is required")

#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page = 1
#         page_size = 20

#     meta = frappe.get_meta("Item Group")
#     fields_available = {df.fieldname for df in meta.fields}

#     name_exists = "item_group_name" in fields_available
#     subcat_id_exists = "sub_cat_id" in fields_available
#     image_path_exists = "image_path" in fields_available

#     filters = {"parent_item_group": category, "is_group": 0}

#     if search and name_exists:
#         filters["item_group_name"] = ["like", f"%{search}%"]

#     start = (page - 1) * page_size

#     fields = ["name as subcategory_id"]
#     if name_exists: fields.append("item_group_name as subcategory_name")
#     if subcat_id_exists: fields.append("sub_cat_id")
#     if image_path_exists: fields.append("image_path")

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

#         return api_response(True, "Subcategory list fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": data
#         })

#     except:
#         return api_response(True, "Subcategory list fetched", {
#             "total": 0,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": 0,
#             "data": []
#         })
        

# # @frappe.whitelist(allow_guest=True)
# # def get_brands_by_subcategory(subcategory_id=None):
# #     from shoption_api.erp_api.common import api_auth, require_post, api_response

# #     api_auth()
# #     require_post()
# #     frappe.set_user("Administrator")

# #     if not subcategory_id:
# #         return api_response(False, "subcategory_id is required")

# #     # STEP 1 → Get subcategory doc
# #     try:
# #         subcat = frappe.get_doc("Sub Categoury", subcategory_id)
# #     except:
# #         return api_response(False, "Invalid subcategory_id")

# #     # STEP 2 → Find category of this subcategory
# #     category_name = subcat.categoury
# #     if not category_name:
# #         return api_response(True, "Brands fetched", [])

# #     # STEP 3 → Find brands where this category is mapped (custom_brand_category child table)
# #     brands = []

# #     brand_docs = frappe.get_all(
# #         "Brand",
# #         fields=["name", "brand", "custom_brand_id", "custom_image_path"]
# #     )

# #     for b in brand_docs:
# #         try:
# #             brand_doc = frappe.get_doc("Brand", b.name)

# #             if not hasattr(brand_doc, "custom_brand_category"):
# #                 continue

# #             # Check child table rows
# #             for row in brand_doc.custom_brand_category:
# #                 if row.category == category_name:
# #                     brands.append({
# #                         "brand_id": b.name,
# #                         "brand_name": b.get("brand"),
# #                         "custom_brand_id": b.get("custom_brand_id"),
# #                         "image": b.get("custom_image_path") or "",
# #                         "category": category_name
# #                     })
# #                     break
# #         except:
# #             pass  # ignore silent errors

# #     return api_response(True, "Brands fetched", brands)

# 06/12
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_subcategories(category=None, search=None, page=1, page_size=20):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     if not category:
#         return api_response(False, "category is required")

#     # Safe conversion
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page = 1
#         page_size = 20

#     filters = {"categoury": category}

#     if search:
#         filters["sub_categoury"] = ["like", f"%{search}%"]

#     start = (page - 1) * page_size

#     try:
#         data = frappe.get_list(
#             "Sub Categoury",
#             filters=filters,
#             fields=[
#                 "name as subcategory_id",
#                 "sub_categoury as subcategory_name",
#                 "sub_cat_id",
#                 "image_path"
#             ],
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         total = frappe.db.count("Sub Categoury", filters)
#         total_pages = (total + page_size - 1) // page_size

#         return api_response(True, "Subcategory list fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": data
#         })

#     except:
#         return api_response(True, "Subcategory list fetched", {
#             "total": 0,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": 0,
#             "data": []
#         })

import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response


@frappe.whitelist(allow_guest=True)
def get_subcategories(category=None, search=None, page=None, page_size=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not category:
        return api_response(False, "category is required")

    # Safe conversion
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    start = (page - 1) * page_size

    base_filter = {"categoury": category}

    # ------------------------------------------------------
    # 1️⃣ EXACT MATCH FIRST (same as category/brand logic)
    # ------------------------------------------------------
    exact_rows = []

    if search:
        exact_filters = {
            "categoury": category,
            "sub_categoury": search,
            "disabled": 0
        }

        exact_rows = frappe.get_list(
            "Sub Categoury",
            filters=exact_filters,
            fields=[
                "name as subcategory_id",
                "sub_categoury as subcategory_name",
                "sub_cat_id",
                "image_path"
            ],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

    # If exact match found → return only exact match
    if exact_rows:
        return api_response(True, "Subcategory list fetched", {
            "total": len(exact_rows),
            "page": page,
            "page_size": page_size,
            "total_pages": 1,
            "data": exact_rows
        })

    # ------------------------------------------------------
    # 2️⃣ NO EXACT → FALLBACK TO LIKE SEARCH (ERPNext style)
    # ------------------------------------------------------
    filters = {"categoury": category, "disabled": 0}

    if search:
        filters["sub_categoury"] = ["like", f"%{search}%"]

    # ------------------------------------------------------
    # Fetch LIKE results
    # ------------------------------------------------------
    try:
        data = frappe.get_list(
            "Sub Categoury",
            filters=filters,
            fields=[
                "name as subcategory_id",
                "sub_categoury as subcategory_name",
                "sub_cat_id",
                "image_path"
            ],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        total = frappe.db.count("Sub Categoury", filters)
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Subcategory list fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Subcategories API Error")
        return api_response(True, "Subcategory list fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })


@frappe.whitelist(allow_guest=True)
def get_brand_subcategories(brand_id=None, page=1, page_size=20):
    from shoption_api.erp_api.common import api_auth, require_post, api_response

    api_auth()
    require_post()

    if not brand_id:
        return api_response(False, "brand_id is required")

    try:
        brand_doc = frappe.get_doc("Brand", brand_id)
    except frappe.DoesNotExistError:
        return api_response(False, "Invalid brand_id")

    # Safe pagination
    try:
        page = max(int(page), 1)
        page_size = max(int(page_size), 1)
    except:
        page, page_size = 1, 20

    categories = [
        row.category for row in getattr(brand_doc, "custom_brand_category", [])
        if row.category
    ]

    if not categories:
        return api_response(True, "Subcategories fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

    # ---------------------------------------
    # STEP 1 → Fetch ALL subcategories at once
    # ---------------------------------------
    subcategories = frappe.get_all(
        "Sub Categoury",
        filters={
            "categoury": ["in", categories],
            "disabled": 0
        },
        fields=["name", "sub_categoury", "image_path", "categoury"],
        order_by="sub_categoury asc"
    )

    if not subcategories:
        return api_response(True, "Subcategories fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

    subcat_names = [s.name for s in subcategories]

    # ---------------------------------------
    # STEP 2 → Get ONLY subcategories having items
    # ---------------------------------------
    valid_subcats = frappe.db.sql("""
    SELECT DISTINCT custom_sub_category
    FROM `tabItem`
    WHERE brand = %(brand)s
    AND item_group IN %(categories)s
    AND custom_sub_category IN %(subcats)s
    AND disabled = 0
    ORDER BY custom_sub_category ASC
    """, {
        "brand": brand_id,
        "categories": tuple(categories),
        "subcats": tuple(subcat_names)
    }, as_dict=True)
    valid_set = {row.custom_sub_category for row in valid_subcats}

    # ---------------------------------------
    # STEP 3 → Filter in Python (fast)
    # ---------------------------------------
    all_subcats = [
        {
            "sub_cat_id": sc.name,
            "subcategory_name": sc.sub_categoury,
            "image": sc.image_path or "",
            "category": sc.categoury
        }
        for sc in subcategories
        if sc.name in valid_set
    ]

    # ---------------------------------------
    # PAGINATION
    # ---------------------------------------
    total = len(all_subcats)
    start = (page - 1) * page_size
    end = start + page_size

    return api_response(True, "Subcategories fetched", {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": all_subcats[start:end]
    })
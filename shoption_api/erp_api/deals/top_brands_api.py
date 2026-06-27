import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_top_brands(page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    try:
        page, page_size = int(page), int(page_size)
    except:
        page, page_size = 1, 20

    meta = frappe.get_meta("Top Brands")
    fields_available = {df.fieldname for df in meta.fields}

    safe_fields = []
    for f in ["brand_id", "brand_name", "image"]:
        if f in fields_available:
            safe_fields.append(f)

    start = (page - 1) * page_size

    try:
        data = frappe.get_list(
            "Top Brands",
            fields=safe_fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        total = frappe.db.count("Top Brands")
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Top Brands fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data
        })

    except:
        return api_response(True, "Top Brands fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

# # updated response format for brand
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response


# @frappe.whitelist(allow_guest=True)
# def get_top_brands(page=1, page_size=20):

#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     # -----------------------------
#     # Safe pagination conversion
#     # -----------------------------
#     try:
#         page, page_size = int(page), int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     try:
#         # -----------------------------
#         # Fetch Top Brands rows
#         # -----------------------------
#         top_rows = frappe.get_list(
#             "Top Brands",
#             fields=["brand_id", "brand_name", "image"],
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         response_data = []

#         # -----------------------------
#         # Loop and enrich with Brand Master data
#         # -----------------------------
#         for row in top_rows:

#             brand_id = row.get("brand_id")

#             # Fetch extra information from Brand doctype
#             brand_info = frappe.get_all(
#                 "Brand",
#                 filters={"name": brand_id},
#                 fields=["custom_brand_id", "custom_image_path"],
#                 limit=1
#             )

#             custom_brand_id = None
#             custom_image = None

#             if brand_info:
#                 custom_brand_id = brand_info[0].get("custom_brand_id")
#                 # Prefer TopBrand image → fallback to brand master image
#                 custom_image = row.get("image") or brand_info[0].get("custom_image_path")

#             # Final cleaned object
#             response_data.append({
#                 "brand_id": brand_id,
#                 "brand_name": row.get("brand_name"),
#                 "custom_brand_id": custom_brand_id,
#                 "image": custom_image
#             })

#         total = frappe.db.count("Top Brands")
#         total_pages = (total + page_size - 1) // page_size

#         return api_response(True, "Top Brands fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": response_data
#         })

#     except Exception as e:
#         return api_response(False, f"Error: {str(e)}")

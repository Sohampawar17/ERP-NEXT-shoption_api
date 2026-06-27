import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_trending_brands(page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # safe convert
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    meta = frappe.get_meta("Trending brands")
    fields_available = {df.fieldname for df in meta.fields}

    # allowed fields
    safe_fields = []
    for f in ["brand_id", "brand_name", "image"]:
        if f in fields_available:
            safe_fields.append(f)

    start = (page - 1) * page_size

    try:
        data = frappe.get_list(
            "Trending brands",
            fields=safe_fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        total = frappe.db.count("Trending brands")
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Trending brands fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data
        })

    except:
        return api_response(True, "Trending brands fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

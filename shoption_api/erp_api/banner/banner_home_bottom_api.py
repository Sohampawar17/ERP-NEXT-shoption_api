import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_home_banner_bottom(page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # Safe pagination
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    doctype = "Home Banner Bottom"

    meta = frappe.get_meta(doctype)
    image_field_exists = "image_path" in [df.fieldname for df in meta.fields]

    safe_fields = ["name"]
    if image_field_exists:
        safe_fields.append("image_path")

    start = (page - 1) * page_size

    try:
        data = frappe.get_list(
            doctype,
            fields=safe_fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        total = frappe.db.count(doctype)
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Home Banner Bottom fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data
        })

    except:
        return api_response(True, "Home Banner Bottom fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

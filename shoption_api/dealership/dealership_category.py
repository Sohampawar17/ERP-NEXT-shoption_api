import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_dealership_categories(page=1, page_size=20):
    api_auth()
    require_post()

    frappe.set_user("Administrator")

    # pagination safe conversion
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    start = (page - 1) * page_size

    try:
        # Fetch records
        data = frappe.get_list(
            "Dealership Category Master",
            fields=["dealership_category_name"],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        total = frappe.db.count("Dealership Category Master")
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Dealership categories fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data
        })

    except Exception as e:
        return api_response(False, f"Error: {str(e)}")

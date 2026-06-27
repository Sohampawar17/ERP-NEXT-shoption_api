import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def check_status(form_id=None):
    if not form_id:
        return api_response(False, "form_id is required")

    if not frappe.db.exists("Delear Registration", form_id):
        return api_response(False, "Invalid form_id")

    status = frappe.db.get_value("Delear Registration", form_id, "is_completed")

    return api_response(True, "Status fetched", {
        "form_id": form_id,
        "is_completed": bool(status)
    })

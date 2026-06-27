import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def create_demand_special_rate(item_code=None, quantity=None, rate_per_unit=None, expected_rate=None,
                               expected_purchase_date=None, user_id=None):

    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # accept both user_id and userId
    # user_id = frappe.form_dict.get("user_id") or frappe.form_dict.get("userId") or user_id

    if not user_id:
        return api_response(False, "user_id is required")

    try:
        doc = frappe.get_doc({
            "item_code": item_code,
            "doctype": "Demand Special Rate",
            "quantity": quantity,
            "rate_per_unit": rate_per_unit,
            "expected_rate": expected_rate,
            "expected_purchase_date": expected_purchase_date,
            "user_id": user_id
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return api_response(True, "Demand Special Rate created successfully", {
            "docname": doc.name,
            "item_code": doc.item_code,
            "item_name": doc.item_name
        })

    except Exception as e:
        return api_response(False, f"Error creating Demand Special Rate: {str(e)}")

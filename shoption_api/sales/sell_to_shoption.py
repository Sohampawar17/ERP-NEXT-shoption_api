import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def create_sell_to_shoption(item_code=None, price_rate=None, quantity_available=None, dispatch_location=None,
                            brand_discount=None, user_id=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # Validate required fields
    if not user_id:
        return api_response(False, "user_id is required")

    try:
        doc = frappe.get_doc({
            "doctype": "Sell This to Shoption",
            "item_code": item_code,
            "price_rate": price_rate,
            "quantity_available": quantity_available,
            "dispatch_location": dispatch_location,
            "brand_discount": brand_discount,
            "user_id": user_id  # Auto-fill customer details via hooks
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return api_response(True, "Sell to Shoption created successfully", {
            "docname": doc.name,
            "item_code" : doc.item_code,
            "item_name" : doc.item_name
        })

    except Exception as e:
        return api_response(False, f"Error creating Sell to Shoption: {str(e)}")

import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from frappe.utils import get_url

@frappe.whitelist(allow_guest=True)
def get_dealer_registration_details(id=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # -----------------------------
    # VALIDATION
    # -----------------------------
    if not id:
        return api_response(False, "id is required")

    if not frappe.db.exists("Delear Registration", id):
        return api_response(False, "Dealer Registration not found")

    # -----------------------------
    # FETCH DOCUMENT
    # -----------------------------
    doc = frappe.get_doc("Delear Registration", id)

    # -----------------------------
    # BUILD RESPONSE (FORM LIKE)
    # -----------------------------
    data = {
        "docname": doc.name,
        "from_document": doc.from_document,
        "mobile_number": doc.mobile_number,

        # -----------------------------
        # SHOP DETAILS
        # -----------------------------
        "shop_details": {
            "shop_name": doc.shop_name,
            "party_name": doc.party_name,
            "email_id": doc.email_id
        },

        # -----------------------------
        # ADDRESS
        # -----------------------------
        "address": {
            "country": doc.country,
            "state": doc.state,
            "district": doc.district,
            "tahshil": doc.tahshil,
            "marketplace": doc.marketplace,
            "pincode": doc.pincode,
            "address_line_1": doc.address_line_1,
            "address_line_2": doc.address_line_2
        },

        # -----------------------------
        # GST
        # -----------------------------
        "gst": {
            "gst_no": doc.gst_no,
            "gst_certificate": get_url(doc.gst_certificate) if doc.gst_certificate else None
        },

        # -----------------------------
        # ATTACHMENTS
        # -----------------------------
        "documents": {
            # "shop_front_photo": doc.shop_front_photo,
            "shop_front_photo": get_url(doc.shop_front_photo) if doc.shop_front_photo else None,
            # "visiting_card": doc.visiting_card,
            "visiting_card": get_url(doc.visiting_card) if doc.visiting_card else None,
            # "passbook_or_checkbook": doc.passbook_or_checkbook
            "passbook_or_checkbook": get_url(doc.passbook_or_checkbook) if doc.passbook_or_checkbook else None
        },

        # -----------------------------
        # META
        # -----------------------------
        "status": doc.docstatus,
        "created_on": doc.creation,
        "last_updated_on": doc.modified
    }

    # -----------------------------
    # RESPONSE
    # -----------------------------
    return api_response(
        True,
        "Dealer registration details fetched successfully",
        data
    )

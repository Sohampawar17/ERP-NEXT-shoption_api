import random
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from frappe.exceptions import DuplicateEntryError

@frappe.whitelist(allow_guest=True)
def create_farmer_registration(
	from_document=None,
	first_name=None,
	email_id=None,
	country=None,
	state=None,
	district=None,
	tahshil=None,
	marketplace=None,
	pincode=None,
	address_line_1=None,
	address_line_2=None
):
    api_auth()
    require_post()

    # NOTE: Consider removing Administrator impersonation in production.
    frappe.set_user("Administrator")
    frappe.flags.ignore_throttling = True

    if not from_document:
        return api_response(False, "from_document (Lead ID) is required")

    # ---- GET EXISTING FARMER FORM ----
    existing = frappe.db.get_value("Farmer Registration", {"from_document": from_document}, "name")
    if not existing:
        return api_response(False, "No registration form found for this lead_id")

    doc = frappe.get_doc("Farmer Registration", existing)

    # ---- EMAIL LOGIC ----
    if email_id:
        email_id = str(email_id).strip()
    else:
        base = pincode or (first_name.lower().replace(" ", "") if first_name else str(random.randint(100000, 999999)))
        email_id = f"{base}@demo.com"

    # ---- UPDATE FIELDS ----
    if first_name:
        doc.first_name = first_name

    if email_id:
        doc.email_id = email_id

    doc.country = country
    doc.state = state
    doc.district = district
    doc.tahshil = tahshil
    doc.marketplace = marketplace
    doc.pincode = pincode
    doc.address_line_1 = address_line_1
    doc.address_line_2 = address_line_2

    
    try:
        frappe.flags.ignore_throttling = True

        # IMPORTANT: only one save (avoid double validations/permission checks)
        doc.save(ignore_permissions=True)
        frappe.db.commit()

    except DuplicateEntryError:
        frappe.db.rollback()
       
        return api_response(
            False,
            "Email already exists. Please use a different email address.",
            {"error_type": "DUPLICATE_EMAIL"},
        )

    except frappe.ValidationError as e:
        # Throttle sometimes comes as ValidationError
        if "Throttled" in str(e):
            
            try:
                doc.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e2:
                frappe.db.rollback()
                
                return api_response(
                    False,
                    "Throttled fallback save failed",
                    {"error_type": "THROTTLE_FALLBACK_FAILED"},
                )
        else:
            frappe.db.rollback()
            
            payload = {"error_type": "VALIDATION_ERROR"}
            payload["detail"] = str(e)
            return api_response(False, str(e), payload)

    except Exception as e:
        frappe.db.rollback()
       
        payload = {"error_type": "UNKNOWN_ERROR"}
        payload["detail"] = str(e)
        return api_response(False, "Something went wrong while saving Farmer Registration", payload)

    return api_response(True, "Farmer Registration updated successfully", {
        "name": doc.name,
        "email_used": email_id
    })

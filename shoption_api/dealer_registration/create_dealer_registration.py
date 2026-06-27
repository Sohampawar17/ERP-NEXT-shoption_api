# try 
# 05/12 – Final Stable Version
import frappe
from frappe.utils.file_manager import save_file
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def create_dealer_registration(
    from_document=None,
    shop_name=None,
    email_id=None,
    country=None,
    state=None,
    district=None,
    tahshil=None,
    marketplace=None,
    pincode=None,
    address_line_1=None,
    address_line_2=None,
    gst_no = None,
    gst_certificate=None,
    shop_front_photo=None,
    visiting_card=None,
    passbook_or_checkbook=None,
    gst_verified=None,
    mode=None
):
    api_auth()
    require_post()
    frappe.set_user("Administrator")
    
    frappe.flags.ignore_throttling = True

    if not from_document:
        return api_response(False, "from_document (Lead ID) is required")

    # ----------------------------------------------------
    # Fetch existing Dealer Registration (pre-created form)
    # ----------------------------------------------------
    existing = frappe.db.get_value("Delear Registration",
                                   {"from_document": from_document},
                                   "name")

    if not existing:
        return api_response(False, "No registration form found for this lead_id")

    doc = frappe.get_doc("Delear Registration", existing)

    # ----------------------------------------------------
    # Update ONLY if value provided
    # ----------------------------------------------------
    if shop_name: doc.shop_name = shop_name
    if email_id: doc.email_id = email_id
    if country: doc.country = country
    if state: doc.state = state
    if district: doc.district = district
    if tahshil: doc.tahshil = tahshil
    if marketplace: doc.marketplace = marketplace
    if pincode: doc.pincode = pincode
    if address_line_1: doc.address_line_1 = address_line_1
    if address_line_2: doc.address_line_2 = address_line_2
    if gst_no: doc.gst_no = gst_no
    if gst_verified is not None: doc.gst_verified = gst_verified
    if mode: doc.mode = mode


    def save_uploaded_file_formdata(fieldname):
        uploaded_file = frappe.request.files.get(fieldname)
        if uploaded_file:
            content = uploaded_file.read()
            saved = save_file(
                uploaded_file.filename,
                content,
                "Delear Registration",
                doc.name,
                # is_private=True
            )
            return saved.file_url   # correct for Attach field
        return None

    doc.gst_certificate = save_uploaded_file_formdata("gst_certificate") or doc.gst_certificate
    doc.shop_front_photo = save_uploaded_file_formdata("shop_front_photo") or doc.shop_front_photo
    doc.visiting_card = save_uploaded_file_formdata("visiting_card") or doc.visiting_card
    doc.passbook_or_checkbook = save_uploaded_file_formdata("passbook_or_checkbook") or doc.passbook_or_checkbook

    try:
        frappe.flags.ignore_throttling = True

        # IMPORTANT: only one save (avoid double validations/permission checks)
        doc.save(ignore_permissions=True)
        frappe.db.commit()

    except frappe.exceptions.ValidationError as e:
        # If the error is throttling → do NOT fail API
        if "Throttled" in str(e):
            frappe.log_error("User creation throttled but continuing", "Throttle Bypass")
            frappe.db.commit()   # ensure no partial data loss
        else:
            raise e  # any other error → let ERPNext handle

    return api_response(True, "Dealer Registration updated successfully", {
        "docname": doc.name,
        "shop_name": doc.shop_name,
        "email_id": doc.email_id,
        "country": doc.country,
        "state": doc.state,
        "district": doc.district,
        "tahshil": doc.tahshil,
        "marketplace": doc.marketplace,
        "pincode": doc.pincode,
        "address_line_1": doc.address_line_1,
        "address_line_2": doc.address_line_2,
        "gst_no": doc.gst_no,
        "gst_certificate": doc.gst_certificate,
        "shop_front_photo": doc.shop_front_photo,
        "visiting_card": doc.visiting_card,
        "passbook_or_checkbook": doc.passbook_or_checkbook,
        "gst_verified": doc.gst_verified,
        "mode": doc.mode
        
    })



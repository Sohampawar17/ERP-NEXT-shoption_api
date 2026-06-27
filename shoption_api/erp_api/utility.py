

def extract_last(value):
    if not value:
        return None
    return value.split("-")[0]

import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.app_utils import generate_key
from frappe.utils import get_url


@frappe.whitelist(allow_guest=True)
def get_user_details(mobile_no=None):
    api_auth()
    require_post()

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    # --------------------------------------------------
    # 1️⃣ Registration Form (Dealer / Farmer)
    # --------------------------------------------------
    form_id, shop_name = get_registration_form(mobile_no)

    # --------------------------------------------------
    # 2️⃣ Customer Lookup (Single Query)
    # --------------------------------------------------
    customer = frappe.db.get_value(
        "Customer",
        {"mobile_no": mobile_no},
        ["name", "customer_group", "customer_name", "custom_profile_image"],
        as_dict=True
    )

    # ==================================================
    # 3️⃣ ACTIVE USER FLOW
    # ==================================================
    if customer:

        portal_user = frappe.db.get_value(
            "Portal User",
            {"parent": customer.name},
            "user"
        )

        if portal_user:
            username = frappe.db.get_value("User", portal_user, "username")

            return api_response(True, "User details fetched", {
                "status": "ACTIVE",
                "customer_id": customer.name,
                "user_id": portal_user,
                "username": username,
                "shoption_customer_id": username,
                "role": customer.customer_group,
                "form_id": form_id,
                "shop_name": shop_name,
                "brand_ambassador": frappe.get_value("Brand Ambassador", {"customer": customer.name}, "name") or "",                
                "Customer_name": customer.customer_name if customer.customer_group =="Farmer"else shop_name,
                "address": get_customer_address(customer.name),
                "profile_image": get_full_url(customer.custom_profile_image),
                "key_details": generate_key(portal_user)
            })

    # ==================================================
    # 4️⃣ LEAD FLOW
    # ==================================================
    lead = frappe.db.get_value(
        "Lead",
        {"mobile_no": mobile_no},
        ["first_name", "mobile_no", "custom_profile_image", "type"],
        as_dict=True
    )

    if lead:
        return api_response(True, "Lead user fetched", {
            "status": "LEAD",
            "Customer_name": lead.first_name,
            "mobile_no": lead.mobile_no,
            "profile_image": get_full_url(lead.custom_profile_image),
            "customer_id": None,
            "user_id": None,
            "shoption_customer_id": None,
            "role": lead.type,
            "form_id": form_id,
            "shop_name": shop_name,
            "address": None,
            "key_details": None,
        })

    return api_response(False, "User not found")


# ======================================================
# 🔹 Helper: Registration Form (Optimized)
# ======================================================
def get_registration_form(mobile_no):
    dealer = frappe.db.get_value(
        "Delear Registration",
        {"mobile_number": mobile_no},
        ["name", "shop_name"],
        as_dict=True
    )

    if dealer:
        return dealer.name, dealer.shop_name

    farmer = frappe.db.get_value(
        "Farmer Registration",
        {"mobile_number": mobile_no},
        "name"
    )

    return (farmer, None) if farmer else (None, None)


# ======================================================
# 🔹 Helper: Address (Single Query + No Full Doc Load)
# ======================================================
def get_customer_address(customer_name):
    address_name = frappe.db.get_value(
        "Dynamic Link",
        {
            "link_doctype": "Customer",
            "link_name": customer_name,
            "parenttype": "Address"
        },
        "parent"
    )

    if not address_name:
        return None

    addr = frappe.db.get_value(
        "Address",
        address_name,
        [
            "address_line1",
            "address_line2",
            "city",
            "custom_tahshil",
            "custom_district",
            "state",
            "pincode",
            "country"
        ],
        as_dict=True
    )

    if not addr:
        return None

    parts = [
        addr.address_line1,
        addr.address_line2,
        extract_last(addr.city),
        extract_last(addr.custom_tahshil),
        extract_last(addr.custom_district),
        addr.state,
        addr.pincode,
        addr.country
    ]

    return ", ".join([str(p) for p in parts if p])


# ======================================================
# 🔹 Helper: Safe URL
# ======================================================
def get_full_url(file_path):
    return get_url(file_path) if file_path else None

@frappe.whitelist(allow_guest=True)
def get_user_details(mobile_no=None):
    api_auth()
    require_post()

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    # --------------------------------------------------
    # 1️⃣ Registration Form (Dealer / Farmer)
    # --------------------------------------------------
    form_id, shop_name = get_registration_form(mobile_no)

    # --------------------------------------------------
    # 2️⃣ Customer Lookup (Single Query)
    # --------------------------------------------------
    customer = frappe.db.get_value(
        "Customer",
        {"mobile_no": mobile_no},
        ["name", "customer_group", "customer_name", "custom_profile_image"],
        as_dict=True
    )

    # ==================================================
    # 3️⃣ ACTIVE USER FLOW
    # ==================================================
    if customer:

        portal_user = frappe.db.get_value(
            "Portal User",
            {"parent": customer.name},
            "user"
        )

        if portal_user:
            username = frappe.db.get_value("User", portal_user, "username")

            return api_response(True, "User details fetched", {
                "status": "ACTIVE",
                "customer_id": customer.name,
                "user_id": portal_user,
                "username": username,
                "shoption_customer_id": username,
                "role": customer.customer_group,
                "form_id": form_id,
                "shop_name": shop_name,
                "brand_ambassador": frappe.get_value("Brand Ambassador", {"customer": customer.name}, "name") or "",                
                "Customer_name": customer.customer_name if customer.customer_group =="Farmer"else shop_name,
                "address": get_customer_address(customer.name),
                "profile_image": get_full_url(customer.custom_profile_image),
                "key_details": generate_key(portal_user)
            })

    # ==================================================
    # 4️⃣ LEAD FLOW
    # ==================================================
    lead = frappe.db.get_value(
        "Lead",
        {"mobile_no": mobile_no},
        ["first_name", "mobile_no", "custom_profile_image", "type"],
        as_dict=True
    )

    if lead:
        return api_response(True, "Lead user fetched", {
            "status": "LEAD",
            "Customer_name": lead.first_name,
            "mobile_no": lead.mobile_no,
            "profile_image": get_full_url(lead.custom_profile_image),
            "customer_id": None,
            "user_id": None,
            "shoption_customer_id": None,
            "role": lead.type,
            "form_id": form_id,
            "shop_name": shop_name,
            "address": None,
            "key_details": None,
        })

    return api_response(False, "User not found")


# ======================================================
# 🔹 Helper: Registration Form (Optimized)
# ======================================================
def get_registration_form(mobile_no):
    dealer = frappe.db.get_value(
        "Delear Registration",
        {"mobile_number": mobile_no},
        ["name", "shop_name"],
        as_dict=True
    )

    if dealer:
        return dealer.name, dealer.shop_name

    farmer = frappe.db.get_value(
        "Farmer Registration",
        {"mobile_number": mobile_no},
        "name"
    )

    return (farmer, None) if farmer else (None, None)


# ======================================================
# 🔹 Helper: Address (Single Query + No Full Doc Load)
# ======================================================
def get_customer_address(customer_name):

    address_name = frappe.db.get_value(
        "Dynamic Link",
        {
            "link_doctype": "Customer",
            "link_name": customer_name,
            "parenttype": "Address"
        },
        "parent"
    )

    if not address_name:
        return None

    addr = frappe.db.get_value(
        "Address",
        address_name,
        [
            "address_line1",
            "address_line2",
            "city",
            "custom_tahshil",
            "custom_district",
            "state",
            "pincode",
            "country"
        ],
        as_dict=True
    )

    if not addr:
        return None

    # 🔥 Fetch linked document names
    city_name = frappe.db.get_value("Marketplace", addr.city, "marketplace_name") if addr.city else None
    tahshil_name = frappe.db.get_value("Tahshil", addr.custom_tahshil, "tahshil") if addr.custom_tahshil else None
    district_name = frappe.db.get_value("District", addr.custom_district, "district_name") if addr.custom_district else None

    parts = [
        addr.address_line1,
        addr.address_line2,
        city_name,
        tahshil_name,
        district_name,
        addr.state,
        addr.pincode,
        addr.country
    ]

    return ", ".join([str(p) for p in parts if p])


# ======================================================
# 🔹 Helper: Safe URL
# ======================================================
def get_full_url(file_path):
    return get_url(file_path) if file_path else None


from frappe.utils.file_manager import save_file
from frappe.utils import get_url
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response


@frappe.whitelist(allow_guest=True)
def upload_image(mobile_no=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # -----------------------------
    # VALIDATION
    # -----------------------------
    if not mobile_no:
        return api_response(False, "mobile_no is required")

    uploaded_file = frappe.request.files.get("file")
    if not uploaded_file:
        return api_response(False, "Profile image file is required")

    # =====================================================
    # STEP 1: FIND CUSTOMER (ONLY FOR USER CHECK)
    # =====================================================
    customer = frappe.get_all(
        "Customer",
        filters={"mobile_no": mobile_no},
        fields=["name"],
        limit=1
    )

    portal_user = None
    customer_doc = None

    if customer:
        customer_doc = frappe.get_doc("Customer", customer[0].name)

        if customer_doc.portal_users:
            portal_user = customer_doc.portal_users[0].user

    # =====================================================
    # ❌ USER NOT FOUND → UPLOAD TO LEAD
    # =====================================================
    if not portal_user:
        lead = frappe.get_all(
            "Lead",
            filters={"mobile_no": mobile_no},
            fields=["name"],
            limit=1
        )

        if not lead:
            return api_response(False, "User not found")

        lead_doc = frappe.get_doc("Lead", lead[0].name)

        content = uploaded_file.read()

        saved = save_file(
            uploaded_file.filename,
            content,
            "Lead",
            lead_doc.name,
            is_private=0
        )

        if not saved or not saved.file_url:
            return api_response(False, "Failed to upload profile image")

        lead_doc.custom_profile_image = saved.file_url
        lead_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return api_response(
            True,
            "Lead profile image updated successfully",
            {
                "source": "Lead",
                "reference": lead_doc.name,
                "profile_image": saved.file_url,
                "profile_image_url": get_url(saved.file_url)
            }
        )

    # =====================================================
    # ✅ USER EXISTS → UPLOAD TO CUSTOMER
    # =====================================================
    content = uploaded_file.read()

    saved = save_file(
        uploaded_file.filename,
        content,
        "Customer",
        customer_doc.name,
        is_private=0
    )

    if not saved or not saved.file_url:
        return api_response(False, "Failed to upload profile image")

    if saved.file_url:
        customer_doc.custom_profile_image = None
        customer_doc.custom_profile_image = saved.file_url
        
    customer_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return api_response(
        True,
        "Customer profile image updated successfully",
        {
            "source": "Customer",
            "reference": customer_doc.name,
            "profile_image": saved.file_url,
            "profile_image_url": get_url(saved.file_url)
        }
    )


import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_user_onboarding_status(mobile_no=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # ---------------------------------
#     # CUSTOMER (ACTIVE USER)
#     # ---------------------------------
#     # customer = frappe.db.get_value(
#     #     "Customer",
#     #     {"mobile_no": mobile_no},
#     #     "name"
#     # )

#     # if customer:
#     #     return api_response(True, "User status fetched successfully", {
#     #         "status": "ACTIVE",
#     #         "source": "Customer",
#     #         "reference": customer
#     #     })
    
    
#     # ---------------------------------
#     # CUSTOMER
#     # ---------------------------------
#     customer = frappe.get_all(
#         "Customer",
#         filters={"mobile_no": mobile_no},
#         fields=["name", "customer_group"],
#         limit=1
#     )
#     form="Farmer Registration" if customer and customer[0].customer_group=="Farmer" else "Delear Registration"
#     is_completed = frappe.db.get_value(form, {"mobile_number": mobile_no},[ "docstatus","is_completed"],as_dict=True) if customer else None
    
#     if customer and is_completed and is_completed.docstatus==1 and is_completed.is_completed==1:
#         customer = customer[0]
#         customer_doc = frappe.get_doc("Customer", customer.name)

#         # ---------------------------------
#         # PORTAL USER (linked with Customer)
#         # ---------------------------------
#         portal_user = None

#         if customer_doc.portal_users:
#             portal_user = customer_doc.portal_users[0].user

#         if portal_user:
#             return api_response(True, "User status fetched successfully", {
#                 "status": "ACTIVE",
#                 "source": "Customer → User",
#                 "reference": {
#                     "customer": customer.name,
#                     "user": portal_user,
#                     "role": customer.customer_group or "Unknown"
#                 }
#             })


#     # ---------------------------------
#     # FARMER REGISTRATION
#     # field = mobile_number
#     # ---------------------------------
#     farmer_registration = frappe.db.get_value(
#         "Farmer Registration",
#         {"mobile_number": mobile_no},
#         "name"
#     )

#     if farmer_registration:
#         return api_response(True, "User status fetched successfully", {
#             "status": "PENDING_FOR_APPROVAL",
#             "source": "Farmer Registration",
#             "reference": farmer_registration
#         })

#     # ---------------------------------
#     # 3️⃣ DEALER REGISTRATION
#     # field = mobile_number
#     # ---------------------------------
#     dealer_registration = frappe.db.get_value(
#         "Delear Registration",
#         {"mobile_number": mobile_no},
#         "name"
#     )

#     if dealer_registration:
#         return api_response(True, "User status fetched successfully", {
#             "status": "PENDING_FOR_APPROVAL",
#             "source": "Delear Registration",
#             "reference": dealer_registration
#         })

#     # ---------------------------------
#     # 4️⃣ LEAD
#     # field = mobile_no
#     # ---------------------------------
#     lead = frappe.db.get_value(
#         "Lead",
#         {"mobile_no": mobile_no},
#         "name"
#     )

#     if lead:
#         return api_response(True, "User status fetched successfully", {
#             "status": "LEAD",
#             "source": "Lead",
#             "reference": lead
#         })

#     # ---------------------------------
#     # 5️⃣ NEW USER
#     # ---------------------------------
#     return api_response(True, "User status fetched successfully", {
#         "status": "NEW_USER",
#         "source": None,
#         "reference": None
#     })

@frappe.whitelist(allow_guest=True)
def get_user_onboarding_status(mobile_no=None):
    api_auth()
    require_post()

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    # ---------------------------------
    # 1️⃣ CUSTOMER
    # ---------------------------------
    customer = frappe.get_all(
        "Customer",
        filters={"mobile_no": mobile_no},
        fields=["name", "customer_group"],
        limit=1
    )

    if customer:
        customer = customer[0]

        form = "Farmer Registration" if customer.customer_group == "Farmer" else "Delear Registration"

        reg_doc = frappe.db.get_value(
            form,
            {"mobile_number": mobile_no},
            ["name", "docstatus", "is_completed"],
            as_dict=True
        )

        if reg_doc and reg_doc.docstatus == 1 and reg_doc.is_completed == 1:

            customer_doc = frappe.get_doc("Customer", customer.name)

            portal_user = None
            if customer_doc.portal_users:
                portal_user = customer_doc.portal_users[0].user

            if portal_user:
                return api_response(True, "User status fetched successfully", {
                    "status": "ACTIVE",
                    "source": "Customer → User",
                    "reference": {
                        "customer": customer.name,
                        "user": portal_user,
                        "role": customer.customer_group or "Unknown"
                    }
                })

    # ---------------------------------
    # 2️⃣ FARMER REGISTRATION
    # ---------------------------------
    farmer_registration = frappe.db.get_value(
        "Farmer Registration",
        {"mobile_number": mobile_no,"docstatus":["!=",2]},
        "name"
    )

    if farmer_registration:
        return api_response(True, "User status fetched successfully", {
            "status": "PENDING_FOR_APPROVAL",
            "source": "Farmer Registration",
            "reference": farmer_registration
        })

    # ---------------------------------
    # 3️⃣ DEALER REGISTRATION
    # ---------------------------------
    dealer_registration = frappe.db.get_value(
        "Delear Registration",
        {"mobile_number": mobile_no,"docstatus":["!=",2]},
        "name"
    )

    if dealer_registration:
        return api_response(True, "User status fetched successfully", {
            "status": "PENDING_FOR_APPROVAL",
            "source": "Delear Registration",
            "reference": dealer_registration
        })

    # ---------------------------------
    # 4️⃣ LEAD
    # ---------------------------------
    lead = frappe.db.get_value(
        "Lead",
        {"mobile_no": mobile_no},
        "name"
    )

    if lead:
        return api_response(True, "User status fetched successfully", {
            "status": "LEAD",
            "source": "Lead",
            "reference": lead
        })

    # ---------------------------------
    # 5️⃣ NEW USER
    # ---------------------------------
    return api_response(True, "User status fetched successfully", {
        "status": "NEW_USER",
        "source": None,
        "reference": None
    })

import frappe
@frappe.whitelist()
def enqueue():
    frappe.enqueue(
        "shoption_api.erp_api.utility.set_item_supplier_company_bulk",
        queue="long",
        timeout=6000
    )

import frappe

def set_item_supplier_company_bulk():
    try:
        company_name="Shoption Private Limited"
        frappe.db.sql("""
            UPDATE `tabItem Supplier`
            SET custom_company = %s
        """, (company_name,))
        frappe.db.commit()
        frappe.log_error(f"All Item Supplier entries updated to company: {company_name}", "Item Supplier Bulk Update")
    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Item Supplier Bulk Update Error")

from shoption_api.shoption_test_api.page.show_otp.show_otp import get_last_otp
@frappe.whitelist()
def get_otp_from_mobile(mobile_no=None):
    try:
        if not mobile_no:
            return api_response(False, "mobile_no is required")

        data = get_last_otp(mobile_no)

        if not data.get("status"):
            return api_response(False, data.get("message"))

        return api_response(True, "OTP data fetch successfully", data)

    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Doesn't fetch OTP Error")
        return api_response(False, "OTP error while fetch the data")



# import frappe

# def create_missing_registrations():
#     try:
#         batch_size = 1000
#         start = 0
#         total_created = 0
#         total_skipped = 0

#         # ✅ Preload ALL existing mobile numbers
#         dealer_registered = set(
#             d.mobile_number for d in frappe.db.get_all(
#                 "Delear Registration",
#                 fields=["mobile_number"]
#             ) if d.mobile_number
#         )

#         farmer_registered = set(
#             f.mobile_number for f in frappe.db.get_all(
#                 "Farmer Registration",
#                 fields=["mobile_number"]
#             ) if f.mobile_number
#         )

#         while True:
#             leads = frappe.db.get_all(
#                 "Lead",
#                 filters=[
#                     ["name", "not like", "%CRM%"],
#                     ["type", "in", ["Dealer", "Farmer"]]
#                 ],
#                 fields=["name", "lead_name", "mobile_no", "type"],
#                 limit_start=start,
#                 limit_page_length=batch_size
#             )

#             if not leads:
#                 break

#             for lead in leads:
#                 try:
#                     if not lead.mobile_no:
#                         total_skipped += 1
#                         continue

#                     if lead.type == "Farmer" and lead.mobile_no not in farmer_registered:

#                         frappe.get_doc({
#                             "doctype": "Farmer Registration",
#                             "from_document": lead.name,
#                             "mobile_number": lead.mobile_no,
#                             "first_name": lead.lead_name,
#                             "is_completed": 0
#                         }).insert(ignore_permissions=True)

#                         farmer_registered.add(lead.mobile_no)
#                         total_created += 1

#                     elif lead.type == "Dealer" and lead.mobile_no not in dealer_registered:

#                         frappe.get_doc({
#                             "doctype": "Delear Registration",
#                             "from_document": lead.name,
#                             "mobile_number": lead.mobile_no,
#                             "shop_name": lead.lead_name,
#                             "is_completed": 0
#                         }).insert(ignore_permissions=True)

#                         dealer_registered.add(lead.mobile_no)
#                         total_created += 1

#                     else:
#                         total_skipped += 1

#                 except Exception:
#                     frappe.log_error(
#                         frappe.get_traceback(),
#                         "Registration Creation Error"
#                     )
#                     total_skipped += 1

#             frappe.db.commit()
#             start += batch_size

#         frappe.log_error(
#             f"Job Completed. Created: {total_created}, Skipped: {total_skipped}",
#             "Lead Registration Background Job"
#         )

#     except Exception:
#         frappe.db.rollback()
#         frappe.log_error(
#             frappe.get_traceback(),
#             "Lead Registration Background Job Failed"
#         )

# import frappe

# def update_payment_term_notation():
#     try:
#         # Keywords → Notation mapping
#         mapping = {
#             "Advance": "Advance",
#             "Against PI": "Against PI",
#             "Against Dispatch LR": "Against Dispatch",
#             "Against GRN": "Against GRN",
#             "Credit": "Credit"
#         }

#         # Get all payment terms
#         terms = frappe.get_all("Payment Term", fields=["name", "payment_term_name"])

#         for term in terms:
#             name = term.payment_term_name or ""
#             notation = None

#             # Find first keyword in name
#             for key, value in mapping.items():
#                 if key in name:
#                     notation = value
#                     break

#             if notation:
#                 frappe.db.set_value(
#                     "Payment Term",
#                     term.name,
#                     "custom_notation",
#                     notation,
#                     update_modified=False  # Do not change modified timestamp
#                 )
#                 frappe.log_error(
#                     f"Payment Term '{term.payment_term_name}' updated with notation '{notation}'",
#                     "Payment Term Notation Debug"
#                 )
#             else:
#                 frappe.log_error(
#                     f"Payment Term '{term.payment_term_name}' skipped (no matching notation)",
#                     "Payment Term Notation Debug"
#                 )

#         frappe.db.commit()
#         frappe.log_error("All Payment Term notations updated successfully!", "Payment Term Notation Debug")

#     except Exception:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "Payment Term Notation Update Failed")



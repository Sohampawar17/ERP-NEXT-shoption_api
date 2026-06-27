import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist(allow_guest=True)
def check_customer(mobile_no=None):
    if not mobile_no:
        return {"status": False, "message": "mobile_no is required"}

    mobile_no = str(mobile_no).strip()

    # Existing customer check
    fields = [
        "name",
        "mobile_no",
        "custom_profile_status",
        "custom_gst_status",
        "custom_dealer_status",
        "custom_product_access",
    ]

    customer = frappe.get_all(
        "Customer",
        filters={"mobile_no": mobile_no},
        fields=fields,
        limit=1
    )

    if customer:
        cust = customer[0]

        assigned = frappe.get_all(
            "Marketplace Assignment",
            filters={"parent": cust.name},
            fields=["marketplace"]
        )

        return {
            "status": True,
            "exists": True,
            "mobile_no": mobile_no,
            "profile_status": cust.custom_profile_status,
            "gst_status": cust.custom_gst_status,
            "dealer_status": cust.custom_dealer_status,
            "product_access": cust.custom_product_access,
            "marketplaces_assigned": assigned,
            "message": "Existing dealer fetched"
        }

    # Create new customer
    new_cust = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": mobile_no,
        "mobile_no": mobile_no,
        "customer_group": "Individual",
        "territory": "All Territories",
        "custom_profile_status": 0,
        "custom_gst_status": "Pending",
        "custom_dealer_status": "Pending",
        "custom_product_access": 0
    })

    new_cust.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": True,
        "exists": False,
        "mobile_no": mobile_no,
        "profile_status": 0,
        "gst_status": "Pending",
        "dealer_status": "Pending",
        "product_access": 0,
        "marketplaces_assigned": [],
        "message": "New customer created"
    }

# def generate_username():
#     company = frappe.db.get_single_value("Global Defaults", "default_company")

#     # Lock table to avoid race condition (very important)
#     frappe.db.sql("LOCK TABLE `tabCompany` WRITE")

#     try:
#         counter = frappe.db.get_value("Company", company, "custom_user_counter") or 0
#         counter = int(counter) + 1

#         frappe.db.set_value("Company", company, "custom_user_counter", counter)
#         frappe.db.commit()
#     finally:
#         frappe.db.sql("UNLOCK TABLES")

#     return str(counter)




# @frappe.whitelist()
# def create_user_and_customer(mobile_no, name, role, email_id=None, lead_id=None, registration_id=None):

#     if not mobile_no:
#         return {"status": False, "message": "mobile_no is required"}

#     if not name:
#         return {"status": False, "message": "name is required"}

#     # Final Email Logic
#     final_email = email_id if email_id else f"{mobile_no}@demo.com"

#     # Generate unique username
#     username = generate_username()

#     # Create User
#     user = frappe.get_doc({
#         "doctype": "User",
#         "email": final_email,            # final email used here
#         "first_name": name,
#         "full_name": name,
#         "mobile_no": mobile_no,
#         "send_welcome_email": 0,

#         "username": username,            # shown username
#         "name": username,                # force user ID = username

#         "role_profile_name": role
#     })

#     user.flags.ignore_mandatory = True
#     user.flags.ignore_permissions = True
#     user.insert()

#     # Set Document Type
#     doc_type = "Delear Registration" if role == "Dealer" else "Farmer Registration"

#     # Create Customer
#     customer = frappe.get_doc({
#         "doctype": "Customer",
#         "customer_name": name,
#         "mobile_no": mobile_no,
#         "customer_group": role,

#         "lead_name": lead_id,
#         "custom_document_type": doc_type,
#         "custom_document_value": registration_id
#     })
#     customer.insert(ignore_permissions=True)

#     # Link Portal User
#     customer.append("portal_users", {
#         "user": user.name
#     })
#     customer.save(ignore_permissions=True)

#     frappe.db.commit()

#     return {
#         "status": True,
#         "message": "User & Customer Created Successfully",
#         "user_id": user.name,
#         "email": final_email,
#         "customer_id": customer.name
#     }

# update 29/11/2025
def generate_username():
    company = frappe.db.get_single_value("Global Defaults", "default_company")

    frappe.db.sql("LOCK TABLE `tabCompany` WRITE")

    try:
        counter = frappe.db.get_value("Company", company, "custom_user_counter") or 0
        counter = int(counter) + 1
        frappe.db.set_value("Company", company, "custom_user_counter", counter)
        frappe.db.commit()
    finally:
        frappe.db.sql("UNLOCK TABLES")

    return str(counter)

# @frappe.whitelist()
# def create_user_and_customer(mobile_no, name, role, email_id=None, lead_id=None, registration_id=None):

#     if not mobile_no:
#         return {"status": False, "message": "mobile_no is required"}

#     if not name:
#         return {"status": False, "message": "name is required"}

#     # ✔ Final Email Logic
#     final_email = email_id if email_id else f"{mobile_no}@demo.com"

#     # ✔ Generate unique username from counter
#     username = generate_username()

#     # ✔ Create User
#     user = frappe.get_doc({
#         "doctype": "User",
#         "email": final_email,
#         "first_name": name,
#         "full_name": name,
#         "mobile_no": mobile_no,
#         "send_welcome_email": 0,

#         "username": username,     # → shown username
#         # "name": username,         # → user ID also username

#         "role_profile_name": role
#     })

#     user.flags.ignore_mandatory = True
#     user.flags.ignore_permissions = True
#     user.flags.no_throttle = True  # Disable rate limiting
#     user.insert()

#     # ✔ Document Type
#     doc_type = "Delear Registration" if role == "Dealer" else "Farmer Registration"

#     user.reload()  # reload to ensure all fields are updated
    
#     # ✔ Create Customer
#     customer = frappe.get_doc({
#         "doctype": "Customer",
#         "customer_name": name,
#         "mobile_no": mobile_no,
#         "customer_group": role,

#         "lead_name": lead_id,
#         "custom_document_type": doc_type,
#         "custom_document_value": registration_id
#     })
#     customer.insert(ignore_permissions=True)

#     # ✔ Link Portal User
#     customer.append("portal_users", {
#         "user": user.name
#     })
#     customer.save(ignore_permissions=True)

#     frappe.db.commit()

#     return {
#         "status": True,
#         "message": "User & Customer Created Successfully",
#         "user_id": user.name,   # this = username
#         "email": final_email,
#         "customer_id": customer.name
#     }

@frappe.whitelist()
def create_user_and_customer(
    mobile_no,
    name,
    role,
    email_id=None,
    lead_id=None,
    registration_id=None
):
    try:
        mobile_no = mobile_no
        name = name
        role = role
        final_email = (email_id or f"{mobile_no}@demo.com").strip().lower()
        lead_id = lead_id
        registration_id = registration_id

        if not mobile_no or not name:
            frappe.throw("mobile_number and first_name are required")

        doc_type = "Delear Registration" if role == "Dealer" else "Farmer Registration"  # fix spelling as needed
        reg_doc = frappe.get_doc(doc_type, registration_id)

        # ---------- USER ----------
        user_name = frappe.db.exists("User", {"email": final_email})
        if user_name:
            user = frappe.get_doc("User", user_name)
        else:
            user = frappe.get_doc({
                "doctype": "User",
                "email": final_email,
                "first_name": name,
                "full_name": name,
                "mobile_no": mobile_no,
                "send_welcome_email": 0,
                "username": generate_username(),
                "role_profile_name": role
            })
            user.flags.ignore_permissions = True
            user.new_password = frappe.generate_hash(length=10)
            user.insert(ignore_permissions=True)

        # ---------- CUSTOMER ----------
        customer_name = (
            frappe.db.exists("Customer", {
                "custom_document_type": doc_type,
                "custom_document_value": registration_id
            })
            or frappe.db.exists("Customer", {"mobile_no": mobile_no})
        )

        if customer_name:
            customer = frappe.get_doc("Customer", customer_name)
        else:
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": name,
                "mobile_no": mobile_no,
                "customer_group": role,
                "lead_name": lead_id,
                "custom_document_type": doc_type,
                "custom_document_value": registration_id
            })
            customer.insert(ignore_permissions=True)

        # portal user link
        if not any(pu.user == user.name for pu in customer.portal_users):
            customer.append("portal_users", {"user": user.name})
            customer.save(ignore_permissions=True)

        # ---------- ADDRESSES ----------
        address_data = {
            "address_title": name,
            "address_line1": reg_doc.address_line_1,
            "address_line2": reg_doc.address_line_2,
            "city": str(reg_doc.marketplace) if reg_doc.marketplace else None,
            "custom_tahshil": str(reg_doc.tahshil) if reg_doc.tahshil else None,
            "custom_district": str(reg_doc.district) if reg_doc.district else None,
            "state": reg_doc.state,
            "country": reg_doc.country,
            "pincode": str(reg_doc.pincode).strip() if reg_doc.pincode else None,
            "phone": str(mobile_no),
            "email_id": final_email,
            "links": [{"link_doctype": "Customer", "link_name": customer.name}],
        }

        def has_address(address_type):
            return frappe.db.sql("""
                select a.name
                from `tabAddress` a
                join `tabDynamic Link` dl on dl.parent = a.name
                where dl.link_doctype='Customer'
                  and dl.link_name=%s
                  and a.address_type=%s
                limit 1
            """, (customer.name, address_type))

        if not has_address("Billing"):
            frappe.get_doc({
                "doctype": "Address",
                "address_type": "Billing",
                "is_primary_address": 1,
                "is_shipping_address": 0,
                **address_data
            }).insert(ignore_permissions=True)

        if not has_address("Shipping"):
            frappe.get_doc({
                "doctype": "Address",
                "address_type": "Shipping",
                "is_primary_address": 0,
                "is_shipping_address": 1,
                **address_data
            }).insert(ignore_permissions=True)

        # (optional) store links on your registration doc
        # doc.customer = customer.name
        # doc.user = user.name

    except Exception:
        # rollback any partial inserts and stop submission
        frappe.db.rollback()
        frappe.log_error("Before Submit: create_user_and_customer failed", frappe.get_traceback())
        frappe.throw("User/Customer creation failed. Please check Error Log.")




@frappe.whitelist(allow_guest=True)
def get_dealer_status(mobile_no=None):
    """Return full dealer onboarding status after OTP verification."""
    
    # Validate mobile number
    if not mobile_no:
        return {"status": False, "message": "mobile_no is required"}

    mobile_no = str(mobile_no).strip()

    # Header Auth Check
    cfg = frappe.get_site_config()
    expected_key = cfg.get("shoption_api_key")
    expected_secret = cfg.get("shoption_api_secret")

    incoming_key = frappe.get_request_header("X-API-KEY")
    incoming_secret = frappe.get_request_header("X-API-SECRET")

    if incoming_key != expected_key or incoming_secret != expected_secret:
        return {"status": False, "message": "Unauthorized"}

    # Call existing customer status function
    status = check_customer(mobile_no=mobile_no)

    # Format response
    return {
        "status": True,
        "exists": status.get("exists"),
        "mobile_no": mobile_no,

        "profile_status": status.get("profile_status"),
        "gst_status": status.get("gst_status"),
        "dealer_status": status.get("dealer_status"),
        "product_access": status.get("product_access"),
        "marketplaces_assigned": status.get("marketplaces_assigned", []),

        "message": "Dealer status fetched"
    }

@frappe.whitelist(allow_guest=True)
def save_basic_profile(
    mobile_no=None,
    customer_name=None,
    owner_name=None,
    email=None,
    whatsapp_no=None,
    address_line1=None,
    address_line2=None,
    pincode=None,
    country=None,
    state=None,
    district=None,
    tehsil=None,
    marketplace_ids=None, 
    gender=None,
    dob=None,
    gst_number=None
):
    """Save or update basic dealer profile."""

    # ---- AUTH CHECK ----
    cfg = frappe.get_site_config()
    if frappe.get_request_header("X-API-KEY") != cfg.get("shoption_api_key"):
        return {"status": False, "message": "Unauthorized"}
    if frappe.get_request_header("X-API-SECRET") != cfg.get("shoption_api_secret"):
        return {"status": False, "message": "Unauthorized"}

#     # ---- VALIDATION ----
#     if not mobile_no:
#         return {"status": False, "message": "mobile_no is required"}
#     mobile = "".join(ch for ch in str(mobile_no) if ch.isdigit())
#     if len(mobile) < 10:
#         return {"status": False, "message": "Invalid mobile number"}

#     # ---- MARKETPLACE LIST NORMALIZATION ----
#     mp_list = []
#     if marketplace_ids:
#         try:
#             import json
#             if marketplace_ids.strip().startswith("["):
#                 mp_list = json.loads(marketplace_ids)
#             else:
#                 mp_list = [x.strip() for x in marketplace_ids.split(",") if x.strip()]
#         except:
#             mp_list = [x.strip() for x in marketplace_ids.split(",") if x.strip()]

#     # ---- GET OR CREATE CUSTOMER ----
#     try:
#         cust_name = frappe.db.get_value("Customer", {"mobile_no": mobile}, "name")
#         if cust_name:
#             customer = frappe.get_doc("Customer", cust_name)
#         else:
#             customer = frappe.get_doc({
#                 "doctype": "Customer",
#                 "customer_name": customer_name or f"Customer-{mobile}",
#                 "customer_type": "Individual",
#                 "mobile_no": mobile
#             })
#             customer.insert(ignore_permissions=True)
#     except Exception as e:
#         frappe.log_error(f"Customer create/update failed: {e}", "save_basic_profile")
#         return {"status": False, "message": "Customer creation failed"}

#     # ---- UPDATE CUSTOMER FIELDS ----
#     try:
#         if customer_name:
#             customer.customer_name = customer_name

#         if gst_number:
#             customer.custom_gst_number = gst_number

#         # Mark profile as completed
#         customer.custom_profile_status = 1

#         # Ensure default flags
#         if not customer.custom_gst_status:
#             customer.custom_gst_status = "None"
#         if not customer.custom_dealer_status:
#             customer.custom_dealer_status = "None"
#         if not customer.custom_product_access:
#             customer.custom_product_access = 0

#         customer.save(ignore_permissions=True)
#     except Exception as e:
#         frappe.log_error(f"Customer update error: {e}", "save_basic_profile")
#         return {"status": False, "message": "Customer update failed"}

#     # ---- CONTACT CREATION ----
#     try:
#         contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile}, "name")
#         if contact_name:
#             contact = frappe.get_doc("Contact", contact_name)
#         else:
#             contact = frappe.get_doc({
#                 "doctype": "Contact",
#                 "first_name": owner_name or customer.customer_name,
#                 "mobile_no": mobile,
#                 "email_id": email or "",
#                 "phone": whatsapp_no or "",
#                 "links": [{"link_doctype": "Customer", "link_name": customer.name}]
#             })
#         if owner_name:
#             contact.first_name = owner_name
#         if email:
#             contact.email_id = email
#         if whatsapp_no:
#             contact.phone = whatsapp_no
#         contact.save(ignore_permissions=True)
#     except Exception as e:
#         frappe.log_error(f"Contact update failed: {e}", "save_basic_profile")

#     try:
#         address_name = frappe.db.get_value(
#             "Address",
#             {"address_line1": address_line1, "pincode": pincode, "city": district},
#             "name"
#         )

#         if address_name:
#             addr = frappe.get_doc("Address", address_name)
#         else:
#             addr = frappe.get_doc({
#                 "doctype": "Address",
#                 "address_title": customer.customer_name,
#                 "address_type": "Billing",
#                 "address_line1": address_line1 or "",
#                 "address_line2": address_line2 or "",
#                 "pincode": pincode or "",
#                 "city": district or "",
#                 "state": state or "",
#                 "country": country or "",
#             })

#         # Always ensure dynamic link
#         addr.append("links", {
#             "link_doctype": "Customer",
#             "link_name": customer.name
#         })

#         addr.save(ignore_permissions=True)

#     except Exception as e:
#         frappe.log_error(f"Address create/update failed: {e}", "save_basic_profile")

#     if mp_list:
#         frappe.db.delete("Marketplace Assignment", {"parent": customer.name})

#         for mp in mp_list:
#             # check marketplace exists (new doctype + new field)
#             if not frappe.db.exists("Marketplace", {"marketplace_name": mp}):
#                 frappe.log_error(f"Marketplace not found: {mp}", "save_basic_profile")
#                 continue

#             row = frappe.get_doc({
#                 "doctype": "Marketplace Assignment",
#                 "parent": customer.name,
#                 "parenttype": "Customer",
#                 "parentfield": "marketplaces_assigned",
#                 "marketplace": mp,        # marketplace_name is used as name
#                 "tahshil": tehsil or ""   # updated field name
#             })
#             row.insert(ignore_permissions=True)


# #    except Exception as e:
# #       frappe.log_error(f"Marketplace assignment failed: {e}", "save_basic_profile")

#     # ---- FINAL COMMIT ----
#     frappe.db.commit()

#     return {
#         "status": True,
#         "message": "Profile saved successfully",
#         "customer": customer.name,
#         "profile_status": customer.custom_profile_status,
#         "gst_status": customer.custom_gst_status,
#         "dealer_status": customer.custom_dealer_status,
#         "product_access": customer.custom_product_access
#     }

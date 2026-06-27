# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response
# from frappe.utils import get_url
# from shoption_api.area.api import get_marketplaces
# from frappe.utils import today
# from shoption_api.dealership.dealership_item import get_items_by_dealership_master

# @frappe.whitelist(allow_guest=True)
# def get_dealership_profile_details(dealership=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     if not dealership:
#         return api_response(False, "dealership (ADL docname) is required")

#     # -------------------------------------------------
#     # FETCH Dealership Profile USING dealership field
#     # -------------------------------------------------
#     profile_name = frappe.db.get_value(
#         "Dealership Profile",
#         {"dealership": dealership},
#         "name"
#     )

#     #If no profile found → return null data (NOT error)
#     if not profile_name:
#         return api_response(True, "No dealership profile found", None)

#     doc = frappe.get_doc("Dealership Profile", profile_name)

#     # -------------------------
#     # HEADER / BASIC DETAILS
#     # -------------------------
#     data = {
#         "form_name": doc.name,
#         "dealership": doc.dealership,
#         "plan_logo": get_url(doc.plan_logo) if doc.plan_logo else "",
#         "current_status": doc.current_status,
#         "dealership_plan": doc.dealerhsip_plan,
#         "dealership_plan_name": doc.dealership_plan_name,
#         "dealership_type": doc.dealership_type,
#         "valid_from": doc.valid_from,
#         "valid_till": doc.valid_till,
#         "Plan_deposite_amount" : doc.deposite_amount,
#         "annual_target": doc.annual_target,
#         "first_order_value": doc.first_order_value,
#         "Exclusivity" : doc.is_exclusive
#     }

#     # -------------------------
#     # DEALERSHIP PLAN RANGE
#     # -------------------------
#     data["dealership_plan_range"] = []
#     for row in doc.dealership_plan_range:
#         data["dealership_plan_range"].append({
#             "notation": row.notation,
#             "value": row.value,
#             "in_percentage": row.in__percentage
#         })

#     # -------------------------
#     # DOCUMENTS
#     # -------------------------
#     data["documents"] = {
#         "gst_certificate": get_url(doc.gst_certificate) if doc.gst_certificate else None,
#         "aadhaar": get_url(doc.aadhaar) if doc.aadhaar else None,
#         "dealership_aggrement": get_url(doc.dealership_aggrement) if doc.dealership_aggrement else None,
#         "passport_sized_photograph": get_url(doc.passport_sized_photograph) if doc.passport_sized_photograph else None,
#         "pan": get_url(doc.pan) if doc.pan else None,
#         "shop_photo": get_url(doc.shop_photo) if doc.shop_photo else None,
#         "address_proof": get_url(doc.address_proof) if doc.address_proof else None,
#     }

#     # -------------------------
#     # TAHSILS
#     # -------------------------
#     # data["tahsils"] = [{"tehsil": row.tehsil} for row in doc.tahsils]

#     # # -------------------------
#     # # MARKETPLACES
#     # # -------------------------
#     # data["marketplaces"] = [{"marketplace": row.marketplace} for row in doc.marketplaces]
       
#     # ==========================================================
#     # COVERAGE LOGIC 
#     # ==========================================================
#     coverage = []

#     # ---------- CASE 1: TAHSILS PRESENT ----------
#     if doc.tahsils:
#         for row in doc.tahsils:
#             tehsil_name = row.tehsil

#             resp = get_marketplaces(tehsil_name)
#             if resp.get("status"):
#                 for mp in resp.get("data", []):
#                     parts = mp["id"].split("-")
#                     if len(parts) >= 4:
#                         coverage.append({
#                             "marketplace": parts[0],
#                             "tehsil": parts[1],
#                             "district": parts[2],
#                             "state": parts[3]
#                         })

#     # ---------- CASE 2: MARKETPLACES PRESENT ----------
#     elif doc.marketplaces:
#         for row in doc.marketplaces:
#             mp_name = row.marketplace   # correct field

#             parts = mp_name.split("-")
#             if len(parts) >= 4:
#                 coverage.append({
#                     "marketplace": parts[0],
#                     "tehsil": parts[1],
#                     "district": parts[2],
#                     "state": parts[3]
#                 })
                
#     data["coverage"] = coverage
    
#     return api_response(True, "Dealership profile details fetched successfully", data)

import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from frappe.utils import get_url, today
from shoption_api.area.api import get_marketplaces
from shoption_api.dealership.dealership_item import get_items_by_dealership_master


def get_marketplace_name(mp_id):
    if not mp_id:
        return ""

    return frappe.db.get_value(
        "Marketplace",
        mp_id,
        "marketplace_name"
    ) or mp_id
    
def get_tehsil_name(tehsil_id):
    if not tehsil_id:
        return ""

    return frappe.db.get_value(
        "Tahshil",
        tehsil_id,
        "tahshil"
    ) or tehsil_id

@frappe.whitelist(allow_guest=True)
def get_dealership_profile_details(dealership=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not dealership:
        return api_response(False, "dealership (ADL docname) is required")

    # -------------------------------------------------
    # FETCH Dealership Profile USING dealership field
    # -------------------------------------------------
    profile_name = frappe.db.get_value(
        "Dealership Profile",
        {"dealership": dealership},
        "name"
    )

    # If no profile found → return null data (NOT error)
    if not profile_name:
        return api_response(True, "No dealership profile found", None)

    doc = frappe.get_doc("Dealership Profile", profile_name)

    # ==================================================
    # BASIC DETAILS
    # ==================================================
    data = {
        "form_name": doc.name,
        "dealership": doc.dealership,
        "plan_logo": get_url(doc.plan_logo) if doc.plan_logo else "",
        "current_status": doc.current_status,
        "dealership_plan": doc.dealerhsip_plan,
        "dealership_plan_name": doc.dealership_plan_name,
        "dealership_type": doc.dealership_type,
        "valid_from": doc.valid_from,
        "valid_till": doc.valid_till,
        "Plan_deposite_amount": doc.deposite_amount,
        "annual_target": float(doc.annual_target or 0),
        "first_order_value": float(doc.first_order_value or 0),
        "Exclusivity": doc.is_exclusive,
        "plan_coverage":frappe.db.get_value("Dealership Plan", doc.dealerhsip_plan, "plan_coverage") if doc.dealerhsip_plan else None,
        "shop_name" : doc.shop_name,
        "brand" : "Gbru"
    }

    # ==================================================
    # DEALERSHIP PLAN RANGE
    # ==================================================
    data["dealership_plan_range"] = [
        {
            "notation": row.notation,
            "value": row.value,
            "in_percentage": row.in__percentage
        }
        for row in doc.dealership_plan_range
    ]
    def build_file_url(file_path):
        if not file_path:
            return None

        if file_path.startswith("http"):
            return file_path

        if file_path.startswith("/"):
            return get_url(file_path)

        return None
    # ==================================================
    # DOCUMENTS
    # ==================================================
    data["documents"] = {
        "gst_certificate": get_url(doc.gst_certificate) if doc.gst_certificate else None,
        "aadhaar": get_url(doc.aadhaar) if doc.aadhaar else None,
        "dealership_aggrement": get_url(doc.dealership_aggrement) if doc.dealership_aggrement else get_url(frappe.db.get_value("Apply Dealership", doc.dealership, "dealership_aggrement")),
        "passport_sized_photograph": get_url(doc.passport_sized_photograph) if doc.passport_sized_photograph else None,
        "pan": get_url(doc.pan) if doc.pan else None,
        "shop_photo": get_url(doc.shop_photo) if doc.shop_photo else None,
        "address_proof": get_url(doc.address_proof) if doc.address_proof else None,
        "Dealership_certificate" : get_url(doc.certificate) if doc.certificate else None,
    }

    # ==================================================
    # COVERAGE LOGIC (TAHSIL / MARKETPLACE)
    # ==================================================
    dealership = frappe.get_doc("Apply Dealership", doc.dealership)
    state = dealership.state
    district_name = frappe.db.get_value(
        "District",
        dealership.district,
        "district_name"
    ) if dealership.district else ""
    plan_coverage = frappe.db.get_value(
        "Dealership Plan",
        doc.dealerhsip_plan,
        "plan_coverage"
    ) if doc.dealerhsip_plan else ""
    coverage = []
    # ---------- TAHSIL COVERAGE ----------
    if dealership.tehsil and plan_coverage == "Tehsils":
        for row in dealership.tehsil:
            tehsil_name = get_tehsil_name(row.tehsil)
            coverage.append({
                "marketplace": "",
                "tehsil": tehsil_name,
                "district": district_name,
                "state": state
            })


    # ---------- MARKETPLACE COVERAGE ----------
    elif dealership.marketplaces and plan_coverage == "Marketplaces":
        for row in dealership.marketplaces:
            mp_name = get_marketplace_name(row.marketplace)
            marketplace_data = frappe.db.get_value("Marketplace", row.marketplace, ["marketplace_name","tahshil"], as_dict=True)
            tehsil_name = get_tehsil_name(marketplace_data.tahshil)
            coverage.append({
                "marketplace": mp_name,
                "tehsil": tehsil_name,
                "district": district_name,
                "state": state
            })


    # ---------- FALLBACK ----------
    elif state or district_name and plan_coverage == "District":
        coverage.append({
            "marketplace": "",
            "tehsil": "",
            "district": district_name,
            "state": state
        })
    data["coverage"] = coverage

    # # ==================================================
    # # REVENUE PERFORMANCE (🔥 FIXED)
    # # ==================================================
    # booked_revenue = 0.0
    # annual_target = float(doc.annual_target or 0)

    # # -------------------------
    # # Allowed Item Codes
    # # -------------------------
    # allowed_item_codes = set()

    # if doc.dealership_type:
    #     items_resp = get_items_by_dealership_master(
    #         dealership_master_name=doc.dealership_type,
    #         page=1,
    #         page_size=10000
    #     )

    #     # 🔥 IMPORTANT FIX: handle both dict & list responses
    #     if isinstance(items_resp, dict):
    #         categories = items_resp.get("data", {}).get("categories", [])
    #     elif isinstance(items_resp, list):
    #         categories = items_resp
    #     else:
    #         categories = []

    #     for cat in categories:
    #         for item in cat.get("items", []):
    #             allowed_item_codes.add(item.get("item_code"))

    # # -------------------------
    # # Fetch Sales Orders
    # # -------------------------
    # sales_orders = frappe.get_all(
    #     "Sales Order",
    #     filters={
    #         "customer": doc.dealership,
    #         "billing_status": "Fully Billed",
    #         "transaction_date": ["between", [doc.valid_from, today()]]
    #     },
    #     fields=["name"]
    # )

    # # -------------------------
    # # Calculate Revenue
    # # -------------------------
    # for so_row in sales_orders:
    #     so = frappe.get_doc("Sales Order", so_row.name)
    #     for item in so.items:
    #         if item.item_code in allowed_item_codes:
    #             booked_revenue += float(item.amount or 0)

    # achievement_percentage = 0.0
    # if annual_target > 0:
    #     achievement_percentage = round((booked_revenue / annual_target) * 100, 2)

    # data["revenue_performance"] = {
    #     "booked_revenue": booked_revenue,
    #     "annual_target": annual_target,
    #     "achievement_percentage": achievement_percentage
    # }
    
    # ==================================================
    # REVENUE PERFORMANCE (SAFE + FIXED)
    # ==================================================
    # booked_revenue = 0.0
    # annual_target = float(doc.annual_target or 0)

    # # -------------------------
    # # Allowed Item Codes
    # # -------------------------
    # allowed_item_codes = set()

    # if doc.dealership_type:
    #     items_resp = get_items_by_dealership_master(
    #         dealership_master_name=doc.dealership_type,
            
    #         page=1,
    #         page_size=10000
    #     )

    #     categories = []

    #     # 🔥 SAFE NORMALIZATION (THIS FIXES YOUR ERROR)
    #     if isinstance(items_resp, dict):
    #         # API wrapped response
    #         data_block = items_resp.get("data")
    #         if isinstance(data_block, dict):
    #             categories = data_block.get("categories", [])
    #         elif isinstance(data_block, list):
    #             categories = data_block

    #     elif isinstance(items_resp, list):
    #         # direct list response
    #         categories = items_resp

    #     # extract item codes
    #     for cat in categories:
    #         for item in cat.get("items", []):
    #             if item.get("item_code"):
    #                 allowed_item_codes.add(item["item_code"])

    # # -------------------------
    # # Fetch Sales Orders
    # # -------------------------
    # sales_orders = frappe.get_all(
    #     "Sales Order",
    #     filters={
    #         "customer": doc.dealership,
    #         "custom_payment_status": "Fully Paid",
    #         "transaction_date": ["between", [doc.valid_from, today()]]
    #     },
    #     fields=["name"]
    # )

    # # -------------------------
    # # Calculate Revenue
    # # -------------------------
    # for so_row in sales_orders:
    #     so = frappe.get_doc("Sales Order", so_row.name)

    #     for item in so.items:
    #         if item.item_code in allowed_item_codes:
    #             booked_revenue += float(item.amount or 0)

    # achievement_percentage = 0.0
    # if annual_target > 0:
    #     achievement_percentage = round((booked_revenue / annual_target) * 100, 2)

    # data["revenue_performance"] = {
    #     "booked_revenue": booked_revenue,
    #     "annual_target": annual_target,
    #     "achievement_percentage": achievement_percentage
    # }
    
    from shoption_api.dealership.dealership_item import get_allowed_item_codes_by_dealership

    booked_revenue = 0.0
    annual_target = float(doc.annual_target or 0)

    # -------------------------
    # Allowed Item Codes (SINGLE SOURCE OF TRUTH)
    # -------------------------
    allowed_item_codes = get_allowed_item_codes_by_dealership(
        doc.dealership_type
    )
    
    mobile_number = frappe.db.get_value(
    "Apply Dealership",
        doc.dealership,
        "mobile_number"
    )

    if not mobile_number:
        frappe.throw("Mobile number not found for this dealership")

    customer = frappe.db.get_value(
        "Customer",
        {"mobile_no": mobile_number},
        "name"
    )

    

    # -------------------------
    # Fetch Sales Orders
    # -------------------------
    sales_orders = frappe.get_all(
        "Sales Order",
        filters={
            "customer": customer,
            "docstatus": 1,
            "custom_payment_status": "Fully Paid",
            "transaction_date": ["between", [doc.valid_from, today()]]
        },
        fields=["name"]
    )

    # -------------------------
    # Calculate Revenue
    # -------------------------
    for so_row in sales_orders:
        so = frappe.get_doc("Sales Order", so_row.name)

        for item in so.items:
            if str(item.item_code).strip() in allowed_item_codes:
                booked_revenue += (float(item.amount or 0)+float(item.igst_amount or 0)+float(item.cgst_amount or 0)+float(item.sgst_amount or 0))

    achievement_percentage = 0.0
    if annual_target > 0:
        achievement_percentage = round(
            (booked_revenue / annual_target) * 100, 2
        )

    data["revenue_performance"] = {
        "booked_revenue": booked_revenue,
        "annual_target": annual_target,
        "achievement_percentage": achievement_percentage
    }

    return api_response(True, "Dealership profile details fetched successfully", data)


import frappe
from frappe.utils.file_manager import save_file
from shoption_api.erp_api.common import api_auth, require_post, api_response


@frappe.whitelist(allow_guest=True)
def save_dealership_certificate(docname=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # -----------------------------
    # VALIDATION
    # -----------------------------
    if not docname:
        return api_response(False, "docname (Dealership Profile) is required")

    if not frappe.db.exists("Dealership Profile", docname):
        return api_response(False, "Dealership Profile not found")

    uploaded_file = frappe.request.files.get("file")
    if not uploaded_file:
        return api_response(False, "Certificate file is required")

    doc = frappe.get_doc("Dealership Profile", docname)

    # -----------------------------
    # SAVE FILE (Attach pattern)
    # -----------------------------
    content = uploaded_file.read()

    saved = save_file(
        uploaded_file.filename,
        content,
        "Dealership Profile",
        doc.name,
        is_private=0   # 🔥 Attach field requires private
    )

    if not saved or not saved.file_url:
        return api_response(False, "Failed to upload certificate")

    # -----------------------------
    # MAP FILE
    # -----------------------------
    doc.certificate = saved.file_url

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # -----------------------------
    # RESPONSE
    # -----------------------------
    return api_response(
        True,
        "Dealership certificate uploaded successfully",
        {
            "docname": doc.name,
            "certificate": saved.file_url
        }
    )



import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist()
def create_dealership_profile(apply_dealership=None):
#     api_auth()
#     require_post()
    frappe.set_user("Administrator")

    if not apply_dealership:
        return api_response(False, "apply_dealership is required")

    # ----------------------------------
    # Validate Apply Dealership
    # ----------------------------------
    if not frappe.db.exists("Apply Dealership", apply_dealership):
        return api_response(False, "Apply Dealership not found")

    ad = frappe.get_doc("Apply Dealership", apply_dealership)

    # ----------------------------------
    # Prevent duplicate profile
    # ----------------------------------
    existing = frappe.db.exists(
        "Dealership Profile",
        {"dealership_form": ad.name}
    )

    if existing:
        return api_response(
            True,
            "Dealership Profile already exists",
            {
                "dealership_profile": existing
            }
        )

    # ----------------------------------
    # Create Dealership Profile
    # ----------------------------------
    dp = frappe.get_doc({
        "doctype": "Dealership Profile",
        "dealership_form": ad.name,
        "dealership": ad.name   # 🔥 THIS IS IMPORTANT
    })

    dp.insert(ignore_permissions=True)

    return api_response(
        True,
        "Dealership Profile created successfully",
        {
            "dealership_profile": dp.name
        }
    )

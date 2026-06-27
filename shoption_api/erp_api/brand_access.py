# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def create_brand_access(user=None, price_list=None, user_name=None, monthly_revenue=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     # ---- VALIDATION ----
#     if not user:
#         return api_response(False, "user is required")
#     if not price_list:
#         return api_response(False, "price_list is required")
#     # if not user_name:
#     #     return api_response(False, "user_name is required")
#     # if not monthly_revenue:
#     #     return api_response(False, "monthly_revenue is required")

#     # Validate Price List exists
#     if not frappe.db.exists("Price List", price_list):
#         return api_response(False, "Invalid price_list")

#     # Prevent duplicate pending requests
#     existing = frappe.db.exists(
#         "Brand Access",   # Doctype remains same if not renamed
#         {"user": user, "price_list": price_list}
#     )
#     if existing:
#         return api_response(False, "Price list access request already exists")

#     # ---- CREATE DOCUMENT ----
#     try:
#         doc = frappe.new_doc("Brand Access")  # Doctype still Brand Access, only field renamed
#         doc.user = user
#         doc.price_list = price_list  # changed from doc.brand
#         doc.user_name = user_name
#         doc.monthly_revenue = monthly_revenue
#         doc.insert(ignore_permissions=True)
#         doc.submit()

#         return api_response(True, "Price list access request submitted", {
#             "price_list_access_id": doc.name
#         })

#     except Exception as e:
#         frappe.log_error(f"Price List Access API failed: {e}")
#         return api_response(False, "Failed to create price list access request")

# 05/12     : Updated to select price list based on brand and user role
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def create_brand_access(user=None, brand=None, user_role=None, user_name=None, monthly_revenue=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     # ---- VALIDATION ----
#     if not user:
#         return api_response(False, "user is required")
#     if not brand:
#         return api_response(False, "brand is required")
#     if not user_role:
#         return api_response(False, "user_role is required (Dealer/Farmer)")

#     # ---- Check Brand Exists ----
#     if not frappe.db.exists("Brand", brand):
#         return api_response(False, "Invalid brand")

#     # ---- Fetch Price Lists linked to this brand ----
#     price_lists = frappe.get_list(
#         "Price List",
#         filters={"brand": brand},
#         fields=["name"]
#     )

#     if not price_lists:
#         return api_response(False, "No price list found for this brand")

#     # ---- Auto-select Price List based on role ----
#     selected_price_list = None

#     for pl in price_lists:
#         pl_name = pl.name.lower()
#         role = user_role.lower()

#         if role in pl_name:  # matches '-dealer' or '-farmer'
#             selected_price_list = pl.name
#             break

#     if not selected_price_list:
#         return api_response(False, "No matching price list found for user role")

#     # ---- Prevent duplicate pending requests ----
#     existing = frappe.db.exists(
#         "Brand Access",
#         {"user": user, "brand": brand, "price_list": selected_price_list}
#     )

#     if existing:
#         return api_response(False, "Brand access request already exists")

#     # ---- CREATE DOCUMENT ----
#     try:
#         doc = frappe.new_doc("Brand Access")
#         doc.user = user
#         doc.brand = brand                        # NEW
#         doc.price_list = selected_price_list     # Auto-selected based on role
#         doc.user_name = user_name
#         doc.monthly_revenue = monthly_revenue

#         doc.insert(ignore_permissions=True)
#         doc.submit()

#         return api_response(True, "Brand access request submitted", {
#             "brand_access_id": doc.name,
#             "price_list_used": selected_price_list
#         })

#     except Exception as e:
#         frappe.log_error(f"Brand Access API failed: {e}")
#         return api_response(False, "Failed to create brand access request")

# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def create_brand_access(user=None, brand=None, user_role=None, user_name=None, monthly_revenue=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     # ---- VALIDATION ----
#     if not user:
#         return api_response(False, "user is required")
#     if not brand:
#         return api_response(False, "brand is required")
#     if not user_role:
#         return api_response(False, "user_role is required (Dealer/Farmer)")

#     # ---- Check Brand Exists ----
#     if not frappe.db.exists("Brand", brand):
#         return api_response(False, "Invalid brand")

#     # ---- Fetch Price Lists linked to this brand ----
#     price_lists = frappe.get_all(
#         "Price List",
#         filters={"custom_brand": brand},
#         fields=["name"]
#     )

#     if not price_lists:
#         return api_response(False, "No price list found for this brand")

#     # ---- Auto-select Price List based on role ----
#     selected_price_list = None
#     role = user_role.lower()

#     for pl in price_lists:
#         if role in pl.name.lower():   # matches -dealer OR -farmer
#             selected_price_list = pl.name
#             break

#     if not selected_price_list:
#         return api_response(False, "No matching price list found for user role")

#     # ---- Prevent duplicate requests ----
#     existing = frappe.db.exists(
#         "Brand Access",
#         {"user": user, "brand": brand, "price_list": selected_price_list}
#     )

#     if existing:
#         return api_response(False, "Brand access request already exists")

#     # ---- CREATE DOCUMENT ----
#     try:
#         doc = frappe.new_doc("Brand Access")
#         doc.user = user
#         doc.brand = brand
#         doc.price_list = selected_price_list
#         doc.user_name = user_name
#         doc.monthly_revenue = monthly_revenue

#         doc.insert(ignore_permissions=True)
#         doc.submit()

#         return api_response(True, "Brand access request submitted", {
#             "brand_access_id": doc.name,
#             "price_list_used": selected_price_list
#         })

#     except Exception as e:
#         frappe.log_error(f"Brand Access API failed: {e}")
#         return api_response(False, "Failed to create brand access request")

import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from frappe.exceptions import DuplicateEntryError

@frappe.whitelist(allow_guest=True)
def create_brand_access(user=None, brand=None, user_role=None, user_name=None, monthly_revenue=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # ---- VALIDATION ----
    if not user:
        return api_response(False, "user is required")
    if not brand:
        return api_response(False, "brand is required")
    if not user_role:
        return api_response(False, "user_role is required (Dealer/Farmer)")

    # ---- Check Brand Exists ----
    if not frappe.db.exists("Brand", brand):
        return api_response(False, "Invalid brand")

    # ---- Fetch Price Lists linked to this brand ----
    price_lists = frappe.get_all(
        "Price List",
        filters={"custom_brand": brand},
        fields=["name"]
    )

    if not price_lists:
        return api_response(False, "No price list found for this brand")

    # ---- Auto-select Price List based on role ----
    selected_price_list = None
    role = user_role.lower()

    for pl in price_lists:
        if role in pl.name.lower():   # matches -dealer OR -farmer
            selected_price_list = pl.name
            break

    if not selected_price_list:
        return api_response(False, "No matching price list found for user role")

    # ---- Prevent duplicate requests ----
    existing = frappe.db.exists(
        "Brand Access",
        {"user": user, "brand": brand, "price_list": selected_price_list}
    )

    if existing:
        return api_response(False, "Brand access request already exists")

    # ---- CREATE DOCUMENT ----
    try:
        doc = frappe.new_doc("Brand Access")
        doc.user = user
        doc.brand = brand
        doc.price_list = selected_price_list
        doc.user_name = user_name
        doc.monthly_revenue = monthly_revenue

        doc.insert(ignore_permissions=True)
        doc.save()

        return api_response(True, "Brand access request submitted", {
            "brand_access_id": doc.name,
            "price_list_used": selected_price_list
        })

    except DuplicateEntryError:
        # Handles PRIMARY KEY duplicate cleanly
        return api_response(False, "Brand access request already exists")

    except Exception as e:
        # Avoid logging huge traceback causing CharacterLengthExceeded
        safe_msg = str(e)[:120]  # limit error size
        frappe.log_error("Brand Access API failed: " + safe_msg)

        return api_response(False, "Failed to create brand access request")

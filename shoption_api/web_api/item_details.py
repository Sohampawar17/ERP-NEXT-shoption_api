# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response
# from shoption_api.cart.cart import get_item_price_withgst  # GST helper

# @frappe.whitelist(allow_guest=True)
# def get_item_details(item_code=None, mobile_no=None):

#     api_auth()
#     require_post()

#     # ------------------------------------------------
#     # 1) Basic Validations
#     # ------------------------------------------------
#     if not item_code:
#         return api_response(False, "item_code is required")

#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # ------------------------------------------------
#     # 2) FIND CUSTOMER FROM MOBILE
#     # ------------------------------------------------
#     customer = frappe.get_all(
#         "Customer",
#         filters={"mobile_no": mobile_no},
#         fields=["name", "customer_group"],
#         limit=1
#     )

#     user_id = None
#     customer_group = None
#     customer_name = None

#     if customer:
#         customer_name = customer[0].name
#         customer_group = customer[0].customer_group

#         portal_user = frappe.get_all(
#             "Portal User",
#             filters={"parent": customer_name},
#             fields=["user"],
#             limit=1
#         )

#         if portal_user:
#             user_id = portal_user[0].user

#     # ------------------------------------------------
#     # 3) SET USER CONTEXT
#     # ------------------------------------------------
#     if user_id:
#         frappe.set_user(user_id)
#     else:
#         frappe.set_user("Administrator")

#     # ------------------------------------------------
#     # 4) FETCH ITEM DETAILS
#     # ------------------------------------------------
#     item_doc = frappe.get_all(
#         "Item",
#         filters={"name": item_code},
#         fields=[
#             "name",
#             "item_name",
#             "brand",
#             "stock_uom",
#             "min_order_qty",
#             "description",
#             "custom_image_1",
#             "custom_image_2",
#             "custom_image_3",
#             "custom_image_4",
#             "custom_image_5"
#         ],
#         limit=1
#     )

#     if not item_doc:
#         return api_response(False, "Invalid item_code")

#     item = item_doc[0]

#     # ------------------------------------------------
#     # 5) PRICE FILTERS (ONLY FARMER OVERRIDE)
#     # ------------------------------------------------
#     price_filters = {"item_code": item_code}

#     if customer_group == "Farmer":
#         price_filters["price_list"] = f"{item.brand}-Farmer"

#     # ------------------------------------------------
#     # 6) FETCH PRICE
#     # ------------------------------------------------
#     price_row = frappe.get_list(
#         "Item Price",
#         filters=price_filters,
#         fields=[
#             "price_list",
#             "custom_mrp",
#             "discount",
#             "price_list_rate",
#             "custom_full_payment",
#             "custom_full_payment_discount_value",
#             "custom_display_rate_discount",
#             "custom_cod_discount_value",
#             "custom_cash_on_delivery_",
#             "custom_cod_display_rate",
#             "custom_oem_code",
#             "valid_from"
#         ],
#         order_by="valid_from desc",
#         limit=1
#     )

#     if user_id and price_row:
#         p = price_row[0]

#         price_list = p.price_list
#         mrp = p.custom_mrp
#         price = p.price_list_rate
#         discount = p.discount
#         actual_rate = p.price_list_rate

#         full_payment_discount = p.custom_full_payment_discount_value
#         full_payment_amount = p.custom_full_payment

#         COD_discount = p.custom_cod_discount_value
#         COD_value = p.custom_cash_on_delivery_
#         COD_display = p.custom_cod_display_rate

#         oem_code = p.custom_oem_code
#         valid_from = p.valid_from
#     else:
#         price_list = mrp = price = discount = actual_rate = None
#         full_payment_discount = full_payment_amount = None
#         COD_discount = COD_value = COD_display = None
#         oem_code = valid_from = None

#     # ------------------------------------------------
#     # 7) MOQ LOGIC (UNCHANGED)
#     # ------------------------------------------------
#     moq = None
#     if customer_group:
#         item_full_doc = frappe.get_doc("Item", item_code)
#         for row in item_full_doc.get("custom_moq", []):
#             if row.customer_group == customer_group:
#                 moq = row.min_qty
#                 break

#     # ------------------------------------------------
#     # 8) GST PRICE (ONLY rate_incl_gst)
#     # ------------------------------------------------
#     gst_price = None

#     if user_id and price:
#         gst_data = get_item_price_withgst(
#             item_code=item_code,
#             customer=customer_name,
#             customer_group=customer_group,
#             company=frappe.defaults.get_global_default("company"),
#             currency=frappe.defaults.get_global_default("currency"),
#             qty=1,
#             brand=item.brand
#         )
#         gst_price = gst_data.get("rate_incl_gst")
#         gst_difference = gst_data.get("difference") or 0
        
        
#     # Add GST difference to payment values (runtime only)
#     if full_payment_amount:
#         full_payment_amount = round(full_payment_amount + gst_difference, 2)

#     if COD_value:
#         COD_value = round(COD_value + gst_difference, 2)


#     # ------------------------------------------------
#     # 9) FINAL RESPONSE
#     # ------------------------------------------------
#     return api_response(True, "Item details fetched", {
#         "item_code": item.name,
#         "item_name": item.item_name,
#         "brand": item.brand,
#         "price_list": price_list,
#         "mrp": mrp,
#         # "price": price,
#         "no_gst_price": price,  # Non-GST price 17/18
#         "price": gst_price,  # GST price as main price 17/18
#         # "gst_price": gst_price,
#         "discount": discount,
#         # "actual_rate": actual_rate,
#         "actual_rate": gst_price,  # GST price as actual rate 17/18

#         "full_payment_amount": full_payment_amount,
#         "full_payment_discount": full_payment_discount,

#         "COD_value": COD_value,
#         "COD_Display": COD_display,
#         "COD_discount": COD_discount,

#         "oem_code": oem_code,
#         "moq": moq,
#         "min_order_qty": item.min_order_qty,
#         "measurement_unit": item.stock_uom,
#         "description": item.description,
#         "valid_from": valid_from,

#         "images": {
#             "image_1": item.custom_image_1,
#             "image_2": item.custom_image_2,
#             "image_3": item.custom_image_3,
#             "image_4": item.custom_image_4,
#             "image_5": item.custom_image_5
#         }
#     })

import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst  # GST helper

@frappe.whitelist(allow_guest=True)
def get_item_details(item_code=None, mobile_no=None):

    api_auth()
    require_post()

    # ------------------------------------------------
    # 1) Basic Validations
    # ------------------------------------------------
    if not item_code:
        return api_response(False, "item_code is required")

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    # ------------------------------------------------
    # 2) FIND CUSTOMER FROM MOBILE
    # ------------------------------------------------
    customer = frappe.get_all(
        "Customer",
        filters={"mobile_no": mobile_no},
        fields=["name", "customer_group"],
        limit=1
    )

    user_id = None
    customer_group = None
    customer_name = None

    if customer:
        customer_name = customer[0].name
        customer_group = customer[0].customer_group

        portal_user = frappe.get_all(
            "Portal User",
            filters={"parent": customer_name},
            fields=["user"],
            limit=1
        )

        if portal_user:
            user_id = portal_user[0].user

    # ------------------------------------------------
    # 3) SET USER CONTEXT
    # ------------------------------------------------
    frappe.set_user(user_id if user_id else "Administrator")

    # ------------------------------------------------
    # 4) FETCH ITEM DETAILS
    # ------------------------------------------------
    item_doc = frappe.get_all(
        "Item",
        filters={"name": item_code},
        fields=[
            "name",
            "item_name",
            "brand",
            "stock_uom",
            "min_order_qty",
            "description",
            "custom_image_1",
            "custom_image_2",
            "custom_image_3",
            "custom_image_4",
            "custom_image_5"
        ],
        limit=1
    )

    if not item_doc:
        return api_response(False, "Invalid item_code")

    item = item_doc[0]

    # ------------------------------------------------
    # 5) PRICE FILTERS (STRICT FARMER ENFORCEMENT)
    # ------------------------------------------------
    price_filters = {"item_code": item_code}

    force_farmer_price = False

    if customer_group == "Farmer" or not user_id:
        force_farmer_price = True
        price_filters["price_list"] = ["like", "%-Farmer"]

    # ------------------------------------------------
    # 6) FETCH PRICE
    # ------------------------------------------------
    price_row = frappe.get_list(
        "Item Price",
        filters=price_filters,
        fields=[
            "price_list",
            "custom_mrp",
            "discount",
            "price_list_rate",
            "custom_full_payment",
            "custom_full_payment_discount_value",
            "custom_display_rate_discount",
            "custom_cod_discount_value",
            "custom_cash_on_delivery_",
            "custom_cod_display_rate",
            "custom_oem_code",
            "valid_from"
        ],
        order_by="valid_from desc",
        limit=1
    )

    p = price_row[0] if price_row else None

    # 🔒 HARD SAFETY — BLOCK non-farmer price leakage
    if force_farmer_price and p and "Farmer" not in p.price_list:
        p = None

    if p:
        price_list = p.price_list
        mrp = p.custom_mrp
        price = p.price_list_rate
        discount = p.discount
        actual_rate = p.price_list_rate

        full_payment_discount = p.custom_full_payment_discount_value
        full_payment_amount = p.custom_full_payment

        COD_discount = p.custom_cod_discount_value
        COD_value = p.custom_cash_on_delivery_
        COD_display = p.custom_cod_display_rate

        oem_code = p.custom_oem_code
        valid_from = p.valid_from
    else:
        price_list = mrp = price = discount = actual_rate = None
        full_payment_discount = full_payment_amount = None
        COD_discount = COD_value = COD_display = None
        oem_code = valid_from = None

    # ------------------------------------------------
    # 7) MOQ LOGIC (UNCHANGED)
    # ------------------------------------------------
    moq = None
    if customer_group:
        item_full_doc = frappe.get_doc("Item", item_code)
        for row in item_full_doc.get("custom_moq", []):
            if row.customer_group == customer_group:
                moq = row.min_qty
                break

    # ------------------------------------------------
    # 8) GST PRICE
    # ------------------------------------------------
    gst_price = None
    gst_difference = 0

    if p and price:
        gst_data = get_item_price_withgst(
            item_code=item_code,
            customer=customer_name,
            customer_group=customer_group,
            company=frappe.defaults.get_global_default("company"),
            currency=frappe.defaults.get_global_default("currency"),
            qty=1,
            brand=item.brand
        )
        gst_price = gst_data.get("rate_incl_gst")
        gst_difference = gst_data.get("difference") or 0

    if full_payment_amount:
        full_payment_amount = round(full_payment_amount + gst_difference, 2)

    if COD_value:
        COD_value = round(COD_value + gst_difference, 2)

    # ------------------------------------------------
    # 9) FINAL RESPONSE
    # ------------------------------------------------
    return api_response(True, "Item details fetched", {
        "item_code": item.name,
        "item_name": item.item_name,
        "brand": item.brand,
        "price_list": price_list,
        "mrp": mrp,
        "no_gst_price": price,
        "price": gst_price,
        "discount": discount,
        "actual_rate": gst_price,

        "full_payment_amount": full_payment_amount,
        "full_payment_discount": full_payment_discount,

        "COD_value": COD_value,
        "COD_Display": COD_display,
        "COD_discount": COD_discount,

        "oem_code": oem_code,
        "moq": moq,
        "min_order_qty": item.min_order_qty,
        "measurement_unit": item.stock_uom,
        "description": item.description,
        "valid_from": valid_from,

        "images": {
            "image_1": item.custom_image_1,
            "image_2": item.custom_image_2,
            "image_3": item.custom_image_3,
            "image_4": item.custom_image_4,
            "image_5": item.custom_image_5
        }
    })

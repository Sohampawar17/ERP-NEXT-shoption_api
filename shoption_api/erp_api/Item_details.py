# updated with gst price
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst  # GST helper
from frappe.utils import flt,cint,get_url
def zero_to_none(value):
    return None if value in (0, 0.0) else value


@frappe.whitelist(allow_guest=True)
def get_item_details(item_code=None, mobile_no=None):

    api_auth()
    require_post()

    if not item_code:
        return api_response(False, "item_code is required")

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    try:
        # ------------------------------------------------
        # 1) Get Customer + Group
        # ------------------------------------------------
        customer = frappe.db.get_value(
            "Customer",
            {"mobile_no": mobile_no},
            ["name", "customer_group"],
            as_dict=True
        )

        customer_name = customer.name if customer else None
        customer_group = customer.customer_group if customer else None

        # ------------------------------------------------
        # 2) Get Portal User
        # ------------------------------------------------
        user_id = None
        if customer_name:
            user_id = frappe.db.get_value(
                "Portal User",
                {"parent": customer_name},
                "user"
            )

        # ------------------------------------------------
        # 3) Safe User Context
        # ------------------------------------------------
        if user_id:
            frappe.set_user(user_id)
        else:
            frappe.set_user("Administrator") # NEVER use Administrator here

        # ------------------------------------------------
        # 4) Get Item
        # ------------------------------------------------
        item = frappe.db.get_value(
            "Item",
            item_code,
            [
                "name", "item_name", "brand", "stock_uom",
                "min_order_qty", "description",
                "custom_image_1", "custom_image_2",
                "custom_image_3", "custom_image_4",
                "custom_image_5"
            ],
            as_dict=True
        )

        if not item:
            return api_response(False, "Invalid item_code")

        # ------------------------------------------------
        # 5) Price List Logic
        # ------------------------------------------------
        price_list = None
        if customer_group and customer_group.lower() == "farmer":
            price_list = frappe.db.get_value(
                "Price List",
                {
                    "custom_customer_group": "Farmer",
                    "custom_brand": item.brand,
                    "selling": 1
                },
                "name"
            ) or f"{item.brand}-Farmer"
        elif customer_group and customer_group.lower() == "dealer":
            price_list = frappe.db.get_value(
                "Price List",
                {
                    "custom_customer_group": "Dealer",
                    "custom_brand": item.brand,
                    "selling": 1
                },
                "name"
            ) or f"{item.brand}-Dealer"
        # ------------------------------------------------
        # 6) Get Latest Item Price
        # ------------------------------------------------
        price_doc = None
        price_rate = None
        discount = None
        full_payment_discount = None
        full_payment_amount = None
        full_payment_discount_type = None
        COD_discount = None
        COD_value = None
        COD_type = None
        COD_display = None
        oem_code = None
        valid_from = None
        mrp = None
        prices=[]
        price_filters = {"item_code": item_code,"selling":1}
        if price_list:
            price_filters["price_list"] = price_list
        if customer_group and customer_group.lower() in ["farmer"] and user_id:
            prices = frappe.get_all(
            "Item Price",
            filters=price_filters,
            fields=[
                "price_list",
                "custom_mrp",
                "custom_discount as discount",
                "price_list_rate",
                "custom_full_payment",
                "custom_full_payment_discount_type",
                "custom_full_payment_discount_value",
                "custom_cod_discount_type",
                "custom_cod_discount_value",
                "custom_cash_on_delivery_",
                "custom_cod_display_rate",
                "custom_oem_code",
                "valid_from"
            ],
            order_by="valid_from desc",
            limit=1
        )
        elif user_id:
            prices = frappe.get_list(
                "Item Price",
                filters=price_filters,
                fields=[
                    "price_list",
                    "custom_mrp",
                    "custom_discount as discount",
                    "price_list_rate",
                    "custom_full_payment",
                    "custom_full_payment_discount_type",
                    "custom_full_payment_discount_value",
                    "custom_cod_discount_type",
                    "custom_cod_discount_value",
                    "custom_cash_on_delivery_",
                    "custom_cod_display_rate",
                    "custom_oem_code",
                    "valid_from"
                ],
                order_by="valid_from desc",
                limit=1
            )
        if prices:
            price_doc = prices[0]
            price_rate = price_doc.price_list_rate
            discount = price_doc.discount
            mrp = price_doc.custom_mrp
            valid_from = price_doc.valid_from
            oem_code = price_doc.custom_oem_code

            # Full Payment
            full_payment_amount = price_doc.custom_full_payment
            full_payment_discount_type = price_doc.custom_full_payment_discount_type
            full_payment_discount = price_doc.custom_full_payment_discount_value

            # COD
            COD_type = price_doc.custom_cod_discount_type
            COD_discount = price_doc.custom_cod_discount_value
            COD_value = price_doc.custom_cash_on_delivery_
            COD_display = price_doc.custom_cod_display_rate

        # ------------------------------------------------
        # 7) Convert Percentage Discounts to Amount
        # ------------------------------------------------
        

        # ------------------------------------------------
        # 8) MOQ
        # ------------------------------------------------
        moq = None
        if customer_group:
            moq = frappe.db.get_value(
                "MOQ Items",
                {
                    "parent": item_code,
                    "customer_group": customer_group
                },
                "min_qty"
            )

        # ------------------------------------------------
        # 9) GST Calculation
        # ------------------------------------------------
        gst_price = None
        gst_difference = 0
        gst_rate = 0
        if price_rate and customer_name:
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
            gst_rate = gst_data.get("gst_rate") or 0
        if price_rate:

            # -------- FULL PAYMENT --------
            if full_payment_discount_type == "Percentage":
                percent = full_payment_discount or 0
                full_payment_discount = round((price_rate * percent) / 100, 2)
        
            discounted_price = price_rate - (full_payment_discount or 0)
            full_payment_discount=round(full_payment_discount + (full_payment_discount * gst_rate / 100), 2)
            full_payment_amount = round(
                discounted_price + (discounted_price * gst_rate / 100), 2
            )

            # -------- COD --------
            if COD_type == "Percentage":
                percent = COD_discount or 0
                COD_discount = round((price_rate * percent) / 100, 2)

            if COD_value:
                basic=COD_display+COD_value
                COD_value = round(
                    COD_value + (basic * gst_rate / 100), 2
                )

        # ------------------------------------------------
        # 10) Brand Name
        # ------------------------------------------------
        if item.brand:
            item.brand = frappe.db.get_value("Brand", item.brand, "brand")

        # ------------------------------------------------
        # 11) Response
        # ------------------------------------------------
        data= {
            "item_code": item.name,
            "item_name": item.item_name,
            "brand": item.brand,
            "price_list": price_doc.price_list if price_doc else price_list,
            "mrp": zero_to_none(mrp),
            "no_gst_price": zero_to_none(price_rate),
            "price": zero_to_none(gst_price),
            "actual_rate": zero_to_none(gst_price),
            "discount": zero_to_none(discount),
            "full_payment_amount": zero_to_none(full_payment_amount),
            "full_payment_discount": zero_to_none(full_payment_discount),
            "COD_value": zero_to_none(COD_value),
            "COD_Display": COD_display if COD_value else None,
            "COD_discount": COD_discount if COD_discount else 0,
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
        }
        return api_response(True, "Item details fetched", data)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "item_details")
        return api_response(False, "Failed to fetch Item Details")

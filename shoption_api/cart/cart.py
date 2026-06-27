from shoption_api.erp_api.common import api_response
from shoption_api.cart.app_utils import (
    validate_method,
    exception_handel,
    gen_response,
    generate_key,
    get_global_defaults,
    get_employee_by_user
    )
import frappe
import json
from urllib.parse import quote
from erpnext.accounts.party import get_party_details
from erpnext.accounts.utils import get_account_currency
from frappe.utils import flt,cint,get_url,getdate
import time
from frappe import _


@frappe.whitelist()
def get_customer_from_user():
    """Fetch customer linked with selected User"""
    customer = frappe.db.get_value(
        "Portal User",
        {"user": frappe.session.user},
        "parent")

    if not customer:
        return {"error": "No customer linked with this user"}

    return customer

def clean_cart_item(row):
    return {
        "item": row.item,
        "brand": row.brand,
        "checkout": row.checkout,
        "item_name": row.item_name,
        "gst_hsn_code": row.gst_hsn_code,
        "description": row.description,
        "quantity": row.quantity,
        "uom": row.uom,
        "image": row.image,
        "selling_price_list": row.selling_price_list,
        "rate": row.rate_with_gst,
        "amount": row.quantity * row.rate_with_gst,
        "discount": row.discount,
        "min_qty": row.min_qty,
        "is_moq_applicable": row.is_moq_applicable,
    }

@frappe.whitelist()
def get_item_moq(item_code, customer_group):
    moqs = frappe.get_all(
        "MOQ Items",
        filters={
            "parent": item_code,
            "customer_group": customer_group
        },
        fields=["min_qty"]
    )
    return moqs[0].min_qty if moqs else None

@frappe.whitelist()
def get_item_price_withgst(
    item_code,
    customer,
    customer_group,
    company,
    currency,
    qty=1,
    brand=None,
    base_rate_override=None 
):
    # -------- PRICE LIST --------
    price_list = frappe.db.get_value(
        "Price List",
        {
            "custom_customer_group": customer_group,
            "custom_brand": brand,
            "enabled": 1,
            "selling": 1
        },
        "name"
    ) or frappe.get_cached_value(
        "Selling Settings", None, "default_price_list"
    )
    

    # -------- ITEM BASE RATE --------
    from erpnext.stock.get_item_details import get_item_details

    item = get_item_details({
        "item_code": item_code,
        "customer": customer,
        "company": company,
        "currency": currency,
        "price_list": price_list,
        "price_list_currency": currency,
        "qty": qty,
        "doctype": "Sales Order"
    })

    base_rate = base_rate_override or item.get("price_list_rate", 0)
    # base_rate = item.get("price_list_rate", 0)

    # -------- GST RATE --------
    gst_rate = frappe.db.get_value(
        "Item Tax Template",
        item.get("item_tax_template"),
        "gst_rate"
    ) or 0
    base_rate_with_gst = round(base_rate * (1 + gst_rate / 100), 2)
    difference=round(base_rate_with_gst-base_rate,2)
    return {
        "gst_rate": gst_rate,
        "rate_excl_gst": base_rate,
        "rate_incl_gst": round(base_rate * (1 + gst_rate / 100), 2),
        "difference":difference
    }



@frappe.whitelist()
@validate_method(methods=["POST"])
def add_cart():
    import json

    try:
        body = json.loads(frappe.request.data or "{}")
        items = body.get("items")

        if not items or not isinstance(items, list):
            return api_response(False, "Items must be a list and cannot be empty")

        user = frappe.session.user
        # Get or create Shopping Cart
        if frappe.db.exists("Shopping Cart", {"user": user}):
            cart_doc = frappe.get_doc("Shopping Cart", {"user": user})
        else:
            cart_doc = frappe.new_doc("Shopping Cart")
            cart_doc.user = user

        # Add / update items
        for row in items:
            item_code = row.get("item")
            qty = float(row.get("quantity", 0))
            customer_group = cart_doc.customer_group
            is_moq_applicable= row.get("is_moq_applicable")
            if not item_code:
                return api_response(False, "Item code is required")

            if qty <= 0:
                return api_response(False, f"Invalid quantity for {item_code}")

            # 🔎 Fetch MOQ
            min_qty = get_item_moq(item_code, customer_group) or 0
            # 🚫 MOQ Validation
            if min_qty and qty < min_qty and not is_moq_applicable:
                return api_response(
                    False,
                    f"Minimum order quantity for {item_code} "
                    f"({customer_group}) is {min_qty}"
                )
            # base_rate, rate_with_gst = get_rate_with_gst(
            #     item_code,
            #     cart_doc.customer,
            #     customer_group,
            #     cart_doc.company,
            #     cart_doc.currency,
            #     qty
            # )
            existing_row = next(
                (d for d in cart_doc.items if d.item == item_code),
                None
            )

            if existing_row:
                existing_row.quantity = qty
                existing_row.amount = row.get("amount", 0)
                existing_row.min_qty = min_qty,
                existing_row.is_moq_applicable = is_moq_applicable
            else:
                cart_doc.append("items", {
                    "item": item_code,
                    "quantity": qty,
                    "min_qty": min_qty,
                    "is_moq_applicable": is_moq_applicable
                })

        cart_doc.save(ignore_permissions=True)
        cleaned = [clean_cart_item(r) for r in cart_doc.items]

        return api_response(True, "Items added in cart successfully", cleaned)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "add_cart")
        return api_response(False, "Unable to add items to cart")
@frappe.whitelist()
@validate_method(methods=["GET"])
def get_cart(page=1, page_size=20):
    try:
        user = frappe.session.user

        try:
            page = int(page)
            page_size = int(page_size)
        except:
            page, page_size = 1, 20

        start = (page - 1) * page_size

        cart_items = frappe.db.get_all(
            "Cart Item",
            filters={"parent": user},
            fields=["*"],
            # limit_start=start,
            # limit_page_length=page_size,
            order_by="modified desc"
        )

        if not cart_items:
            return api_response(True, "Cart fetched", {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "items": [],
                "total_quantity": 0,
                "total_amount": 0
            })

        # ✅ Collect unique brand IDs
        brand_ids = list({item.get("brand") for item in cart_items if item.get("brand")})

        # ✅ Fetch brand names in single query
        brand_map = {}
        if brand_ids:
            brands = frappe.db.get_all(
                "Brand",
                filters={"name": ["in", brand_ids]},
                fields=["name", "brand as brand_name"]
            )
            brand_map = {b.name: b.brand_name for b in brands}

        # ✅ Clean data + replace brand ID with name
        cleaned = []
        for item in cart_items:
            row = clean_cart_item(item)

            brand_id = row.get("brand")
            if brand_id and brand_id in brand_map:
                row["brand"] = brand_map[brand_id]   # replace with name

            cleaned.append(row)

        # Calculate totals
        total_qty = sum(float(item.get("quantity", 0)) for item in cleaned)
        total_amount = sum(float(item.get("amount", 0)) for item in cleaned)
        total = len(cleaned)
        total_pages = (total + page_size - 1) // page_size

        response = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": cleaned,
            "total_quantity": total_qty,
            "total_amount": total_amount
        }

        return api_response(True, "Cart fetched", response)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_cart")
        return api_response(False, "Error fetching cart")

@frappe.whitelist()
@validate_method(methods=["GET"])
def get_cart_count():
    try:
        user = frappe.session.user

        # Fetch only required fields
        cart_items = frappe.db.get_all(
            "Cart Item",
            filters={"parent": user},
            fields=["quantity"],
        )

        total_qty = sum(float(item.quantity or 0) for item in cart_items)

        response = {
            "count": len(cart_items),
            "total_quantity": total_qty
        }

        return api_response(True, "Cart count fetched", response)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_cart_count")
        return api_response(False, "Failed to fetch cart count")


# @frappe.whitelist()
# @validate_method(methods=["POST"])
# def add_cart_item():
#     try:
#         body = json.loads(frappe.request.data or "{}")

#         item = body.get("item")
#         quantity = body.get("quantity")
#         rate = body.get("rate")
#         amount = body.get("amount")
#         checkout = body.get("checkout", 0)

#         if not item:
#             return api_response(False, "Item required")

#         user = frappe.session.user

#         # Ensure parent exists
#         if not frappe.db.exists("Shopping Cart", {"user": user}):
#             parent = frappe.get_doc({
#                 "doctype": "Shopping Cart",
#                 "user": user
#             }).insert(ignore_permissions=True)
#         else:
#             parent = frappe.db.get_value("Shopping Cart", {"user": user}, "name")

#         # Check duplicate
#         if frappe.db.exists("Cart Item", {"parent": parent, "item": item}):
#             return api_response(False, "Item already exists. Use update API.")

#         # Insert row directly
#         child = frappe.get_doc({
#             "doctype": "Cart Item",
#             "parent": parent,
#             "parentfield": "items",
#             "parenttype": "Shopping Cart",
#             "item": item,
#             "quantity": quantity,
#             "rate": rate,
#             "amount": amount,
#             "checkout": checkout
#         }).insert(ignore_permissions=True)

#         return api_response(True, "Item added", child.as_dict())
#     except Exception as e:
#         frappe.log_error(f"Add Cart Item Error: {frappe.get_traceback()}", "add_cart_item")
#         return api_response(False, str(e))
from erpnext.stock.get_item_details import get_item_details

@frappe.whitelist()
def get_item_details_for_cart(customer, customer_group, company, currency, item_code, qty, brand=None):
    """
    Fetch optimized item details for shopping cart
    """

    if not item_code:
        frappe.throw("Item Code is required")

    if not customer:
        frappe.throw("Customer is required")

    # --------- PRICE LIST ---------
    price_list = frappe.db.get_value(
        "Price List",
        {
            "custom_customer_group": customer_group,
            "custom_brand": brand,
            "enabled": 1,
            "selling": 1
        },
        "name"
    )

    if not price_list:
        price_list = frappe.get_cached_value(
            "Selling Settings", None, "default_price_list"
        )

    # --------- ITEM DETAILS ---------
    args = {
        "item_code": item_code,
        "customer": customer,
        "company": company,
        "currency": currency,
        "qty": qty,
        "doctype": "Sales Order",
        "price_list": price_list,
        "price_list_currency": currency,
    }

    item_details = get_item_details(args)
    discount = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list},
        "custom_discount"
    ) or 0

    rate = float(item_details.get("price_list_rate") or 0)
    amount = rate * float(qty)

    return {
        "uom": item_details.get("uom"),
        "rate": rate,
        "amount": amount,
        "price_list": price_list,
        "discount": discount,
        "item_tax_template":item_details.get("item_tax_template")
    }

@frappe.whitelist()
@validate_method(methods=["PUT"])
def update_cart_item():
    import json

    try:
        body = json.loads(frappe.request.data or "{}")

        item_code = body.get("item")
        quantity = float(body.get("quantity") or 0)

        if not item_code or quantity <= 0:
            return api_response(False, "Item and valid quantity required")

        user = frappe.session.user

        # -------- CART ROW --------
        row = frappe.db.get_value(
            "Cart Item",
            {"parent": user, "item": item_code},
            ["name", "item", "brand"],
            as_dict=True
        )

        if not row:
            return api_response(False, "Item not found in cart")

        # -------- CUSTOMER CONTEXT --------
        customer_dict=frappe.db.get_value("Shopping Cart",{"user":user},["customer","customer_group","company","currency"],as_dict=True)
        customer = customer_dict.get("customer")
        customer_group = customer_dict.get("customer_group")
        company =   customer_dict.get("company")
        currency = customer_dict.get("currency")

        # -------- PRICING --------
        item_details = get_item_details_for_cart(
            customer=customer,
            customer_group=customer_group,
            company=company,
            currency=currency,
            item_code=item_code,
            qty=quantity,
            brand=row.brand
        )
        gst_rate = frappe.db.get_value(
            "Item Tax Template",
            item_details.get("item_tax_template"),
            "gst_rate"
        ) or 0
       
        item_details["rate_with_gst"] = round(item_details.get("rate", 0) + (item_details.get("rate", 0) * gst_rate / 100), 2)
        # -------- UPDATE CART --------
        frappe.db.set_value(
            "Cart Item",
            row.name,
            {
                "quantity": quantity,
                "rate": item_details["rate"],
                "rate_with_gst": item_details["rate_with_gst"],
                "amount": item_details["amount"],
                "discount": item_details["discount"],
                "selling_price_list": item_details["price_list"],
                "uom": item_details["uom"]
            }
        )

        return api_response(True, "Item updated successfully")

    except Exception:
        frappe.log_error(frappe.get_traceback(), "update_cart_item")
        return api_response(False, "Error updating cart item")


@frappe.whitelist()
@validate_method(methods=["DELETE"])
def delete_cart_item():
    try:
        item = frappe.form_dict.get("item")

        if not item:
            return api_response(False, "Item required")

        user = frappe.session.user
        # Find row
        row_name = frappe.db.get_value("Cart Item", {"parent": user, "item": item}, "name")

        if not row_name:
            return api_response(False, "Item not found")

        # Delete directly
        frappe.db.delete("Cart Item", {"name": row_name})

        return api_response(True, "Item deleted")
    except Exception as e:
        frappe.log_error(f"Delete Cart Item Error: {frappe.get_traceback()}", "delete_cart_item")
        return api_response(False, str(e))

@frappe.whitelist()
@validate_method(methods=["GET"])
def cart_item_details():
    try:
        item = frappe.form_dict.get("item")

        if not item:
            return api_response(False, "Item required")

        user = frappe.session.user

        cart_item = frappe.db.get_value(
            "Cart Item",
            {
                "parent": user,
                "item": item
            },
            [
               "*"
            ],
            as_dict=True
        )

        if not cart_item:
            return api_response(False, "Item not found in cart")
        cleaned=clean_cart_item(cart_item)
        return api_response(
            True,
            "Cart item details fetched",
            cleaned
        )

    except Exception:
        frappe.log_error(frappe.get_traceback(), "cart_details")
        return api_response(False, "Error fetching cart item details")


def apply_custom_coupon_override(so, coupon_code):
    import frappe
    from frappe.utils import flt, today

    # 🔹 Fetch coupon
    coupon = frappe.db.get_value(
        "Custom Coupon",
        {"coupon_code": coupon_code, "enabled": 1},
        [
            "name",
            "discount_type",
            "discount",
            "maximum_discount_amount",
            "min_order_amount",
            "min_qty",
            "apply_discount_on",
            "customer_group",
            "valid_from",
            "valid_till",
            "max_usage_global",
            "usage_count",
            "per_user_limit"
        ],
        as_dict=True
    )

    if not coupon:
        return {"error": True, "message": "Invalid or disabled coupon code"}

    # 🔥 1. DATE VALIDATION
    today_date = today()

    if coupon.customer_group and so.customer_group != coupon.customer_group:
        return {"error": True, "message":f"Coupon not valid for {so.customer_group}"}
    if coupon.valid_from and today_date < str(coupon.valid_from):
        return {"error": True, "message": "Coupon not started yet"}

    if coupon.valid_till and today_date > str(coupon.valid_till):
        return {"error": True, "message": "Coupon expired"}

    # 🔥 2. GLOBAL USAGE LIMIT
    if coupon.max_usage_global and coupon.usage_count >= coupon.max_usage_global:
        return {"error": True, "message": "Coupon usage limit reached"}

    # 🔥 3. PER USER LIMIT
    user_usage = frappe.db.count(
        "Sales Order",
        {
            "custom_coupon_code_for_discount": coupon_code,
            "customer": so.customer,
            "docstatus": ["!=", 2]
        }
    )

    if coupon.per_user_limit and user_usage >= coupon.per_user_limit:
        return {"error": True, "message": "Coupon already used by this customer"}

    # 🔹 Quantity validation
    total_qty = sum(flt(i.qty) for i in so.items)

    if coupon.min_qty and total_qty < coupon.min_qty:
        return {
            "error": True,
            "message": f"Minimum quantity {coupon.min_qty} required"
        }

    # 🔹 Amount validation
    if coupon.min_order_amount and so.net_total < coupon.min_order_amount:
        return {
            "error": True,
            "message": f"Minimum order value ₹{coupon.min_order_amount} required"
        }

    # -------- CALCULATE DISCOUNT --------
    if coupon.apply_discount_on == "Grand Total":
        base_amount = so.grand_total
    else:
        base_amount = so.net_total

    if coupon.discount_type == "Amount":
        discount = flt(coupon.discount)
    else:
        discount = (base_amount * flt(coupon.discount)) / 100

    if coupon.maximum_discount_amount:
        discount = min(discount, flt(coupon.maximum_discount_amount))

    discount = flt(discount, 2)

    # -------- APPLY --------
    so.apply_discount_on = coupon.apply_discount_on or "Grand Total"
    so.discount_amount = discount
    so.additional_discount_percentage = 0
    so.custom_coupon_code_for_discount = coupon_code

    so.calculate_taxes_and_totals()

    return {
        "error": False,
        "code": coupon_code,
        "discount_type": coupon.discount_type,
        "discount_amount": discount
    }
    
from frappe.utils import flt

def get_item_price_summary(item_code, price_list, qty, company=None, customer=None, customer_group=None):
    # Fetch only necessary fields
    data = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list, "selling": 1},
        ["price_list_rate", "custom_full_payment", "custom_cod_display_rate", "custom_cash_on_delivery_"],
        as_dict=True
    )

    if not data:
        return None

    rate = flt(data.price_list_rate or 0)

    # FULL PAYMENT (always present)
    full_discount = rate - flt(data.custom_full_payment or 0) if data.custom_full_payment else 0

    # COD (optional)
    cod_discount = rate - flt(data.custom_cod_display_rate + data.custom_cash_on_delivery_ or 0 ) if data.custom_cod_display_rate else 0
    cod_basic= flt(data.custom_cod_display_rate or 0) + flt(data.custom_cash_on_delivery_ or 0)
    # Apply discount first, then calculate GST
    taxable_full = (rate - full_discount)
    taxable_cod = (rate - cod_discount)

    gst_data = get_item_price_withgst(
        item_code=item_code,
        customer=customer,
        customer_group=customer_group,
        company=company,
        qty=qty,
        currency=frappe.defaults.get_global_default("currency")
    )
    gst_rate = flt(gst_data.get("gst_rate") or 0)
    gst_full = flt(taxable_full * gst_rate / 100) * qty
    gst_cod = flt(taxable_cod * gst_rate / 100) * qty
    cod_discount_total=flt(cod_discount)+flt(cod_discount*gst_rate/100)
    cod_basic_total=flt(cod_basic*gst_rate/100)
    # Final totals including GST
    full_payment_total = (taxable_full * qty) + gst_full
    cod_total = (taxable_cod * qty) + gst_cod
    full_discount_total=flt(full_discount)+flt(full_discount *gst_rate/100)
    return {
        "full_discount_total": full_discount_total * qty,
"full_discount_total_without_gst": flt(full_discount or 0) * qty,        
"cod_discount_total": cod_discount_total * qty,
        "cod_discount_total_without_gst": cod_discount * qty,
        "cod_display_rate_total": flt(data.custom_cod_display_rate or 0) * qty,
        "cash_on_delivery": (flt(data.custom_cash_on_delivery_ or 0)+cod_basic_total) * qty,
        "full_payment_total": full_payment_total,
        "cod_total": cod_total
    }


def build_order_payment_summary(cart_items, so,total_discount):
    summary = {
        "original_amount": flt(so.rounded_total or so.grand_total, 2) + total_discount,
        "full_payment": {
            "payable_amount": flt(so.rounded_total or so.grand_total, 2),
            "discount_amount": total_discount,
            "label": f"₹ {flt(total_discount, 2)} Off"
        },
        "cash_on_delivery": None,
        "order_book_now": None
    }

    is_farmer = so.customer_group == "Farmer"
    show_cod_section = True
    full_discount_total = 0
    full_discount_total_without_gst=0
    cod_discount_total = 0
    cod_discount_total_without_gst=0
    cod_display_total = 0
    cash_on_delivery = 0
    full_payment_total = 0

    for item in cart_items:
        ip = get_item_price_summary(
            item_code=item.item,
            price_list=item.selling_price_list,
            qty=item.quantity,
            company=so.company,
            customer=so.customer,
            customer_group=so.customer_group
        )
        if not ip:
            continue

        if is_farmer:
            full_discount_total += flt(ip.get("full_discount_total", 0))
            full_discount_total_without_gst += flt(ip.get("full_discount_total_without_gst", 0))
            cod_discount_total += flt(ip.get("cod_discount_total", 0))
            cod_discount_total_without_gst += flt(ip.get("cod_discount_total_without_gst", 0))
            cod_display_total += flt(ip.get("cod_display_rate_total", 0))
            cash_on_delivery+= flt(ip.get("cash_on_delivery", 0))
            full_payment_total+= flt(ip.get("full_payment_total", 0))
            # Check per item: if any item's cod_display is 0 → hide COD section
            if flt(ip.get("cod_display_rate_total", 0)) == 0:
                show_cod_section = False
    # -------- FULL PAYMENT --------
    if is_farmer:
        payable = full_payment_total - total_discount
        summary["full_payment"] = {
            "payable_amount": flt(payable, 2),
            "discount_amount": flt(full_discount_total + total_discount, 2),
            "discount_amount_without_gst": flt(full_discount_total_without_gst +total_discount, 2),
            "coupen_discount": flt(total_discount, 2),
            "label": f"₹ {flt(full_discount_total, 2)} Off",
            "coupon_label":f"₹ {flt(total_discount, 2)} Off"
        }

    # -------- CASH ON DELIVERY --------
    if is_farmer and show_cod_section:
        summary["cash_on_delivery"] = {
                "pay_on_delivery": cash_on_delivery - total_discount,
                "pay_now": flt(cod_display_total, 2),
                "discount_amount": flt(cod_discount_total + total_discount, 2),
                "discount_amount_without_gst": flt(cod_discount_total_without_gst + total_discount, 2),
                "coupen_discount": flt(total_discount, 2),
                "label": f"₹ {flt(cod_discount_total, 2)} Off",
                "coupon_label": f"₹ {flt(total_discount, 2)} Off"
            }
    else:
        summary["cash_on_delivery"] = None  # hide COD section

    # -------- DEALER → ORDER BOOK NOW --------
    if not is_farmer:
        summary["order_book_now"] = {
            "payable_amount": flt(so.rounded_total or so.grand_total, 2) - total_discount,
            "discount_amount": total_discount,
            "label": f"₹ {flt(total_discount, 2)} Off"
        }

    return summary

# def get_item_price_summary(item_code, price_list, qty):
#     """
#     Returns per-item discount totals only (qty based)
#     """

#     data = frappe.db.get_value(
#     "Item Price",
#     {
#         "item_code": item_code,
#         "price_list": price_list,
#         "selling": 1
#     },
#     [
#         "price_list_rate",
#         "custom_full_payment_discount_type",
#         "custom_full_payment_discount_value",
#         "custom_cod_display_rate",
#         "custom_cod_discount_type",
#         "custom_cash_on_delivery_",
#         "custom_cod_discount_value"
#     ],
#     as_dict=True
#     )

#     if not data:
#         return None

#     # Base price = price_list_rate
#     rate = float(data.price_list_rate or 0)

#     # FULL PAYMENT
#     if data.custom_full_payment_discount_type == "Percentage":
#         full_payment_discount_total = (rate * float(data.custom_full_payment_discount_value or 0) / 100) * qty
#     else:
#         full_payment_discount_total = float(data.custom_full_payment_discount_value or 0) * qty

#     # COD discount
#     if data.custom_cod_discount_type == "Percentage":
#         cod_discount_total = (rate * float(data.custom_cod_discount_value or 0) / 100) * qty
#     else:
#         cod_discount_total = float(data.custom_cod_discount_value or 0) * qty

#     # COD display rate is usually absolute
#     cod_display_rate_total = float(data.custom_cod_display_rate or 0) * qty

#     return {
#         "full_payment_discount_total": full_payment_discount_total,
#         "cod_display_rate_total": cod_display_rate_total,
#         "cod_discount_total": cod_discount_total,
#         "cash_on_delivery":float(data.custom_cash_on_delivery_ or 0)
#     }

# from frappe.utils import flt

# def build_order_payment_summary(cart_item, so):
#     summary = {
#         "original_amount": flt(so.rounded_total or so.grand_total, 2),

#         "full_payment": {
#             "payable_amount": flt(so.rounded_total or so.grand_total, 2),
#             "discount_amount": 0,
#             "label": "₹ 0 Off"
#         },

#         "cash_on_delivery": None,
#         "order_book_now": None
#     }

#     # -------- IDENTIFY FARMER --------
#     is_farmer = so.customer_group == "Farmer"

#     full_discount_total = 0
#     cod_discount_total = 0
#     cod_display_total = 0

#     # -------- ITEM LEVEL CALCULATION --------
#     for item in cart_item:
#         ip = get_item_price_summary(
#             item_code=item.item,
#             price_list=item.selling_price_list,
#             qty=item.quantity
#         )
#         if not ip:
#             continue

#         if is_farmer:
#             full_discount_total += flt(ip.get("full_payment_discount_total", 0))
#             cod_discount_total += flt(ip.get("cod_discount_total", 0))
#             cod_display_total += flt(ip.get("cod_display_rate_total", 0))

#     # -------- FULL PAYMENT --------
#     if is_farmer:
#         payable = flt(so.rounded_total or so.grand_total) - full_discount_total
#         summary["full_payment"] = {
#             "payable_amount": flt(payable, 2),
#             "discount_amount": flt(full_discount_total, 2),
#             "label": f"₹ {flt(full_discount_total, 2)} Off"
#         }
#     else:
#         summary["full_payment"] = {
#             "payable_amount": flt(so.rounded_total or so.grand_total, 2),
#             "discount_amount": 0,
#             "label": "₹ 0 Off"
#         }
#     # -------- FARMER → CASH ON DELIVERY --------
#     if is_farmer:
#         if ip.get("cash_on_delivery") >0:
#             summary["cash_on_delivery"] = {
#                 "pay_on_delivery": flt(
#                     (so.rounded_total or so.grand_total) - cod_discount_total - cod_display_total, 2
#                 ),
#                 "pay_now": flt(cod_display_total, 2),
#                 "discount_amount": flt(cod_discount_total, 2),
#                 "label": f"₹ {flt(cod_discount_total, 2)} Off"
#             }
#         else:
#             summary["cash_on_delivery"] = {
#                 "pay_on_delivery": 0,
#                 "pay_now": flt(
#                     (so.rounded_total or so.grand_total) - cod_discount_total, 2
#                 ),
#                 "discount_amount": flt(cod_discount_total, 2),
#                 "label": f"₹ {flt(cod_discount_total, 2)} Off"
#             }

#     # -------- DEALER → ORDER BOOK NOW --------
#     if not is_farmer:
#         summary["order_book_now"] = {
#             "payable_amount": flt(so.rounded_total or so.grand_total, 2),
#             "discount_amount": 0,
#             "label": "₹ 0 Off"
#         }

#     return summary


from erpnext.accounts.doctype.pricing_rule.utils import (
	apply_pricing_rule_for_free_items,
	apply_pricing_rule_on_transaction,
	get_applied_pricing_rules,
)

def get_full_address_display(address_name):
    if not address_name:
        return ""

    addr = frappe.get_doc("Address", address_name)

    # Fetch display names
    marketplace_name = frappe.db.get_value(
        "Marketplace", addr.city, "marketplace_name"
    ) if addr.city else None

    tahsil_name = frappe.db.get_value(
        "Tahshil", addr.custom_tahshil, "tahshil"
    ) if addr.custom_tahshil else None

    district_name = frappe.db.get_value(
        "District", addr.custom_district, "district_name"
    ) if addr.custom_district else None

    parts = [
        addr.address_line1,
        addr.address_line2,
        marketplace_name,
        tahsil_name,
        district_name,
        addr.state,
        f"PIN Code: {addr.pincode}" if addr.pincode else None,
        addr.country,
        f"Phone: {addr.phone}" if addr.phone else None,
        f"Email: {addr.email_id}" if addr.email_id else None,
    ]

    parts = [p for p in parts if p]

    return "<br>".join(parts)


@frappe.whitelist()
@validate_method(methods=["POST"])
def proceed():
    import json
    from frappe.utils import flt, nowdate
    try:
        body = json.loads(frappe.request.data or "{}")
        frappe.flags.ignore_permissions = True
        items = body.get("items")
        warehouse = body.get("warehouse")
        transporter = body.get("transporter")
        delivery_date = body.get("delivery_date") or nowdate()
        coupon_code = body.get("coupon_code")

        # ---------------- VALIDATION ----------------
        if not items or not isinstance(items, list):
            return api_response(False, "Items must be a non-empty list")

        # ---------------- DEFAULT WAREHOUSE ----------------
        if not warehouse:
            warehouse = frappe.db.get_value(
                "Warehouse",
                {"custom_is_default_warehouse": 1},
                "name"
            )

        if not warehouse:
            return api_response(False, "Default warehouse not configured")

        # ---------------- DEFAULT TRANSPORTER ----------------
        if not transporter:
            transporter = frappe.db.get_value(
                "Supplier",
                {"custom_default_transporter": 1},
                "name"
            ) or ""

        # ---------------- COMPANY ADDRESS ----------------
        company_address = frappe.db.get_value(
            "Dynamic Link",
            {
                "link_doctype": "Warehouse",
                "link_name": warehouse
            },
            "parent"
        )

        # ---------------- CART ----------------
        user = frappe.session.user
        cart = frappe.get_doc("Shopping Cart", {"user": user})
        cart_item_map = {c.item: c for c in cart.items}

        # ---------------- SALES ORDER (DRAFT) ----------------
        so = frappe.new_doc("Sales Order")
        so.customer = cart.customer
        so.customer_group = cart.customer_group
        so.company = cart.company
        so.currency = cart.currency
        so.order_type = "Shopping Cart"
        so.company_address = company_address
        so.delivery_date = delivery_date
        so.set_warehouse = warehouse
        so.custom_transporter = transporter

        # ---------------- ITEMS ----------------
        for row in items:
            item_code = row.get("item")
            qty = flt(row.get("quantity"))

            cart_row = cart_item_map.get(item_code)
            if not cart_row or qty <= 0:
                continue
            
            so.append("items", {
                "item_code": item_code,
                "item_name": cart_row.item_name,
                "qty": qty,
                "rate": round(cart_row.rate, 2),
                "warehouse": warehouse,
                "delivery_date": delivery_date
            })

        if not so.items:
            return api_response(False, "No valid items found")
        customer_group = cart.customer_group

        min_order_value = frappe.db.get_value(
            "Customer Group",
            customer_group,
            "custom_min_sales_order_amount"
        ) or 0.0

        # Calculate order total (sum of qty * rate)
        order_total = sum([flt(row.get("quantity") or 0) * flt(cart_item_map[str(row.get("item"))].rate_with_gst)
                        for row in items if str(row.get("item")) in cart_item_map])

        
        frappe.set_user("Administrator")  # Run as admin to avoid permission issues during calculations
        # ---------------- INITIAL TOTALS ----------------
        so.set_missing_values()
        so.calculate_taxes_and_totals()

        # ---------------- COUPON ----------------
        coupon_discount = 0
        coupon_data = None

        if coupon_code:
            coupon_data = apply_custom_coupon_override(so, coupon_code)

            if coupon_data.get("error"):
                return api_response(False, coupon_data["message"])

            coupon_discount = flt(coupon_data.get("discount_amount") or 0)

            so.calculate_taxes_and_totals()

        # ---------------- PAYMENT DISCOUNT ----------------
        total_discount = flt(coupon_discount, 2)
        payment_summary = build_order_payment_summary(cart.items, so, total_discount)

        # payment_discount = payment_summary.get("full_payment", {}).get("discount_amount", 0)
        # ---------------- FINAL DISCOUNT ----------------
        # total_discount = flt(payment_discount + coupon_discount, 2)
      

        so.apply_discount_on = "Grand Total"
        so.discount_amount = total_discount
        so.additional_discount_percentage = 0

        # ---------------- FINAL CALCULATION ----------------
        so.disable_rounded_total = 0
        so.calculate_taxes_and_totals()

        # ✅ FORCE CLEAN ROUNDING
        so.grand_total = round(so.grand_total, 2)
        # ---------------- PAYMENT SUMMARY (FINAL) ----------------
        # payment_summary = build_order_payment_summary(cart.items, so)
        # payable_amount= payment_summary.get("original_amount")
        # if payable_amount < min_order_value:
        #     return api_response(
        #         False,
        #         f"Order total {payable_amount} is below minimum order value {min_order_value}",ispopup=True
        #     )
        AddressLine1, city, state, pincode, country=frappe.db.get_value("Address",so.shipping_address_name,["address_line1", "city", "state", "pincode", "country"])
        # ---------------- RESPONSE ----------------
        response = {
            "name": so.name,
            "currency": so.currency,
            "sub_total": flt(so.net_total, 2),
            "total_discount": total_discount,
            "total_taxes_and_charges": flt(so.total_taxes_and_charges, 2),
            "discount_amount": flt(so.discount_amount, 2),
            "additional_discount_percentage": flt(so.additional_discount_percentage, 2),
            "grand_total": flt(so.grand_total, 2) +total_discount if so.customer_group == "Farmer" else flt(so.grand_total, 2),
            "rounded_total": flt(so.rounded_total, 2),
            "in_words": frappe.utils.money_in_words(so.grand_total),
            "delivery_date": so.delivery_date,
            "warehouse": so.set_warehouse,
            "transporter": so.custom_transporter,
            "company": so.company,
            "company_address": so.company_address,
            "company_gstin": so.company_gstin,
            "place_of_supply": so.place_of_supply,
            "customer": so.customer,
            "customer_name": so.customer_name,
            "billing_address": so.customer_address,
"billing_address_display": get_full_address_display(so.customer_address),
"shipping_address": so.shipping_address_name,
"shipping_address_display": get_full_address_display(so.shipping_address_name),
             "shipping_address_details": {
        "address_line_1": AddressLine1,
        "city": city,
        "state": state,
        "pincode": pincode,
        "country": country
    },
            "gst_category": so.gst_category,
            "items": [
                {
                    "item_code": i.item_code,
                    "item_name": i.item_name,
                    "qty": flt(i.qty, 2),
                    "rate": flt(i.rate, 2),
                    "amount": flt(i.amount, 2),
                    "net_amount": flt(i.net_amount, 2),
                    "uom": i.uom,
                    "gst_hsn_code": i.gst_hsn_code,
                    "discount_percentage": flt(i.discount_percentage, 2),
                    "discount_amount": flt(i.discount_amount, 2),
                    "taxable_value": flt(i.taxable_value, 2)
                }
                for i in so.items
            ],
            "taxes": [
                {
                    "description": t.description,
                    "rate": flt(t.rate, 2),
                    "tax_amount": flt(t.tax_amount, 2)
                }
                for t in so.taxes
            ],
            "payment_summary": payment_summary,
            "coupon": coupon_data
        }
        return api_response(True, "Proceed successful", response)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "proceed")
        return api_response(False, "Proceed failed")


from frappe.utils import flt

def _get_allowed_price_list_for_user(user: str) -> str | None:
    # get all price lists allowed for this user (ignore "None")
    pls = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Price List",
            "for_value": ["not in", ["None", ""]]
        },
        pluck="for_value",
        order_by="modified desc"
    )
    return pls[0] if pls else None


def _set_price_list_fields(so, user: str):
    # 1) from user permission (your case)
    pl = _get_allowed_price_list_for_user(user)

    # 2) fallback from Customer default
    if not pl and so.customer:
        pl = frappe.db.get_value("Customer", so.customer, "default_price_list")

    # 3) fallback from Selling Settings default
    if not pl:
        pl = frappe.db.get_single_value("Selling Settings", "selling_price_list")

    if not pl:
        frappe.throw("Selling Price List is missing. Set User Permission or default in Selling Settings / Customer.")

    so.selling_price_list = pl

    # currency of price list
    so.price_list_currency = frappe.db.get_value("Price List", pl, "currency") or so.currency

    # conversion rate (price list currency -> company currency)
    company_currency = frappe.db.get_value("Company", so.company, "default_currency") or so.currency
    if so.price_list_currency == company_currency:
        so.plc_conversion_rate = 1.0
    else:
        # ERPNext utility
        from erpnext.setup.utils import get_exchange_rate
        so.plc_conversion_rate = flt(get_exchange_rate(so.price_list_currency, company_currency), 6) or 0

    if not so.plc_conversion_rate:
        frappe.throw(f"Missing conversion rate for {so.price_list_currency} → {company_currency}")




@frappe.whitelist()
@validate_method(methods=["POST"])
def place_order():
    import json
    from frappe.utils import flt

    try:
        body = json.loads(frappe.request.data or "{}")

        items = body.get("items")
        warehouse = body.get("warehouse")
        transporter = body.get("transporter")
        delivery_date = body.get("delivery_date") or frappe.utils.nowdate()
        coupon_code = body.get("coupon_code")
        payment_type = body.get("payment_type")
        transaction_amount = flt(body.get("transaction_amount") or 0)
        source= body.get("source")
        brand_ambassador = body.get("brand_ambassador")

        if not items or not isinstance(items, list):
            return api_response(False, "Items must be a list and cannot be empty")
        if brand_ambassador and not frappe.db.exists("Brand Ambassador", brand_ambassador):
            return api_response(False, "Invalid Brand Ambassador")
        # 🔒 Mandatory only for Order Book Now
        if payment_type == "Order Book Now" and transaction_amount <= 0:
            return api_response(False, "Transaction amount is required for Order Book Now")

        # -------- DEFAULT WAREHOUSE --------
        if not warehouse:
            warehouse = frappe.db.get_value(
                "Warehouse",
                {"custom_is_default_warehouse": 1},
                "name"
            )

        # -------- COMPANY ADDRESS --------
        company_address = frappe.db.get_value(
            "Dynamic Link",
            {"link_doctype": "Warehouse", "link_name": warehouse},
            "parent"
        )

        user = frappe.session.user
        cart = frappe.get_doc("Shopping Cart", {"user": user})
        cart_item_map = {str(c.item): c for c in cart.items}
        if brand_ambassador and cart.customer_group != "Farmer":
            return api_response(False, "Brand Ambassador can only be assigned for Farmer")
        # -------- SALES ORDER --------
        so = frappe.new_doc("Sales Order")
        so.customer = cart.customer
        so.customer_group = cart.customer_group
        so.company = cart.company
        so.currency = cart.currency
        so.order_type = "Shopping Cart"
        so.company_address = company_address
        so.delivery_date = delivery_date
        so.set_warehouse = warehouse
        so.custom_transporter = transporter
        so.custom_payment_type = payment_type
        so.custom_sales_order_source=source
        so.custom_brand_ambassador = brand_ambassador
        _set_price_list_fields(so, frappe.session.user)
        for row in items:
            item_key = str(row.get("item"))  # convert row item to string
            cart_row = cart_item_map.get(item_key)
            qty = flt(row.get("quantity") or 0)
            if not cart_row or qty <= 0:
                continue

            so.append("items", {
                "delivery_date": delivery_date,
                "item_code": cart_row.item,
                "item_name": cart_row.item_name,
                "qty": qty,
                "rate": round(cart_row.rate, 2),
                "warehouse": warehouse
            })

        if not so.items:
            return api_response(False, f"No valid items found of {frappe.session.user}")
        # --------- CHECK MINIMUM ORDER VALUE PER CUSTOMER GROUP ---------
        customer_group = cart.customer_group

        min_order_value = frappe.db.get_value(
            "Customer Group",
            customer_group,
            "custom_min_sales_order_amount"
        ) or 0.0

        # Calculate order total (sum of qty * rate)
        order_total = sum([flt(row.get("quantity") or 0) * flt(cart_item_map[str(row.get("item"))].rate_with_gst)
                        for row in items if str(row.get("item")) in cart_item_map])
        frappe.set_user("Administrator")
        # =====================================================
        # 🔹 BASE TOTALS
        # =====================================================
        so.set_missing_values()
        so.calculate_taxes_and_totals()
        
        # =====================================================
        # 🔥 COUPON DISCOUNT
        # =====================================================
        coupon_discount = 0
        if coupon_code:
            coupon_data = apply_custom_coupon_override(so, coupon_code)

            if coupon_data.get("error"):
                return api_response(False, coupon_data["message"])

            coupon_discount = flt(coupon_data.get("discount_amount") or 0)

            # ✅ MUST recalculate after coupon
            so.calculate_taxes_and_totals()

        # =====================================================
        # 🔥 PAYMENT DISCOUNT
        # =====================================================
        payment_discount = 0
        so.custom_pay_on_proceed_order = 0
        payable_amount = 0
        payment_summary = build_order_payment_summary(cart.items, so,coupon_discount)
        if payment_type == "Full Payment":
            payable_amount= payment_summary["full_payment"]["payable_amount"]
        elif payment_type == "Cash On Delivery" and payment_summary.get("cash_on_delivery"):
            payable_amount = payment_summary["cash_on_delivery"]["pay_now"] + payment_summary["cash_on_delivery"]["pay_on_delivery"]
        elif payment_type == "Order Book Now" and payment_summary.get("order_book_now"):
            payable_amount = payment_summary["order_book_now"]["payable_amount"]
        if payable_amount < min_order_value:
            return api_response(
                False,
                f"Order total {payable_amount} is below minimum order value {min_order_value}",ispopup=True
            )
        if payment_type == "Full Payment":
            payment_discount = payment_summary["full_payment"].get("discount_amount", 0)
            so.custom_pay_on_proceed_order = payment_summary["full_payment"].get("payable_amount", 0)
            so.custom_coupon_discount_amount = payment_summary["full_payment"].get("coupen_discount", 0)
        elif payment_type == "Cash On Delivery" and payment_summary.get("cash_on_delivery"):
            payment_discount = payment_summary["cash_on_delivery"].get("discount_amount", 0)
            so.custom_pay_on_proceed_order = payment_summary["cash_on_delivery"].get("pay_now", 0)
            so.custom_coupon_discount_amount = payment_summary["cash_on_delivery"].get("coupen_discount", 0)
        elif payment_type == "Order Book Now" and payment_summary.get("order_book_now"):
            if transaction_amount > so.grand_total:
                return api_response(False, "Advance amount cannot exceed order total")
            payment_discount = payment_summary["order_book_now"].get("discount_amount", 0)
            # ❗ MUST REMAIN UNCHANGED
            so.custom_pay_on_proceed_order = payment_summary["order_book_now"]["payable_amount"]

        so.custom_coupon_code_for_discount = coupon_code
        so.ignore_pricing_rule = 1
        so.apply_discount_on = "Grand Total"
        so.discount_amount = payment_discount
        so.additional_discount_percentage = 0
        so.disable_rounded_total=0
        so.calculate_taxes_and_totals()

        # -------- REMOVE PAYMENT SCHEDULE --------
        so.payment_terms_template = ""
        so.payment_schedule = []
        frappe.set_user(frappe.session.user)  # Set back to original user for permissions
        # -------- INSERT --------
        so.insert(ignore_permissions=True)
        so.submit()
        AddressLine1, city, state, pincode, country=frappe.db.get_value("Address",so.shipping_address_name,["address_line1", "city", "state", "pincode", "country"])
        current_count = frappe.db.get_value("Custom Coupon", coupon_code, "usage_count") or 0

        frappe.db.set_value(
            "Custom Coupon",
            coupon_code,
            "usage_count",
            current_count + 1
        )
        # -------- CLEAR CART --------
        frappe.db.delete(
            "Cart Item",
            {
                "parent": cart.name,
                "item": ["in", [i.get("item") for i in items]]
            }
        )

        # -------- GRAND TOTAL FOR RESPONSE --------
        if payment_type == "Cash On Delivery":
            payable_total = (so.rounded_total or so.grand_total) - so.custom_pay_on_proceed_order
        else:
            payable_total = (so.rounded_total or so.grand_total)

        return api_response(True, "Order placed successfully", {
            "sales_order": so.name,
            "status": so.status,
            "source": so.custom_sales_order_source,
            "brand_ambassador": so.custom_brand_ambassador,
            "grand_total": round(payable_total, 2),
            "shipping_address_details": {
                "address_line_1": AddressLine1,
                "city": city,
                "state": state,
                "pincode": pincode,
                "country": country
            },
            # ✅ RESPONSE FIX (ONLY HERE)
            "transaction_amount": round(
                transaction_amount if payment_type == "Order Book Now"
                else so.custom_pay_on_proceed_order,
                2
            ),
            "discount_amount": round(so.discount_amount or 0, 2),
            "coupon_discount": round(coupon_discount or 0, 2),
            "payment_discount": round(payment_discount or 0, 2)
        })

    except Exception:
        frappe.log_error(frappe.get_traceback(), "place_order")
        return api_response(False, "Order placement failed")
    
    
@frappe.whitelist()
@validate_method(methods=["GET"])
def checkout_details():
    try:
        user = frappe.session.user
        cart = frappe.get_doc("Shopping Cart", {"user": user})
        args={"party_type": "Customer", "party": cart.customer, "company": cart.company,"doctype":"Sales Order"}
        party=get_party_details(**args,ignore_permissions=True)
        cleaned = [clean_cart_item(r) for r in cart.items]
        party_deatils={
            "customer":party.get("customer"),
            "customer_name":party.get("customer_name"),
            "customer_group":party.get("customer_group"),
            "customer_gstin":frappe.db.get_value("Customer",party.get("customer"),"gstin") or None,
            "billing_address":party.get("customer_address"),
            "billing_address_display":get_full_address_display(party.get("customer_address")),
            "shipping_address":party.get("shipping_address_name"),
            "shipping_address_display":get_full_address_display(party.get("shipping_address_name")),
            "company_address": party.get("company_address"),
            "company_gstin": party.get("company_gstin"),
             "place_of_supply": party.get("place_of_supply"),
             "items":cleaned
        }
        return api_response(True, "Items marked for checkout", party_deatils)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "checkout_items")
        return api_response(False, "Error marking items for checkout")
@frappe.whitelist()
@validate_method(methods=["GET"])
def get_customer_shipping_address():
    try:
        customer = get_customer_from_user()

        filters = [
            ["Dynamic Link", "link_doctype", "=", "Customer"],
            ["Dynamic Link", "link_name", "=", customer],
            ["Address", "address_type", "=", "Shipping"]
        ]

        address_list = frappe.get_list(
            "Address",
            filters=filters,
            fields=[
                "name",
                "gstin",
                "email_id",
                "phone",
                "is_shipping_address",
                "address_title",
                "address_line1",
                "address_line2",
                "city",
                "custom_tahshil",
                "custom_district",
                "state",
                "pincode",
                "country"
            ]
        )

        if not address_list:
            return api_response(True, "Shipping address fetched", [])

        from frappe.contacts.doctype.address.address import (
            get_address_templates,
            get_address_display
        )

        shipping_address = []

        for addr in address_list:

            # 🔥 Fetch display names ONLY for template rendering
            marketplace_name = (
                frappe.db.get_value("Marketplace", addr.city, "marketplace_name")
                if addr.city else None
            )

            tahsil_name = (
                frappe.db.get_value("Tahshil", addr.custom_tahshil, "tahshil")
                if addr.custom_tahshil else None
            )

            district_name = (
                frappe.db.get_value("District", addr.custom_district, "district_name")
                if addr.custom_district else None
            )

            # Copy original dict and replace only for display
            display_dict = addr.copy()
            display_dict["city"] = marketplace_name
            display_dict["custom_tahshil"] = tahsil_name
            display_dict["custom_district"] = district_name

            # Build custom formatted address manually

            address_parts = [
                addr.address_line1,
                addr.address_line2,
                marketplace_name,
                tahsil_name,
                district_name,
                addr.state,
                f"PIN Code: {addr.pincode}" if addr.pincode else None,
                addr.country,
                f"Phone: {addr.phone}" if addr.phone else None,
                f"Email: {addr.email_id}" if addr.email_id else None,
            ]

            # Remove empty values
            address_parts = [part for part in address_parts if part]

            # HTML format
            html_output = "<br>".join(address_parts)

            # Text format
            display_text = "\n".join(address_parts)


            # ✅ Keep original IDs in response
            shipping_address.append({
                "name": addr.name,
                "gstin": addr.gstin,
                "email_id": addr.email_id,
                "phone": addr.phone,
                "html": html_output,
                "display_text": display_text,
                "is_primary": addr.is_shipping_address or 0,
                "address_title": addr.address_title or "",
                "address_line1": addr.address_line1,
                "address_line2": addr.address_line2 or "",
                "marketplace": addr.city,                # ID kept
                "tahsil": addr.custom_tahshil,           # ID kept
                "district": addr.custom_district,        # ID kept
                "state": addr.state,
                "pincode": addr.pincode,
                "country": addr.country or "India",
            })

        return api_response(True, "Shipping address fetched", shipping_address)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_customer_shipping_address")
        return api_response(False, "Error fetching shipping address")


@frappe.whitelist()
@validate_method(methods=["POST"])
def add_customer_shipping_address():
    try:
        body = json.loads(frappe.request.data or "{}")

        # Extract fields
        address_title = body.get("address_title", "")
        address_line1 = body.get("address_line1")
        address_line2 = body.get("address_line2", "")
        city = body.get("marketplace")
        tahshil = body.get("tahsil", "")
        district = body.get("district", "")
        state = body.get("state")
        pincode = body.get("pincode")
        email_id = body.get("email_id", "")
        phone = body.get("phone", "")
        country = body.get("country", "India")

        # Mandatory fields check
        if not address_line1 or not city or not state or not pincode:
            return api_response(False, "Mandatory address fields are missing")

        customer = get_customer_from_user()

        # 🔍 Check if customer already has a Shipping Address
        has_shipping_address = frappe.db.exists(
            "Address",
            {
                "address_type": "Shipping",
                "name": ["in", frappe.get_all(
                    "Dynamic Link",
                    filters={
                        "link_doctype": "Customer",
                        "link_name": customer
                    },
                    pluck="parent"
                )]
            }
        )

        # 🟢 First address → make it primary
        is_primary = 0 if has_shipping_address else 1

        # Create Address Document
        address_doc = frappe.get_doc({
            "doctype": "Address",
            "address_type": "Shipping",
            "address_line1": address_line1,
            "address_line2": address_line2,
            "custom_tahshil": tahshil,
            "custom_district": district,
            "city": city,
            "state": state,
            "email_id": email_id,
            "phone": phone,
            "address_title": address_title,
            "country": country,
            "pincode": pincode,
            "is_shipping_address": is_primary,
            "links": [{
                "link_doctype": "Customer",
                "link_name": customer
            }]
        })

        address_doc.insert(ignore_permissions=True)

        # Response
        response_data = {
            "name": address_doc.name,
            "address_title": address_doc.address_title,
            "address_line1": address_doc.address_line1,
            "address_line2": address_doc.address_line2,
            "marketplace": address_doc.city,
            "tahsil": address_doc.custom_tahshil,
            "district": address_doc.custom_district,
            "state": state,
            "pincode": pincode,
            "country": country,
            "email_id": email_id,
            "phone": phone,
            "is_primary": is_primary
        }

        return api_response(True, "Shipping address added", response_data)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "add_customer_shipping_address")
        return api_response(False, "Error adding shipping address")



@frappe.whitelist()
@validate_method(methods=["PUT"])
def update_customer_shipping_address():
    try:
        body = json.loads(frappe.request.data or "{}")

        name = body.get("name")
        if not name:
            return api_response(False, "Address name is required")

        # Load existing Address
        address_doc = frappe.get_doc("Address", name)

        # Extract fields
        address_title = body.get("address_title", "")
        address_line1 = body.get("address_line1")
        address_line2 = body.get("address_line2", "")
        city = body.get("marketplace")
        tahshil = body.get("tahsil", "")
        district = body.get("district", "")
        state = body.get("state")
        pincode = body.get("pincode")
        email_id = body.get("email_id", "")
        phone = body.get("phone", "")
        country = body.get("country", "India")

        # Mandatory check
        if not address_line1 or not city or not state or not pincode:
            return api_response(False, "Mandatory address fields are missing")

        # Update fields
        address_doc.address_title = address_title
        address_doc.address_line1 = address_line1
        address_doc.address_line2 = address_line2
        address_doc.custom_tahshil = tahshil
        address_doc.custom_district = district
        address_doc.city = city
        address_doc.state = state
        address_doc.email_id = email_id
        address_doc.phone = phone
        address_doc.country = country
        address_doc.pincode = pincode

        address_doc.save(ignore_permissions=True)

        # Clean response
        response_data = {
            "name": address_doc.name,
            "address_title": address_doc.address_title,
            "address_line1": address_doc.address_line1,
            "address_line2": address_doc.address_line2,
            "marketplace": address_doc.city,
            "tahsil": address_doc.custom_tahshil,
            "district": address_doc.custom_district,
            "state": address_doc.state,
            "pincode": address_doc.pincode,
            "country": address_doc.country,
            "email_id": address_doc.email_id,
            "phone": address_doc.phone,
        }

        return api_response(True, "Shipping address updated", response_data)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "update_customer_shipping_address")
        return api_response(False, "Error updating shipping address")


@frappe.whitelist()
@validate_method(methods=["DELETE"])
def delete_customer_shipping_address():
    try:
        body = json.loads(frappe.request.data or "{}")

        name = body.get("name")

        if not name:
            return api_response(False, "Address name is required")

        # Check if address exists
        if not frappe.db.exists("Address", name):
            return api_response(False, "Address not found")

        # Optional: Verify user owns this address (if required)
        customer = get_customer_from_user()
        # If Address is linked, you can add additional checks here

        frappe.delete_doc("Address", name, ignore_permissions=True)

        return api_response(True, "Shipping address deleted successfully", {"name": name})

    except Exception:
        frappe.log_error(frappe.get_traceback(), "delete_customer_shipping_address")
        return api_response(False, f"Error deleting shipping address {frappe.get_traceback()}")


@frappe.whitelist()
@validate_method(methods=["PUT"])
def make_primary_shipping_address():
    try:
        body = json.loads(frappe.request.data or "{}")
        name = body.get("name")

        if not name:
            return api_response(False, "Address name is required")

        # Check if the address exists
        if not frappe.db.exists("Address", name):
            return api_response(False, "Address not found")

        customer = get_customer_from_user()

        if not customer:
            return api_response(False, "Customer not found")
        filters = [
            ["Dynamic Link", "link_doctype", "=", "Customer"],
            ["Dynamic Link", "link_name", "=", customer],
            ["Address", "address_type", "=", "Shipping"]
        ]
        # 1️⃣ Get all addresses of this customer
        address_list = frappe.get_all(
            "Address",
            filters=filters,
            fields=["name"]
        )

        # 2️⃣ Set all addresses to non-primary first
        for addr in address_list:
            frappe.db.set_value("Address", addr.name, "is_shipping_address", 0)

       # ✅ Fetch needed fields once
        addr = frappe.db.get_value(
            "Address",
            name,                    # use address_name consistently
            ["city", "custom_tahshil"],
            as_dict=True
        ) or {}

        # ✅ Update Address + Customer in minimal calls
        frappe.db.set_value("Address", name, "is_shipping_address", 1, update_modified=False)

        # Batch customer updates in ONE call (faster than 3 separate set_value)
        customer_updates = {
            "customer_primary_address": name,
            # "custom_tahsil": addr.get("custom_tahshil"),
            # "custom_marketplace": addr.get("city"),
        }
        frappe.db.set_value("Customer", customer, customer_updates, update_modified=False)

        return api_response(True, "Primary shipping address updated", {
            "primary_address": name
        })

    except Exception:
        frappe.log_error(frappe.get_traceback(), "make_primary_shipping_address")
        return api_response(False, f"Error making primary shipping address {frappe.get_traceback()}")

@frappe.whitelist()
@validate_method(methods=["GET"])
def get_warehouse_list():

    try:
        # -----------------------------------------
        # 1. Get customer from logged-in user
        # -----------------------------------------
        customer = get_customer_from_user()
        if not customer:
            return api_response(False, "Customer not found for this user")

        # -----------------------------------------
        # 2. Get shipping address of customer
        # -----------------------------------------
        filters = [
            ["Dynamic Link", "link_doctype", "=", "Customer"],
            ["Dynamic Link", "link_name", "=", customer],
            ["Address", "address_type", "=", "Shipping"],
            ["Address","is_shipping_address","=",1]
        ]
        shipping_address = frappe.db.get_value(
            "Address",
            filters,
            "name"
        )
        # -----------------------------------------
        # 3. Get city from address (optional now)
        # -----------------------------------------
        city = None
        if shipping_address:
            city = frappe.db.get_value("Address", shipping_address, "city")

        warehouse_list = []

        # -----------------------------------------
        # 4. Get warehouses mapped to same city
        # -----------------------------------------
        if city:
            warehouse_names = frappe.get_all(
                "Warehouse Marketplaces",
                filters={"marketplace": city},
                pluck="parent"
            )
            if warehouse_names:
                warehouse_list = frappe.get_all(
                    "Warehouse",
                    filters={
                        "name": ["in", warehouse_names],
                        "is_group": 0,
                        "disabled": 0,
                        "is_rejected_warehouse": 0,
                        "custom_is_mobile_app_warehouse": 1,
                        "company": get_global_defaults().get("default_company")
                    },
                    pluck="name"
                )

        # -----------------------------------------
        # 5. FALLBACK → Default Warehouse
        # -----------------------------------------
        if not warehouse_list:
            default_warehouse = frappe.db.get_value(
                "Warehouse",
                {"custom_is_default_warehouse":1},"name"
            )

            if default_warehouse:
                warehouse_list = [default_warehouse]

        return api_response(True, "Warehouse list fetched", warehouse_list)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_warehouse_list")
        return api_response(False, "Error fetching warehouse list")

@frappe.whitelist()
@validate_method(methods=["GET"])
def get_transporter_list():
    try:
        # GET params (fallback body if sent)
        body = {}
        try:
            body = json.loads(frappe.request.data or "{}")
        except Exception:
            body = {}

        warehouse = frappe.form_dict.get("warehouse") or body.get("warehouse")
        customer = get_customer_from_user()
        if not customer:
            return api_response(False, "Customer not found for this user")

        # 1) Resolve warehouse
        if not warehouse:
            warehouse = frappe.db.get_value(
                "Warehouse",
                {"custom_is_default_warehouse": 1},
                "name"
            )

        if not warehouse or not frappe.db.exists("Warehouse", warehouse):
            return api_response(False, "Warehouse not found")

        # 2) Get customer city (shipping)
        customer_city = frappe.db.get_value(
            "Address",
            {
                "name": [
                    "in",
                    frappe.get_all(
                        "Dynamic Link",
                        filters={
                            "link_doctype": "Customer",
                            "link_name": customer,
                            "parenttype": "Address"
                        },
                        pluck="parent"
                    )
                ],
                "is_shipping_address": 1,
                "disabled": 0
            },
            "city"
        )

        if not customer_city:
            return api_response(False, "Customer shipping city not found")

        # 3) Transporters assigned to this warehouse (Supplier names)
        warehouse_transporters = frappe.get_all(
            "Transporter Assign Warehouse",
            filters={"warehouse": warehouse},
            pluck="transporter"
        ) or []

        # If none assigned, only default transporter will come (below)
        valid_transporters = []

        # 4) Filter those transporters by "transporters marketplaces" = customer_city
        if warehouse_transporters:
            valid_transporters = frappe.get_all(
                "transporters marketplaces",     # <-- your table doctype
                filters={
                    "parent": ["in", warehouse_transporters],  # parent = Supplier
                    "marketplace": customer_city
                },
                pluck="parent",
                distinct=True
            ) or []

        # 5) Fetch Supplier details
        transporter_list = []
        if valid_transporters:
            transporter_list = frappe.get_all(
                "Supplier",
                filters={
                    "name": ["in", valid_transporters],
                    "is_transporter": 1,
                    "disabled": 0
                },
                fields=["name", "supplier_name"]
            )

        # 6) Always include default transporter
        default_transporter = frappe.db.get_value(
            "Supplier",
            {"custom_default_transporter": 1, "is_transporter": 1, "disabled": 0},
            ["name", "supplier_name"],
            as_dict=True
        )

        if default_transporter:
            existing = {t["name"] for t in transporter_list}
            if default_transporter["name"] not in existing:
                transporter_list.append(default_transporter)

        return api_response(True, "Transporter list fetched", transporter_list)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_transporter_list")
        return api_response(False, "Error fetching Transporter list")


@frappe.whitelist()
@validate_method(methods=["GET"])
def get_transporter_list_update():
    try:
        # GET params (fallback body if sent)
        body = {}
        try:
            body = json.loads(frappe.request.data or "{}")
        except Exception:
            body = {}

        warehouse = frappe.form_dict.get("warehouse") or body.get("warehouse")
        customer = get_customer_from_user()
        if not customer:
            return api_response(False, "Customer not found for this user")

        # 1) Resolve warehouse
        if not warehouse:
            warehouse = frappe.db.get_value(
                "Warehouse",
                {"custom_is_default_warehouse": 1},
                "name"
            )

        if not warehouse or not frappe.db.exists("Warehouse", warehouse):
            return api_response(False, "Warehouse not found")

        # 2) Get customer city (shipping)
        customer_city = frappe.db.get_value(
            "Address",
            {
                "name": [
                    "in",
                    frappe.get_all(
                        "Dynamic Link",
                        filters={
                            "link_doctype": "Customer",
                            "link_name": customer,
                            "parenttype": "Address"
                        },
                        pluck="parent"
                    )
                ],
                "is_shipping_address": 1,
                "disabled": 0
            },
            "city"
        )

        if not customer_city:
            return api_response(False, "Customer shipping city not found")

        # 3) Transporters assigned to this warehouse (Supplier names)
        warehouse_transporters = frappe.get_all(
            "Transporter Assign Warehouse",
            filters={"warehouse": warehouse},
            pluck="transporter"
        ) or []

        # If none assigned, only default transporter will come (below)
        valid_transporters = []

        # 4) Filter those transporters by "transporters marketplaces" = customer_city
        if warehouse_transporters:
            valid_transporters = frappe.get_all(
                "transporters marketplaces",     # <-- your table doctype
                filters={
                    "parent": ["in", warehouse_transporters],  # parent = Supplier
                    "marketplace": customer_city
                },
                pluck="parent",
                distinct=True
            ) or []

        # 5) Fetch Supplier details
        transporter_list = []
        if valid_transporters:
            transporter_list = frappe.get_all(
                "Supplier",
                filters={
                    "name": ["in", valid_transporters],
                    "is_transporter": 1,
                    "disabled": 0
                },
                fields=["name", "supplier_name"]
            )

        # 6) Always include default transporter
        default_transporter = frappe.db.get_value(
            "Supplier",
            {"custom_default_transporter": 1, "is_transporter": 1, "disabled": 0},
            ["name", "supplier_name"],
            as_dict=True
        )

        if default_transporter:
            existing = {t["name"] for t in transporter_list}
            if default_transporter["name"] not in existing:
                transporter_list.append(default_transporter)

        return api_response(True, "Transporter list fetched", transporter_list)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_transporter_list_update")
        return api_response(False, "Error fetching Transporter list")
    
    

# @frappe.whitelist()
# @validate_method(methods=["GET"])
# def get_order_from_list(order_id=None, from_date=None, to_date=None, page=1, page_size=20):
#     try:
#         customer = get_customer_from_user()

#         filters = {
#             "customer": customer,
#             "order_type": "Shopping Cart"
#         }

#         if not frappe.db.exists("Customer", customer):
#             return api_response(False, "Customer not found")

#         user_type = frappe.db.get_value("Customer", customer, "customer_group")

#         page = cint(page) or 1
#         page_size = cint(page_size) or 20
#         start = (page - 1) * page_size

#         if order_id:
#             filters["name"] = ["like", f"%{order_id}%"]

#         if bool(from_date) ^ bool(to_date):
#             return api_response(False, "Both from_date and to_date are required")

#         if from_date and to_date:
#             filters["transaction_date"] = ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]]

#         total_records = frappe.db.count("Sales Order", filters)

#         orders = frappe.get_all(
#             "Sales Order",
#             filters=filters,
#             fields=[
#                 "name", "transaction_date",
#                 "grand_total", "advance_paid",
#                 "docstatus", "custom_dispatch_status",
#                 "custom_payment_type",
#                 "custom_pay_on_proceed_order",
#                 "shipping_address_name"
#             ],
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="transaction_date desc"
#         )

#         if not orders:
#             return api_response(True, "No records found", {"data": []})

#         order_ids = [o.name for o in orders]

#         # ---------------------------------------------------
#         # 🔥 BULK FETCH ALL PAYMENTS
#         # ---------------------------------------------------
#         frappe.log_error(title="Order IDs for payment fetch", message=str(order_ids))
#         # Payment Link + PG txn mapping
#         txn_map = frappe._dict()
#         for r in frappe.get_all(
#             "Payment Link",
#             filters={"order_id": ["in", order_ids]},
#             fields=["order_id", "transactionid"]
#         ):
#             if r.transactionid:
#                 txn_map.setdefault(r.order_id, []).append(r.transactionid)
#         frappe.log_error(title="Payment Link Txn Map", message=str(txn_map))
#         for r in frappe.get_all(
#             "Payment Gateway Transaction",
#             filters={"order_id": ["in", order_ids]},
#             fields=["order_id", "txn_id"]
#         ):
#             if r.txn_id:
#                 txn_map.setdefault(r.order_id, []).append(r.txn_id)
#         frappe.log_error(title="Payment Gateway Txn Map", message=str(txn_map))
#         all_txns = list(set([t for v in txn_map.values() for t in v]))
#         frappe.log_error(title="All Txns", message=str(all_txns))
#         # PayU success amounts
#         payu_map = dict(frappe.db.sql("""
#         SELECT txnid, SUM(amount)
#         FROM `tabPayU Response`
#         WHERE status = 'success'
#         AND txnid IN %(txns)s
#         GROUP BY txnid
#     """, {
#         "txns": tuple(all_txns)  # ⚠️ MUST be tuple
#     }))

#         # Bank Approved
#         bank_map = frappe._dict(
#             frappe.db.sql("""
#                 SELECT sales_order, SUM(amount)
#                 FROM `tabBank Transfer Request`
#                 WHERE docstatus=1 AND status="Approved"
#                 GROUP BY sales_order
#             """)
#         )

#         # Bank Draft (pending)
#         bank_pending_map = frappe._dict(
#             frappe.db.sql("""
#                 SELECT sales_order, SUM(amount)
#                 FROM `tabBank Transfer Request`
#                 WHERE docstatus=0 AND status="Unsettled"
#                 GROUP BY sales_order
#             """)
#         )

#         # Rupifi
#         rupifi_map = frappe._dict(
#             frappe.db.sql("""
#                 SELECT order_id, SUM(amount_value)
#                 FROM `tabRupifi Webhook Log`
#                 WHERE status='CAPTURED'
#                 GROUP BY order_id
#             """)
#         )

#         # Van Transactions
#         van_map = frappe._dict(
#             frappe.db.sql("""
#                 SELECT sales_order, SUM(transaction_amount)
#                 FROM `tabVan Transactions`
#                 WHERE transaction_status='Approved'
#                 GROUP BY sales_order
#             """)
#         )

#         # Journal Entry
#         je_map = frappe._dict(
#             frappe.db.sql("""
#                 SELECT jea.reference_name, SUM(jea.credit)
#                 FROM `tabJournal Entry` je
#                 JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
#                 WHERE jea.reference_type = 'Sales Order'
#                 AND je.docstatus = 1
#                 GROUP BY jea.reference_name
#             """)
#         )

#         # ---------------------------------------------------
#         # 🧠 BUILD RESPONSE
#         # ---------------------------------------------------

#         result = []

#         for so in orders:
#             total = float(so.grand_total or 0)

#             # -----------------------------
#             # ✅ RECEIVED CALCULATION
#             # -----------------------------
#             received = 0

#             # PayU
#             for txn in txn_map.get(so.name, []):
#                 received += float(payu_map.get(txn, 0) or 0)

#             # Others
#             received += float(bank_map.get(so.name, 0) or 0)
#             received += float(rupifi_map.get(so.name, 0) or 0)
#             received += float(van_map.get(so.name, 0) or 0)
#             received += float(je_map.get(so.name, 0) or 0)

#             # Bank pending
#             bank_pending = float(bank_pending_map.get(so.name, 0) or 0)

#             # -----------------------------
#             # ✅ PENDING
#             # -----------------------------
#             pending = max(round(total - (received + bank_pending), 2), 0)

#             # -----------------------------
#             # ✅ STATUS
#             # -----------------------------
#             if so.docstatus == 2:
#                 status = "Cancelled"
#                 pending = 0

#             elif (so.custom_dispatch_status or "").lower() == "refunded":
#                 status = "Refunded"
#                 pending = 0

#             elif received <= 0:
#                 status = "Pending"

#             elif pending == 0:
#                 status = "Fully Paid"

#             else:
#                 status = "Partially Paid"

#             # -----------------------------
#             # ✅ ALLOWED ACTION
#             # -----------------------------
#             if so.docstatus == 2 or status == "Refunded":
#                 allowed_action = "none"
#             else:
#                 if pending == 0:
#                     allowed_action = "none"
#                 elif pending == total:
#                     allowed_action = "cancel"
#                 else:
#                     allowed_action = "map"

#             # -----------------------------
#             # ✅ ADDRESS
#             # -----------------------------
#             AddressLine1, city, state, pincode, country = frappe.db.get_value(
#                 "Address",
#                 so.shipping_address_name,
#                 ["address_line1", "city", "state", "pincode", "country"]
#             ) if so.shipping_address_name else ("", "", "", "", "")

#             result.append({
#                 "order_id": so.name,
#                 "date": frappe.utils.format_datetime(so.transaction_date) if so.transaction_date else None,
#                 "total_amount": total,
#                 "received_amount": received,
#                 "pending_amount": pending,
#                 "status": status,
#                 "docstatus": so.docstatus,
#                 "allowed_action": allowed_action,
#                 "payupreferedamount": so.custom_pay_on_proceed_order,
#                 "payupreferedmode": so.custom_payment_type,
#                 "user_type": user_type,
#                 "shipping_address_details": {
#                     "address_line_1": AddressLine1,
#                     "city": city,
#                     "state": state,
#                     "pincode": pincode,
#                     "country": country
#                 },
#             })

#         total_pages = (total_records + page_size - 1) // page_size

#         return api_response(True, "Sales orders fetched", {
#             "total": total_records,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": result
#         })

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "get_order_from_list")
#         return api_response(False, "Error fetching sales orders")
    
@frappe.whitelist()
@validate_method(methods=["GET"])
def get_order_from_list(order_id=None, from_date=None, to_date=None, page=1, page_size=20):
    try:
        customer = get_customer_from_user()

        if not frappe.db.exists("Customer", customer):
            return api_response(False, "Customer not found")

        filters = {
            "customer": customer,
            "order_type": "Shopping Cart"
        }

        user_type = frappe.db.get_value("Customer", customer, "customer_group")

        page = cint(page) or 1
        page_size = cint(page_size) or 20
        start = (page - 1) * page_size

        if order_id:
            filters["name"] = ["like", f"%{order_id}%"]

        # Validate input
        if bool(from_date) ^ bool(to_date):
            return api_response(False, "Both from_date and to_date are required")

        static_from_date = "2025-04-01"

        if from_date and to_date:
            # override from_date if it's older
            if from_date < static_from_date:
                from_date = static_from_date

            filters["transaction_date"] = [
                "between",
                [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            ]
        else:
            # if no date given, still enforce static filter
            filters["transaction_date"] = [">=", f"{static_from_date} 00:00:00"]

        total_records = frappe.db.count("Sales Order", filters)

        orders = frappe.get_all(
            "Sales Order",
            filters=filters,
            fields=[
                "name", "transaction_date","rounded_total",
                "grand_total", "advance_paid",
                "docstatus", "custom_dispatch_status",
                "custom_payment_type",
                "custom_pay_on_proceed_order",
                "shipping_address_name"
            ],
            limit_start=start,
            limit_page_length=page_size,
            order_by="transaction_date desc"
        )

        if not orders:
            return api_response(True, "No records found", {"data": []})

        order_ids = [o.name for o in orders]

        # ---------------------------------------------------
        # 🔥 PAYMENT TXN MAP
        # ---------------------------------------------------

        txn_map = {}

        for r in frappe.get_all(
            "Payment Link",
            filters={"order_id": ["in", order_ids]},
            fields=["order_id", "transactionid"]
        ):
            if r.transactionid:
                txn_map.setdefault(r.order_id, []).append(r.transactionid)

        for r in frappe.get_all(
            "Payment Gateway Transaction",
            filters={"order_id": ["in", order_ids]},
            fields=["order_id", "txn_id"]
        ):
            if r.txn_id:
                txn_map.setdefault(r.order_id, []).append(r.txn_id)

        all_txns = list(set([t for v in txn_map.values() for t in v]))
        # ---------------------------------------------------
        # 🔥 MAPS (FIXED)
        # ---------------------------------------------------

        # PayU
        if all_txns:
            payu_map = dict(frappe.db.sql("""
                SELECT txnid, SUM(amount)
                FROM `tabPayU Response`
                WHERE status = 'Success'
                AND txnid IN %(txns)s
                GROUP BY txnid
            """, {"txns": tuple(all_txns)}))
        else:
            payu_map = {}

        # Bank Approved
        bank_map = dict(frappe.db.sql("""
            SELECT sales_order, SUM(approved_amount)
            FROM `tabBank Transfer Request`
            WHERE docstatus = 1 AND status = 'Approved'
            GROUP BY sales_order
        """))

        # Bank Pending
        bank_pending_map = dict(frappe.db.sql("""
                SELECT
                    sales_order,
                    SUM(
                        CASE
                            WHEN transfer_type = 'Bank Transfer'
                                THEN IFNULL(amount, 0)
                            ELSE IFNULL(approved_amount, 0)
                        END
                    ) AS pending_amount
                FROM `tabBank Transfer Request`
                WHERE docstatus = 0
                AND status = 'Unsettled'
                GROUP BY sales_order
            """))

        # Rupifi
        rupifi_map = dict(frappe.db.sql("""
            SELECT order_id, SUM(amount_value)
            FROM `tabRupifi Webhook Log`
            WHERE status = 'CAPTURED'
            GROUP BY order_id
        """))

        # Van Transactions
        van_map = dict(frappe.db.sql("""
            SELECT sales_order, SUM(transaction_amount)
            FROM `tabVan Transactions`
            WHERE transaction_status = 'Approved'
            GROUP BY sales_order
        """))
        invoices = list(set(
            frappe.get_all(
                "Sales Invoice Item",
                filters={
                    "sales_order": ["in", order_ids]
                },
                pluck="parent"
            )
        ))
        # Journal Entry
        invoice_so_map = {}

        for d in frappe.get_all(
            "Sales Invoice Item",
            filters={"sales_order": ["in", order_ids]},
            fields=["parent", "sales_order"]
        ):
            invoice_so_map[d.parent] = d.sales_order
        je_map = {}

        conditions = [
            """
            (
                jea.reference_type = 'Sales Order'
                AND jea.reference_name IN %(order_ids)s
            )
            """
        ]

        if invoices:
            conditions.append("""
                (
                    jea.reference_type = 'Sales Invoice'
                    AND jea.reference_name IN %(invoices)s
                )
            """)

        je_entries = frappe.db.sql(f"""
            SELECT
                je.name,
                je.posting_date,
                je.user_remark,
                jea.reference_type,
                jea.reference_name,
                SUM(jea.debit) AS debit,
                SUM(jea.credit) AS credit
            FROM `tabJournal Entry` je
            INNER JOIN `tabJournal Entry Account` jea
                ON je.name = jea.parent
            WHERE
                je.docstatus = 1
                AND je.mode_of_payment = 'adjusted from one order to another'
                AND (
                    {' OR '.join(conditions)}
                )
            GROUP BY
                je.name,
                jea.reference_type,
                jea.reference_name
        """, {
            "order_ids": tuple(order_ids),
            "invoices": tuple(invoices or [""])
        }, as_dict=True)

        for row in je_entries:
            amount = flt(row.debit or row.credit or 0)

            if row.reference_type == "Sales Order":
                je_map[row.reference_name] = (
                    je_map.get(row.reference_name, 0) + amount
                )

            elif row.reference_type == "Sales Invoice":
                so_name = invoice_so_map.get(row.reference_name)

                if so_name:
                    je_map[so_name] = (
                        je_map.get(so_name, 0) + amount
                    )

        # ---------------------------------------------------
        # 🧠 BUILD RESPONSE
        # ---------------------------------------------------
        order_paynow = frappe.get_doc("Order Paynow Setting")
        result = []

        for so in orders:
            total = float(so.rounded_total or so.grand_total or 0)

            TOLERANCE = 1  # ₹1

            received = 0

            # PayU
            for txn in txn_map.get(so.name, []):
                received += float(payu_map.get(txn, 0) or 0)

            # Other sources
            received += float(bank_map.get(so.name, 0) or 0)
            received += float(rupifi_map.get(so.name, 0) or 0)
            received += float(van_map.get(so.name, 0) or 0)
            received += float(je_map.get(so.name, 0) or 0)

            unsettled_amount = float(bank_pending_map.get(so.name, 0) or 0)

            pending_raw = round(total - (received), 2)

            if abs(pending_raw) <= TOLERANCE:
                pending = 0
            else:
                pending = max(pending_raw, 0)

            # Status
            if so.docstatus == 2 or (so.custom_dispatch_status or "").lower() == "cancelled":
                status = "Cancelled"
                pending = 0
            elif (so.custom_dispatch_status or "").lower() == "refunded":
                status = "Refunded"
                pending = 0
            elif (so.custom_dispatch_status or "").upper() not in ["PENDING PAYMENT", "FULLY PAID","MATERIAL SHORTAGE"]:
                status = so.custom_dispatch_status
                # pending = 0 if status in ["PARTIALLY DELIVERED","DELIVERED"] else:pending
                pending = 0 if status in ["PARTIALLY DELIVERED", "DELIVERED"] else pending
            elif (so.custom_dispatch_status or "").lower() == "material shortage":
                status = "Order Processing"

            elif received <= 0:
                status = "Pending"

            elif abs(total - received) <= TOLERANCE:
                status = "Fully Paid"
                pending = 0

            else:
                status = "Partially Paid"

            # Allowed Action
            if so.docstatus == 2 or status == "Refunded":
                allowed_action = "none"

            elif abs(total - received) <= TOLERANCE:
                allowed_action = "none"

            elif pending == total:
                allowed_action = "cancel"

            else:
                allowed_action = "map"
            # Address
            AddressLine1, city, state, pincode, country = frappe.db.get_value(
                "Address",
                so.shipping_address_name,
                ["address_line1", "city", "state", "pincode", "country"]
            ) if so.shipping_address_name else ("", "", "", "", "")

            result.append({
                "order_id": so.name,
                "date": frappe.utils.format_datetime(so.transaction_date) if so.transaction_date else None,
                "total_amount": total,
                "received_amount": received,
                "pending_amount": pending,
                "unsettled_amount": unsettled_amount,
                "status": status,
                "paynow_eligibility_date":order_paynow.pay_now_eligibility_date,
                "paynow_message":order_paynow.message,
                "docstatus": so.docstatus,
                "allowed_action": allowed_action,
                "payupreferedamount": so.custom_pay_on_proceed_order,
                "payupreferedmode": so.custom_payment_type,
                "user_type": user_type,
                "shipping_address_details": {
                    "address_line_1": AddressLine1,
                    "city": city,
                    "state": state,
                    "pincode": pincode,
                    "country": country
                },
            })

        total_pages = (total_records + page_size - 1) // page_size

        return api_response(True, "Sales orders fetched", {
            "total": total_records,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": result
        })

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_order_from_list")
        return api_response(False, "Error fetching sales orders")
    

# @frappe.whitelist()
# @validate_method(methods=["GET"])
# def get_order_from_list_optimise(order_id=None, from_date=None, to_date=None, page=1, page_size=20):
#     try:
#         start_time = time.perf_counter()

#         customer = get_customer_from_user()

#         filters = {
#             "customer": customer,
#             "docstatus": ["!=", 2],
#             "order_type": "Shopping Cart"
#         }

#         user_type = frappe.db.get_value("Customer", customer, "customer_group")

#         page = cint(page) or 1
#         page_size = cint(page_size) or 20
#         start = (page - 1) * page_size

#         if order_id:
#             filters["name"] = ["like", f"%{order_id}%"]

#         if bool(from_date) ^ bool(to_date):
#             return api_response(False, "Both from_date and to_date are required")

#         if from_date and to_date:
#             filters["creation"] = ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]]

#         total_records = frappe.db.count("Sales Order", filters)

#         orders = frappe.get_all(
#             "Sales Order",
#             filters=filters,
#             fields=[
#                 "name", "transaction_date", "creation",
#                 "grand_total", "advance_paid",
#                 "docstatus",
#                 "custom_payment_type",
#                 "custom_pay_on_proceed_order"
#             ],
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         if not orders:
#             return api_response(True, "No records found", {"data": []})

#         order_ids = [o.name for o in orders]

#         # ---------------------------------------------------
#         # 🔥 BULK DATA FETCH
#         # ---------------------------------------------------

#         # PayU txns
#         txn_map = frappe._dict()
#         for r in frappe.get_all(
#             "Payment Gateway Transaction",
#             filters={"order_id": ["in", order_ids]},
#             fields=["order_id", "txn_id"]
#         ):
#             txn_map.setdefault(r.order_id, []).append(r.txn_id)

#         # PayU success count
#         payu_success = frappe._dict(
#             frappe.db.sql("""
#                 SELECT txnid, COUNT(*) 
#                 FROM `tabPayU Response`
#                 WHERE status='success'
#                 GROUP BY txnid
#             """)
#         )

#         # Bank Transfer Approved Count
#         bank_approved = frappe._dict(
#             frappe.db.sql("""
#                 SELECT sales_order, COUNT(*)
#                 FROM `tabBank Transfer Request`
#                 WHERE docstatus=1
#                 GROUP BY sales_order
#             """)
#         )

#         # Bank Transfer Unsettled Amount
#         bank_unsettled = frappe._dict(
#             frappe.db.sql("""
#                 SELECT sales_order, SUM(amount)
#                 FROM `tabBank Transfer Request`
#                 WHERE status='Unsettled'
#                 GROUP BY sales_order
#             """)
#         )

#         # Rupifi captured
#         rupifi_captured = frappe._dict(
#             frappe.db.sql("""
#                 SELECT order_id, COUNT(*)
#                 FROM `tabRupifi Webhook Log`
#                 WHERE status='CAPTURED'
#                 GROUP BY order_id
#             """)
#         )

#         # ---------------------------------------------------
#         # 🧠 RESPONSE BUILD
#         # ---------------------------------------------------

#         TOLERANCE = 1.0
#         result = []

#         for so in orders:
#             total = float(so.grand_total or 0)
#             received = float(so.advance_paid or 0)
#             pending = max(round(total - received, 2), 0)

#             if pending <= TOLERANCE:
#                 pending = 0.0

#             if so.docstatus == 2:
#                 status = "Cancelled"
#             elif received <= 0:
#                 status = "Pending"
#             elif pending == 0:
#                 status = "Fully Paid"
#             else:
#                 status = "Partially Paid"

#             txn_ids = txn_map.get(so.name, [])
#             payu_count = sum(payu_success.get(t, 0) for t in txn_ids)

#             bank_count = bank_approved.get(so.name, 0)
#             rupifi_count = rupifi_captured.get(so.name, 0)

#             installments = payu_count + bank_count + rupifi_count

#             unsettled_amount = bank_unsettled.get(so.name, 0) or 0

#             result.append({
#                 "order_id": so.name,
#                 "date": so.transaction_date or so.creation,
#                 "total_amount": total,
#                 "received_amount": received,
#                 "pending_amount": pending,
#                 "unsettled_amount": unsettled_amount,
#                 "status": status,
#                 "installments": installments,
#                 "payupreferedamount": so.custom_pay_on_proceed_order,
#                 "payupreferedmode": so.custom_payment_type,
#                 "user_type": user_type
#             })

#         total_pages = (total_records + page_size - 1) // page_size
#         end_time = time.perf_counter()
#         execution_time = round(end_time - start_time, 3)

#         return api_response(True, "Sales orders fetched", {
#             "total": total_records,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#              "execution_time_sec": execution_time,
#             "data": result
#         })

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "get_order_from_list")
#         return api_response(False, "Error fetching sales orders")

def get_si_dispatch_status_map(so_name):
    """
    Fetch latest Sales Invoice dispatch status for all SO items in one query
    """

    data = frappe.db.sql("""
        SELECT
            sii.so_detail,
            si.custom_dispatch_status,
            si.posting_date,
            si.posting_time
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.sales_order = %s
          AND si.docstatus = 1
          AND IFNULL(si.is_return, 0) = 0
        ORDER BY
            sii.so_detail,
            si.posting_date DESC,
            si.posting_time DESC
    """, so_name, as_dict=True)

    status_map = {}

    for row in data:
        # Keep only latest per item
        if row.so_detail not in status_map and row.custom_dispatch_status:
            status_map[row.so_detail] = row.custom_dispatch_status

    return status_map


import frappe

def get_sales_order_item_status(so, item, si_status_map=None):
    """
    Returns the status of a single Sales Order item.
    
    Priority:
    1. REFUNDED (custom_item_status on item)
    2. Sales Invoice Dispatch Status (if item exists in invoice)
    3. Sales Order Dispatch Status
    """
    # Build Sales Invoice status map if not provided
    if si_status_map is None:
        si_items = frappe.db.get_all(
            "Sales Invoice Item",
            filters={"sales_order": so.name},
            fields=["sales_order_item", "parent as invoice_name"]
        )

        si_status_map = {}
        if si_items:
            invoice_names = list(set([si["invoice_name"] for si in si_items]))
            invoice_status_map = frappe.db.get_all(
                "Sales Invoice",
                filters={"name": ["in", invoice_names]},
                fields=["name", "custom_dispatch_status"]
            )
            invoice_status_lookup = {inv["name"]: inv["custom_dispatch_status"] for inv in invoice_status_map}
            for si in si_items:
                si_status_map[si["sales_order_item"]] = invoice_status_lookup.get(si["invoice_name"])

    # 1. REFUNDED
    if item.get("custom_item_status") == "REFUNDED":
        return "REFUNDED"
    # 2. Sales Invoice status
    elif si_status_map.get(item.name):
        return si_status_map.get(item.name)
    # 3. Fallback → Sales Order status
    else:
        return so.get("custom_dispatch_status") or so.status

@frappe.whitelist()
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0):
    from frappe.utils.pdf import get_pdf

    html = frappe.get_print(doctype, name, format, doc=doc, no_letterhead=no_letterhead)
    frappe.local.response.filename = "{name}.pdf".format(
        name=name.replace(" ", "-").replace("/", "-")
    )
    frappe.local.response.filecontent = get_pdf(html)
    frappe.local.response.type = "download"


@frappe.whitelist()
def download_invoice_pdf(id):
    try:
        frappe.set_user("Administrator")  # Ensure we have permissions to read all necessary data
        sales_invoice_doc = frappe.get_doc("Sales Invoice", id)
        default_print_format = (
            frappe.db.get_value(
                "Property Setter",
                dict(property="default_print_format", doc_type=sales_invoice_doc.doctype),
                "value",
            )
            or "Standard"
        )
        download_pdf(
            sales_invoice_doc.doctype,
            sales_invoice_doc.name,
            default_print_format,
            sales_invoice_doc,
        )
    except Exception as e:
        return api_response(False, f"Error generating PDF: {str(e)}")

@frappe.whitelist()
def get_order_details():
    import json

    try:
        def _fmt_date(value):
            if not value:
                return ""
            try:
                return frappe.utils.formatdate(value, "dd-mm-yyyy")
            except Exception:
                return str(value)

        def _fmt_datetime(value):
            if not value:
                return ""
            try:
                return frappe.utils.format_datetime(value, "dd-MM-yyyy HH:mm:ss")
            except Exception:
                return str(value)

        body = json.loads(frappe.request.data or "{}")
        order_id = body.get("order_id")

        if not order_id:
            return api_response(False, "Order ID is required")

        so = frappe.get_doc("Sales Order", order_id)
        customer_group_normalized = (so.customer_group or "").strip().lower()
        transporter_label = ""
        if so.custom_transporter:
            transporter_label = (
                frappe.db.get_value("Supplier", so.custom_transporter, "supplier_name")
                or so.custom_transporter
                or ""
            )
        transporter_name_normalized = transporter_label.strip().lower()
        is_farmer = customer_group_normalized == "farmer"
        is_indian_post = "indian post" in transporter_name_normalized

        # ---------------- ORDER SUMMARY ----------------
        order_summary = {
            "received": float(so.advance_paid or 0),
            "order_date": _fmt_date(so.transaction_date),
            "order_id": so.name,
            "customer_name": so.customer_name,
            "customer_group": so.customer_group,
            "order_amount": float(so.rounded_total or so.grand_total),
            "total_items": sum(i.qty for i in so.items),
            "discount_received": float(so.discount_amount or 0),
            "coupon_code": so.coupon_code or "",
            "coupon_percentage": 0  # optional if you want to calculate later
        }
        AddressLine1, city, state, pincode, country=frappe.db.get_value("Address",so.shipping_address_name,["address_line1", "city", "state", "pincode", "country"])
        # ---------------- TRANSACTIONS ----------------
        txnid = []

        # Payment Link txn IDs
        txnid.extend(
            frappe.get_all(
                "Payment Link",
                filters={"order_id": so.name},
                pluck="transactionid"
            )
        )

        # Payment Gateway Transaction txn IDs
        txnid.extend(
            frappe.get_all(
                "Payment Gateway Transaction",
                filters={"order_id": so.name},
                pluck="txn_id"
            )
        )

        # Optional: remove duplicates
        txnid = list(set(txnid))

        transactions = frappe.get_all(
            "PayU Response",
            filters={"txnid": ["IN",txnid]},
            fields=["status", "amount", "mode", "txnid", "createdat"]
        )
        bank_transfers= frappe.get_all(
            "Bank Transfer Request",
            filters={"sales_order": so.name, "docstatus": ["!=",2]},  # approved
            fields=["amount", "name", "approved_on as creation","status","approved_amount","transfer_type"],
        )
        rupify_transfers= frappe.get_all(
            "Rupifi Webhook Log",
            filters={"order_id": so.name},
            fields=["merchant_payment_ref_id", "amount_value", "createdat","status"]
        )
        van_transactions= frappe.get_all(
            "Van Transactions",
            filters={"sales_order": so.name},
            fields=["name", "transaction_amount", "created_at","transaction_status"]
        )
         # -----------------------------------------
        # ✅ ADD THIS: JOURNAL ENTRY
        # -----------------------------------------
        invoices = list(set(frappe.get_all(
            "Sales Invoice Item",
            filters={
                "sales_order": so.name
            },
            pluck="parent"
        )))
        je_entries = frappe.db.sql("""
            SELECT
                je.name,
                je.posting_date,
                je.remark,
                SUM(jea.debit) as debit,
                SUM(jea.credit) as credit
            FROM `tabJournal Entry` je
            JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
            WHERE je.docstatus = 1
            AND jea.reference_type IN ('Sales Order', 'Sales Invoice')
            AND (
                (jea.reference_type = 'Sales Order' AND jea.reference_name = %(so)s)
                OR
                (jea.reference_type = 'Sales Invoice' AND jea.reference_name IN %(invoices)s)
            )
            AND je.mode_of_payment = "adjusted from one order to another"
            GROUP BY je.name
        """, {
            "so": so.name,
            "invoices": tuple(invoices or [""])
        }, as_dict=True)


        transaction_data = []
        for tr in transactions:
            transaction_data.append({
                "amount": float(tr.amount),
                "mode_of_payment": tr.mode,
                "transaction_id": tr.txnid,
                "date": frappe.utils.format_datetime(tr.createdat),
                "status": tr.status
            })
        for bt in bank_transfers:
            transaction_data.append({
                "amount": float(bt.amount) if bt.status=='Unsettled' and bt.transfer_type == "Bank Transfer" else float(bt.approved_amount),
                "mode_of_payment": bt.transfer_type,
                "transaction_id": bt.name,
                "date": frappe.utils.format_datetime(bt.creation),
                "status": bt.status,
            })
        for rt in rupify_transfers:
            transaction_data.append({
                "amount": float(rt.amount_value),
                "mode_of_payment": "Shoption Credit",
                "transaction_id": rt.merchant_payment_ref_id,
                "date": frappe.utils.format_datetime(rt.createdat),
                "status":"Success" if rt.status=="CAPTURED" else "Failed",
            })
        for vt in van_transactions:
            transaction_data.append({
                "amount": float(vt.transaction_amount),
                "mode_of_payment": "Van Transaction",
                "transaction_id": vt.name,
                "date": frappe.utils.format_datetime(vt.created_at),
                "status": vt.transaction_status,
            })
        for je in je_entries:
            transaction_data.append({
                "amount": float(je.credit or 0),  # ✅ show value
                "mode_of_payment": "Map From Another Order",
                "transaction_id": je.name,
                "date": frappe.utils.formatdate(je.posting_date),
                "status": "Completed",
                "remark": je.remark
            })
        total = float(so.rounded_total or so.grand_total or 0)

        # -----------------------------
        # ✅ CORRECT RECEIVED CALCULATION
        # -----------------------------
        received = 0

        for tr in transaction_data:
            status = (tr.get("status") or "").lower()
            amount = float(tr.get("amount") or 0)

            # ✅ Only count successful transactions
            if status in ["success", "completed", "captured","approved"]:
                received += amount


        # -----------------------------
        # ✅ BANK PENDING (ONLY DRAFT / PENDING)
        # -----------------------------
        bank_paid = frappe.db.sql("""
            SELECT SUM(amount)
            FROM `tabBank Transfer Request`
            WHERE sales_order = %s
            AND docstatus = 0 AND status = 'Unsettled'
        """, so.name)[0][0] or 0

        si_status_map = get_si_dispatch_status_map(so.name)
        # -----------------------------
        # ✅ FINAL PENDING
        # -----------------------------
        total = so.rounded_total or so.grand_total
        pending_amount = max(total - (received + bank_paid), 0)

        # ✅ Handle rounding difference
        if abs(pending_amount) < 1:
            pending_amount = 0

        # Cancelled / Refunded
        if (
            so.docstatus == 2
            or (so.status or "").lower() == "cancelled"
            or (so.custom_dispatch_status or "").lower() in ["refunded", "cancelled","partially delivered","delivered"] 
        ):
            allowed_action = "none"

        else:
            if pending_amount == 0:
                allowed_action = "none"      # fully paid

            elif pending_amount == total:
                allowed_action = "cancel"    # no payment

            else:
                # ✅ Partial Payment केस
                if customer_group_normalized == "dealer":
                    allowed_action = "map"   # dealer can map
                else:
                    allowed_action = "none"  # farmer gets no action

        order_summary["allowed_action"] = allowed_action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
        # ---------------- INVOICES ----------------
        invoices = frappe.get_all(
            "Sales Invoice Item",
            filters={"sales_order": so.name,"docstatus": ["=", 1]},
            fields=["parent"],
            distinct=True
        )
        invoice_names = [inv.parent for inv in invoices if inv.parent]

        def _build_print_url(doctype, name, print_format=""):
            if not doctype or not name:
                return ""
            query = (
                f"doctype={quote(doctype)}"
                f"&name={quote(name)}"
                "&trigger_print=1"
                "&no_letterhead=1"
                "&_lang=en"
            )
            if print_format:
                query += f"&format={quote(print_format)}"
            return get_url(f"/printview?{query}")

        sales_invoice_print_format = f"{get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice&name=SINV-0001&format=Sales%20Invoice%20New"

        lr_list_by_invoice = {}
        if invoice_names and frappe.db.exists("DocType", "Upload LR Main"):
            lr_rows = frappe.get_all(
                "Upload LR Main",
                filters={"sales_invoice": ["in", invoice_names], "docstatus": ["!=", 2]},
                fields=[
                    "name", "sales_invoice", "transporter", "transporter_name",
                    "tracking_id", "lr_copy", "payment_status","customer_delivery_date","total_charges",
                    "estimeted_arrival_time", "creation", "no_of_boxes", "freight_amount"
                ],
                order_by="creation desc"
            )
            
            for lr in lr_rows:
                if lr.sales_invoice:
                    lr_list_by_invoice.setdefault(lr.sales_invoice, []).append(lr)

        ip_list_by_invoice = {}
        if (
            invoice_names
            and frappe.db.exists("DocType", "Indian Post Tracking Log")
        ):
            ip_rows = frappe.get_all(
                "Indian Post Tracking Log",
                filters={
                    "reference_type": "Sales Invoice",
                    "reference_name": ["in", invoice_names],
                    "docstatus": ["!=", 2],
                    "is_cancelled": 0,
                },
                fields=[
                    "name", "reference_name", "transporter", "tracking_id",
                    "payment_status", "estimeted_arrival_time", "created_at", "creation",
                    "no_of_boxes", "amount","length_cm","breadth_cm","height_cm","total_weight"
                ],
                order_by="creation desc"
            )
            for ip in ip_rows:
                if ip.reference_name:
                    ip_list_by_invoice.setdefault(ip.reference_name, []).append(ip)

        invoice_list = []
        for inv in invoices:
            si = frappe.get_doc("Sales Invoice", inv.parent)
            lr_list = lr_list_by_invoice.get(si.name, [])
            ip_list = ip_list_by_invoice.get(si.name, [])
            lr_entries = []
            ip_entries = []

            for lr in lr_list:
                lr_entries.append({
                    "lr_number": lr.get("name") or "",
                    "transporter": lr.get("transporter") or "",
                    "transporter_name": frappe.db.get_value("Supplier", lr.get("transporter"), "supplier_name") or "",
                    "tracking_id": lr.get("tracking_id") or "",
                    "lr_copy": get_url(lr.get("lr_copy")) if lr.get("lr_copy") else "",
                    "payment_status": lr.get("payment_status") or "",
                    "estimated_arrival_time": _fmt_datetime(lr.get("estimeted_arrival_time") or ""),
                    "no_of_boxes": float(lr.get("no_of_boxes") or 0),
                    "amount": float(lr.get("freight_amount") or 0),
                    "charges": float(lr.get("total_charges") or 0),
                    "created_at": _fmt_datetime(lr.get("creation") or ""),
                })

            for ip in ip_list:
                ip_entries.append({
                    "log_id": ip.get("name") or "",
                    "transporter": ip.get("transporter") or "",
                    "transporter_name": frappe.db.get_value("Supplier", ip.get("transporter"), "supplier_name") or "",
                    "tracking_id": ip.get("tracking_id") or "",
                    "payment_status": ip.get("payment_status") or "",
                    "estimated_arrival_time": _fmt_datetime(ip.get("estimeted_arrival_time") or ""),
                    "no_of_boxes": float(ip.get("no_of_boxes") or 0),
                    "amount": float(ip.get("amount") or 0),
                    "charges": float(ip.get("amount") or 0),
                    "created_at": _fmt_datetime(ip.get("created_at") or ip.get("creation") or ""),
                    "print_url": f"{get_url()}{frappe.db.get_value('File', {'attached_to_doctype': 'Indian Post Tracking Log', 'attached_to_name': ip.get('name')}, 'file_url')}" or "",
                })

            lr_and_stickers = []
            for lr_entry in lr_entries:
                lr_and_stickers.append({
                    "type": "lr",
                    "entry_id": lr_entry.get("lr_number") or "",
                    "transporter": lr_entry.get("transporter") or "",
                    "transporter_name": frappe.db.get_value("Supplier", lr_entry.get("transporter"), "supplier_name") or "",
                    "tracking_id": lr_entry.get("tracking_id") or "",
                    "payment_status": lr_entry.get("payment_status") or "",
                    "estimated_arrival_time": lr_entry.get("estimated_arrival_time") or "",
                    "no_of_boxes": float(lr_entry.get("no_of_boxes") or 0),
                    "amount": float(lr_entry.get("amount") or 0),
                    "charges": float(lr_entry.get("charges") or 0),
                    "document_url": lr_entry.get("lr_copy") or "",
                    "created_at": lr_entry.get("created_at") or "",
                    "print_url": "",
                })
            for ip_entry in ip_entries:
                lr_and_stickers.append({
                    "type": "sticker",
                    "entry_id": ip_entry.get("log_id") or "",
                    "transporter": ip_entry.get("transporter") or "",
                    "transporter_name": frappe.db.get_value("Supplier", ip_entry.get("transporter"), "supplier_name") or "",
                    "tracking_id": ip_entry.get("tracking_id") or "",
                    "payment_status": ip_entry.get("payment_status") or "",
                    "estimated_arrival_time": ip_entry.get("estimated_arrival_time") or "",
                    "no_of_boxes": float(ip_entry.get("no_of_boxes") or 0),
                    "amount": float(ip_entry.get("amount") or 0),
                    "charges": float(ip_entry.get("charges") or 0),
                    "document_url": ip_entry.get("print_url") or "",
                    "created_at": ip_entry.get("created_at") or "",
                    "print_url": ip_entry.get("print_url") or "",
                })

            if is_farmer and is_indian_post:
                selected_source = "indian_post_tracking_log"
                selected_entries = ip_entries
            elif not is_farmer and not is_indian_post:
                selected_source = "upload_lr_main"
                selected_entries = lr_entries
            elif ip_entries and not lr_entries:
                selected_source = "indian_post_tracking_log"
                selected_entries = ip_entries
            elif lr_entries and not ip_entries:
                selected_source = "upload_lr_main"
                selected_entries = lr_entries
            else:
                selected_source = "both"
                selected_entries = lr_entries + ip_entries

            total_no_of_boxes = sum(x["no_of_boxes"] for x in selected_entries)
            total_transport_amount = sum(x["amount"] for x in selected_entries)

            invoice_list.append({
                "invoice_id": si.name,
                "invoice_date": _fmt_date(si.posting_date),
                "amount": float(si.rounded_total or si.grand_total or 0),
                "status": si.status,
                "dispatch_status": si.custom_dispatch_status or "",
                "no_of_boxes": float(total_no_of_boxes or 0),
                "transport_amount": float(total_transport_amount or 0),
                "charges": float(total_transport_amount or 0),
                "sales_invoice_print_url":sales_invoice_print_format.replace("SINV-0001", si.name),
                "selected_source": selected_source,
                "selected_transport_entries": selected_entries,
                "lr_and_stickers": lr_and_stickers,
            })

        # ---------------- DISPATCH DETAILS ----------------
        deliveries = frappe.get_all(
            "Delivery Note Item",
            filters={"against_sales_order": so.name},
            fields=["parent"],
            distinct=True
        )

        dispatch_list = []
        for d in deliveries:
            dn = frappe.get_doc("Delivery Note", d.parent)
            dispatch_list.append({
                "dispatch_id": dn.name,
                "delivery_slip": dn.name,
                "date": _fmt_date(dn.posting_date),
                "status": dn.status
            })

        delivery_slips = []
        if invoice_names and frappe.db.exists("DocType", "Shipment"):
            shipment_meta = frappe.get_meta("Shipment")
            shipment_fields = ["name", "creation", "docstatus"]
            if shipment_meta.has_field("status"):
                shipment_fields.append("status")
            if shipment_meta.has_field("tracking_number"):
                shipment_fields.append("tracking_number")
            if shipment_meta.has_field("carrier"):
                shipment_fields.append("carrier")
            if shipment_meta.has_field("custom_delivery_conformation_recording"):
                shipment_fields.append("custom_delivery_conformation_recording")

            shipment_rows = frappe.get_all(
                "Shipment",
                filters={
                    "custom_sales_invoice": ["in", invoice_names],
                    "docstatus": ["!=", 2],
                },
                fields=shipment_fields,
                order_by="creation desc"
            )

            for sh in shipment_rows:
                delivery_slips.append({
                    "delivery_slip_id": sh.name,
                    "date": _fmt_datetime(sh.creation),
                    "status": sh.get("status") or "",
                    "tracking_number": sh.get("tracking_number") or "",
                    "carrier": sh.get("carrier") or "",
                    "delivery_confirmation_recording": get_url(sh.get("custom_delivery_conformation_recording")) or "",
                })

        # ---------------- SHIPMENT ITEMS ----------------
        shipment_items = []
        for item in so.items:
            shipment_items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "image":frappe.db.get_value("Item",item.item_code,"custom_image_1"),
                "qty": float(item.qty),
                "rate": float(item.rate),
                "total": float(item.amount),
                "status": get_sales_order_item_status(so, item, si_status_map)
            })

        # ---------------- FINAL RESPONSE ----------------
        response = {
            "order_summary": order_summary,
            "transactions": transaction_data,
            "invoices": invoice_list,
            "dispatch_details": dispatch_list,
            "shipment": {
                "transporter_name": frappe.db.get_value("Supplier", so.custom_transporter, "supplier_name") if so.custom_transporter else "",
                "status": so.custom_dispatch_status or "",
                "date": _fmt_date(so.transaction_date),
                "items": shipment_items,
                "delivery_slips": delivery_slips
            },
              "shipping_address_details": {
        "address_line_1": AddressLine1,
        "city": city,
        "state": state,
        "pincode": pincode,
        "country": country
    },
        }

        return api_response(True, "Order details fetched", response)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_order_details")
        return api_response(False, "Failed to fetch order details")

@frappe.whitelist()
def raise_bank_transfer():
    try:
        # --------------------------------------------------
        # Auth
        # --------------------------------------------------
        customer = get_customer_from_user()
        data = frappe.form_dict
        files = frappe.request.files

        # --------------------------------------------------
        # Required fields
        # --------------------------------------------------
        required_fields = ["order_id", "amount", "utr_number"]
        for field in required_fields:
            if not data.get(field):
                frappe.throw(f"{field} is required")

        # --------------------------------------------------
        # Create Bank Transfer Request
        # --------------------------------------------------
        doc = frappe.new_doc("Bank Transfer Request")
        doc.sales_order = data.get("order_id")
        doc.customer = customer
        doc.amount = float(data.get("amount"))
        doc.utr_number = data.get("utr_number")
        doc.insert(ignore_permissions=True)

        # --------------------------------------------------
        # Save receipt (multipart)
        # --------------------------------------------------
        _attach_file(files, doc, "receipt")

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return api_response(
            True,
            "Bank transfer submitted for verification",
            {"name": doc.name}
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "raise_bank_transfer_complaint"
        )
        return api_response(False, "Failed to submit bank transfer")

@frappe.whitelist()
def get_complaint_masters():
    try:
        meta_data={}
        meta_data["complaint_types"] = frappe.get_all(
            "Complaint Type",
            filters={"disabled": 0},
            pluck="name"
        )
        meta_data["orders"]= frappe.get_all(
            "Sales Order",
            filters={"docstatus": 1, "customer": get_customer_from_user()},
            pluck="name"
        )

        return api_response(True, "Complaint masters fetched", meta_data)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_complaint_type_masters")
        return api_response(False, "Failed to fetch complaint types")

@frappe.whitelist()
def complaint_type():
    try:
        
        complaint_types = frappe.get_all(
            "Complaint Type",
            filters={"disabled": 0},
            pluck="name"
        )

        return api_response(True, "Complaint types fetched", complaint_types)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "complaint_type")
        return api_response(False, "Failed to fetch complaint types")
    
import frappe
from frappe import _
from frappe.utils import nowdate,now
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def raise_complaint():
    try:
        # --------------------------------------------------
        # Auth check
        # --------------------------------------------------
        data = frappe.form_dict
        files = frappe.request.files

        # --------------------------------------------------
        # Required fields
        # --------------------------------------------------
        required = ["order_id", "complaint_type", "subject"]
        for field in required:
            if not data.get(field):
                frappe.throw(_(f"{field} is required"))
        # --------------------------------------------------
        # Create Complaint
        # --------------------------------------------------
        complaint = frappe.new_doc("Raise a Complaint")
        complaint.order_id = data.get("order_id")
        complaint.complaint_type = data.get("complaint_type")
        complaint.subject = data.get("subject")
        complaint.description = data.get("description")
        complaint.status = "Pending"
        complaint.raised_on = now()
        complaint.customer = get_customer_from_user()

        complaint.insert(ignore_permissions=True)

        # --------------------------------------------------
        # Save Attachments (multipart)
        # --------------------------------------------------
        _attach_file(files, complaint, "attachment_1")
        _attach_file(files, complaint, "attachment_2")
        _attach_file(files, complaint, "attachment_3")

        complaint.save(ignore_permissions=True)
        frappe.db.commit()

        return api_response(True, "Complaint Raised Successfully", complaint.name)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "raise_complaint")
        return api_response(False, "Failed to raise complaint", None)


  
# ======================================================
# Helper: Save attachment safely
# ======================================================
def _attach_file(files, doc, fieldname):
    if fieldname in files:
        file = files.get(fieldname)

        saved = save_file(
            fname=file.filename,
            content=file.stream.read(),
            dt=doc.doctype,
            dn=doc.name,
            is_private=0
        )

        setattr(doc, fieldname, saved.file_url)
        
        
@frappe.whitelist()
def complaint_list(page=1, page_size=20):
    try:
        customer = get_customer_from_user()

        # ---------------- Pagination ----------------
        try:
            page = int(page)
            page_size = int(page_size)
        except Exception:
            page, page_size = 1, 20

        start = (page - 1) * page_size

        filters = {"customer": customer}

        # ---------------- Total Count ----------------
        total_records = frappe.db.count("Raise a Complaint", filters)

        # ---------------- Fetch Complaints ----------------
        complaints = frappe.get_all(
            "Raise a Complaint",
            filters=filters,
            fields=[
                "name",
                "complaint_type",
                "order_id",
                "subject",
                "description",
                "status",
                "resolved_on"            ],
            order_by="creation desc",
            limit_start=start,
            limit_page_length=page_size,
        )

        total_pages = (total_records + page_size - 1) // page_size

        return api_response(True, "Complaints fetched successfully", {
            "total": total_records,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": complaints
        })

    except Exception:
        frappe.log_error(frappe.get_traceback(), "complaint_list")
        return api_response(False, "Failed to fetch complaints")

@frappe.whitelist()
def become_a_supplier():
    try:
        data = frappe.form_dict
        files = frappe.request.files

        # --------------------------------------------------
        # Required fields validation
        # --------------------------------------------------
        required_fields = ["brand_name", "product_name"]
        for field in required_fields:
            if not data.get(field):
                frappe.throw(f"{field.replace('_', ' ').title()} is required")

        # --------------------------------------------------
        # Resolve customer from logged-in user
        # --------------------------------------------------
        customer = get_customer_from_user()
        if not customer:
            frappe.throw("Customer not found for this user")

        # --------------------------------------------------
        # Create Supplier Request
        # --------------------------------------------------
        supplier_doc = frappe.get_doc({
            "doctype": "Be a Supplier",
            "brand_name": data.get("brand_name"),
            "product_name": data.get("product_name"),
            "percentage_discount_to_retailer": data.get("percentage_discount_to_retailer"),
            "percentage_discount_to_shoption": data.get("percentage_discount_to_shoption"),
            "customer": customer,
        })

        supplier_doc.insert(ignore_permissions=True)

        # --------------------------------------------------
        # Attach files (multipart)
        # --------------------------------------------------
        if files:
            _attach_file(files, supplier_doc, "attachment")
            supplier_doc.save(ignore_permissions=True)

        frappe.db.commit()

        return api_response(
            True,
            "Supplier request submitted successfully",
            supplier_doc.name
        )

    except frappe.ValidationError:
        # Validation errors should bubble up cleanly
        raise

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "become_a_supplier API Error"
        )
        return api_response(False, "Failed to submit supplier request", None)
    
    


@frappe.whitelist()
def get_general_ledger_report(from_date=None, to_date=None):
    """
    Mobile API to fetch Customer General Ledger report
    Opening & Closing balances are returned separately
    """

    try:
        from erpnext.accounts.utils import get_fiscal_year
        from frappe.utils import nowdate
        from frappe.desk.query_report import run
        import json

        # --------------------------------------------------
        # Resolve date range
        # --------------------------------------------------
        if not from_date or not to_date:
            current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
            from_date = from_date or current_fiscal_year.get("year_start_date")
            to_date = to_date or current_fiscal_year.get("year_end_date")
            fiscal_year_name = current_fiscal_year.get("name")
        else:
            fiscal_year_name = None

        # --------------------------------------------------
        # Resolve customer
        # --------------------------------------------------
        customer = get_customer_from_user()
        if not customer:
            frappe.throw("Customer not found for this user")

        # --------------------------------------------------
        # Report filters
        # --------------------------------------------------
        filters = {
            # "from_date": from_date,
            "from_date":getdate("2026-04-09"),
            "to_date": to_date,
            "company": frappe.defaults.get_user_default("Company"),
            "party_type": "Customer",
            "party": json.dumps([customer]),
            "categorize_by": "Categorize by Voucher (Consolidated)",
            "show_remarks": 1
        }

        # --------------------------------------------------
        # Run General Ledger report
        # --------------------------------------------------
        report_data = run(
            report_name="General Ledger",
            filters=filters,
            ignore_prepared_report=True
        )

        rows = report_data.get("result", [])

        # --------------------------------------------------
        # Extract Opening / Closing & Transactions
        # --------------------------------------------------
        opening_balance = 0
        closing_balance = 0
        transactions = []

        for row in rows:
            account = (row.get("account") or "").lower().strip("'").strip()

            # ---------------- Opening ----------------
            if account == "opening":
                opening_balance = (row.get("balance") or 0) * -1
                continue

            # ---------------- Total ----------------
            if account == "total":
                continue

            # ---------------- Closing ----------------
            if account.startswith("closing"):
                closing_balance = (row.get("balance") or 0) * -1
                continue

            # ---------------- Actual Transactions ----------------
            if not row.get("voucher_no"):
                continue

            debit = row.get("debit") or 0
            credit = row.get("credit") or 0

            transactions.append({
                "posting_date": row.get("posting_date"),
                "voucher_type": row.get("voucher_type"),
                "voucher_no": row.get("voucher_no"),

                # Customer perspective
                "debit": -debit if debit else 0,
                "credit": credit if credit else 0,
                "balance": (row.get("balance") or 0) * -1,

                "remarks": row.get("remarks"),
            })


        return api_response(
            True,
            "Customer Ledger fetched successfully",
            {
                "fiscal_year": fiscal_year_name,
                "from_date": from_date,
                "to_date": to_date,
                "opening_balance": opening_balance,
                "closing_balance": closing_balance,
                "count": len(transactions),
                "transactions": transactions,
            }
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Mobile General Ledger API Error"
        )
        return api_response(False, "Failed to fetch General Ledger", None)

# Map to another order list for this
@frappe.whitelist()
def orders_to_map(amount=None,customer=None):
    """
    Fetch Sales Orders with pending amount greater than the specified 'amount'.
    Excludes orders with dispatch status REFUNDED or CANCELLED.
    """
    try:
        if not amount:
            return api_response(False, "Amount is mandatory to compare")

        # Fetch all relevant Sales Orders
        if not customer:
            customer = get_customer_from_user()
        orders = frappe.get_all(
            "Sales Order",
            filters={
                "docstatus": ["!=", 2],
                "customer": customer,
                "transaction_date":[">=","2026-04-01"],
                "status":["!=","Completed"],
                "custom_dispatch_status": ["not in", ["REFUNDED", "CANCELLED"]]
            },
            fields=["name", "grand_total", "advance_paid","transaction_date","rounded_total"],
            order_by="transaction_date desc"
        )

        # Fetch unsettled bank transfer amounts
        bank_unsettled = frappe._dict(
            frappe.db.sql("""
                SELECT sales_order, SUM(approved_amount)
                FROM `tabBank Transfer Request`
                WHERE status='Unsettled'
                GROUP BY sales_order
            """)
        )
        result = []
        for so in orders:
            total = flt(so.rounded_total or so.grand_total)
            received = flt(so.advance_paid)
            bank_paid = flt(bank_unsettled.get(so.name, 0))
            pending_amount = max(total - (received + bank_paid), 0)
            
            if pending_amount >= flt(amount):
                result.append(so.name)

        return api_response(True, "Orders fetched successfully", result)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "orders_to_map")
        return api_response(False, "Something went wrong.")


# Map to another order API
@frappe.whitelist()
def process_order_payments(order_id, allowed_action, target_order_id=None):
    """
    Move or cancel payments linked to a Sales Order.
    allowed_action: "cancel", "map", "none"
    target_order_id: required if allowed_action == "map"
    """
    try:
        if not order_id:
            return api_response(
                False,
                "Sales Order is required"
            )

        if not allowed_action:
            return api_response(
                False,
                "allowed_action is required"
            )
        allowed_action = allowed_action.lower()

        if allowed_action not in ["cancel", "map", "none"]:
            return api_response(False, "Invalid allowed_action.")
        if not frappe.db.exists("Sales Order", order_id):
            return api_response(
                False,
                f"Sales Order not found: {order_id}"
            )
        if allowed_action == "map":

            if not target_order_id:
                return api_response(
                    False,
                    "target_order_id is mandatory when allowed_action = 'map'"
                )

            if order_id == target_order_id:
                return api_response(
                    False,
                    "Source and target Sales Order cannot be same"
                )

            if not frappe.db.exists("Sales Order", target_order_id):
                return api_response(
                    False,
                    f"Target Sales Order not found: {target_order_id}"
                )
        # ------------------ CANCEL ------------------
        # ------------------ CANCEL ------------------
        if allowed_action == "cancel":
            so_doc = frappe.get_doc("Sales Order", order_id)

            # Submit if not submitted
            if so_doc.docstatus != 1:
                try:
                    so_doc.submit()
                except Exception as e:
                    return api_response(False, f"Cannot submit the Sales Order: {e}")

            # Now cancel the order
            try:
                so_doc.cancel()
            except Exception as e:
                return api_response(False, f"Cannot cancel the Sales Order: {e}")

            # Update Sales Order dispatch status
            frappe.db.set_value(
                "Sales Order",
                order_id,
                "custom_dispatch_status",
                "CANCELLED",
                update_modified=True
            )
            frappe.db.commit()

            return api_response(True, "Sales order cancelled successfully.")


        # ------------------ MAP ------------------
        elif allowed_action == "map":
            # docstatus = frappe.db.get_value("Sales Order", order_id, "docstatus")
            # if docstatus == 0:
            #     so_doc = frappe.get_doc("Sales Order", order_id)
            #     so_doc.submit()

            # elif docstatus == 1:
            #     pass  # already submitted

           # ---------- PAYMENT ENTRY (ONLY SUBMITTED) ----------
            payment_refs = frappe.get_all(
                "Payment Entry Reference",
                filters={
                    "reference_name": order_id,
                    "reference_doctype": "Sales Order"
                },
                fields=["parent", "allocated_amount"]
            )

            # Get only submitted Payment Entries
            pe_ids = list(set([r.parent for r in payment_refs]))

            valid_pe = []
            paid_from_accounts = set()

            if pe_ids:
                payment_entries = frappe.get_all(
                    "Payment Entry",
                    filters={
                        "name": ["in", pe_ids],
                        "docstatus": 1
                    },
                    fields=["name", "paid_from"]
                )

                valid_pe = [pe.name for pe in payment_entries]

                for pe in payment_entries:
                    if pe.paid_from:
                        paid_from_accounts.add(pe.paid_from)

            # Filter valid references only
            valid_refs = [r for r in payment_refs if r.parent in valid_pe]

            total_paid_amount = sum(flt(r.allocated_amount) for r in valid_refs)


            # ---------- JOURNAL ENTRY ----------
            je_amount = frappe.db.sql("""
                SELECT SUM(jea.credit)
                FROM `tabJournal Entry` je
                JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
                WHERE jea.reference_type = 'Sales Order'
                AND jea.reference_name = %s
                AND je.mode_of_payment = 'adjusted from one order to another'
                AND je.docstatus = 1
            """, order_id)[0][0] or 0


            # ---------- FINAL MAPPED ----------
            mapped_amount = flt(total_paid_amount) + flt(je_amount)

            # ---------- ACCOUNT ----------
            company = frappe.db.get_value("Sales Order", order_id, "company")

            company_default_account = frappe.db.get_value(
                "Company",
                company,
                "default_receivable_account"
            )

            account_to_use = list(paid_from_accounts)[0] if paid_from_accounts else company_default_account

            journal_response=None
            # ---------- ADJUST ----------
            if mapped_amount > 0 and account_to_use:
                journal_response = adjust_advance_via_journal(
                    order_id,
                    target_order_id,
                    mapped_amount,
                    account_to_use
                )
                # If journal failed, stop execution and return error
                if not journal_response.get("status"):
                    return api_response(
                        False,
                        f"Journal Adjustment Failed: {journal_response.get('message')}"
                    )

            
            # Directly update the custom_dispatch_status to "REFUNDED"
            frappe.db.set_value(
                "Sales Order",
                order_id,
                "custom_dispatch_status",
                "REFUNDED",
                update_modified=True
            )

            return api_response(True, f"Payments mapped to {target_order_id} and original order marked as Refunded.", journal_response.get("data") if journal_response else None)

        # ------------------ NONE ------------------
        else:
            return api_response(True, "No action performed.")

    except Exception:
        frappe.log_error(frappe.get_traceback(), "process_order_payments")
        return api_response(False, "Something went wrong.")


# ------------------ JOURNAL ADJUSTMENT ------------------
from frappe.utils import nowdate

@frappe.whitelist()
def adjust_advance_via_journal(source_order, target_order, amount, account):
    try:
        amount = flt(amount)

        source_doc = frappe.get_doc("Sales Order", source_order)

        customer = source_doc.customer
        company = source_doc.company

        amount = flt(amount, 2)
        account_currency = get_account_currency(account)
        company_currency = frappe.get_cached_value("Company", company, "default_currency")

        def _get_mapped_amount():
            # Always read latest state so we don't over-map SO advance.
            target_doc = frappe.get_doc("Sales Order", target_order)
            voucher_total = (
                flt(target_doc.base_grand_total, 2)
                if account_currency == company_currency
                else flt(target_doc.grand_total, 2)
            )
            current_advance = flt(target_doc.advance_paid, 2)
            # Keep tiny buffer for boundary/currency rounding issues.
            allowed = max(flt(voucher_total - current_advance - 0.01, 2), 0)
            return min(amount, allowed), voucher_total, current_advance

        def _build_and_submit(reference_amount):
            je = frappe.new_doc("Journal Entry")
            je.voucher_type = "Journal Entry"
            je.company = company
            je.posting_date = nowdate()
            je.mode_of_payment = "adjusted from one order to another"
            je.user_remark = f"Advance adjustment {source_order} -> {target_order}"

            je.append("accounts", {
                "account": account,
                "party_type": "Customer",
                "party": customer,
                "debit_in_account_currency": amount,
                "debit": amount
            })

            if reference_amount > 0:
                je.append("accounts", {
                    "account": account,
                    "party_type": "Customer",
                    "party": customer,
                    "credit_in_account_currency": reference_amount,
                    "credit": reference_amount,
                    "is_advance": "Yes",
                    "reference_type": "Sales Order",
                    "reference_name": target_order,
                })

            remaining = flt(amount - reference_amount, 2)
            if remaining > 0:
                je.append("accounts", {
                    "account": account,
                    "party_type": "Customer",
                    "party": customer,
                    "credit_in_account_currency": remaining,
                    "credit": remaining,
                })

            je.insert(ignore_permissions=True)
            je.submit()
            return je

        mapped_amount, voucher_total, current_advance = _get_mapped_amount()
        try:
            je = _build_and_submit(mapped_amount)
        except Exception as submit_error:
            if "cannot be greater than Grand Total" in str(submit_error):
                frappe.log_error(
                    f"SO={target_order}, amount={amount}, mapped={mapped_amount}, "
                    f"voucher_total={voucher_total}, advance_paid={current_advance}",
                    "adjust_advance_via_journal_retry_unlinked"
                )
                je = _build_and_submit(0)
            else:
                raise

        return api_response(True, "Advance adjusted successfully.", je.name)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "adjust_advance_via_journal")
        return api_response(False, f"Error: {e}")

@frappe.whitelist()
def create_contact(contact_list):
    try:
        # ----------------------------
        # Get customer from logged-in user
        # ----------------------------
        customer = get_customer_from_user()
        if not customer:
            frappe.throw("Customer not found for this user")

        if not frappe.db.exists("Customer", customer):
            frappe.throw("Customer not found")

        # ----------------------------
        # Parse payload
        # ----------------------------
        if isinstance(contact_list, str):
            import json
            contact_list = json.loads(contact_list)

        # If API receives {"contact_list": [...]}
        if isinstance(contact_list, dict) and "contact_list" in contact_list:
            contact_list = contact_list.get("contact_list")

        if not isinstance(contact_list, list) or not contact_list:
            frappe.throw("contact_list must be a non-empty list")

        results = []

        for row in contact_list:
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip().lower()
            phone = (row.get("phone") or "").strip()

            if not name:
                results.append({
                    "status": "skipped",
                    "reason": "name is required",
                    "row": row
                })
                continue

            # ---------------------------------
            # ✅ Find existing contact by (customer + email + phone)
            # so same email but different phone => NEW contact
            # ---------------------------------
            contact_name = None
            if email and phone:
                existing = frappe.db.sql("""
                    SELECT c.name
                    FROM `tabContact` c
                    JOIN `tabDynamic Link` dl ON dl.parent = c.name
                    LEFT JOIN `tabContact Email` ce ON ce.parent = c.name
                    LEFT JOIN `tabContact Phone` cp ON cp.parent = c.name
                    WHERE dl.parenttype = 'Contact'
                      AND dl.link_doctype = 'Customer'
                      AND dl.link_name = %s
                      AND ce.email_id = %s
                      AND cp.phone = %s
                    LIMIT 1
                """, (customer, email, phone), as_list=True)

                if existing:
                    contact_name = existing[0][0]

            # ---------------------------------
            # Create or Update Contact
            # ---------------------------------
            if contact_name:
                contact = frappe.get_doc("Contact", contact_name)
                action = "updated"
            else:
                contact = frappe.new_doc("Contact")
                contact.append("links", {
                    "link_doctype": "Customer",
                    "link_name": customer
                })
                action = "created"

            contact.first_name = name

            # ----------------------------
            # Add Email (if provided & not exists)
            # ----------------------------
            if email:
                existing_emails = set(
                    (r.email_id or "").strip().lower()
                    for r in (contact.email_ids or [])
                    if r.email_id
                )
                if email not in existing_emails:
                    contact.append("email_ids", {
                        "email_id": email,
                        "is_primary": 0 if not existing_emails else 0
                    })

            # ----------------------------
            # Add Phone (if provided & not exists)
            # ----------------------------
            if phone:
                existing_phones = set(
                    (r.phone or "").strip()
                    for r in (contact.phone_nos or [])
                    if r.phone
                )
                if phone not in existing_phones:
                    contact.append("phone_nos", {
                        "phone": phone,
                        "is_primary_phone": 0 if not existing_phones else 0,
                        "is_primary_mobile_no": 0 if not existing_phones else 0
                    })

            # ----------------------------
            # Ensure primary flags exist
            # ----------------------------
            if contact.email_ids and not any(int(r.is_primary or 0) == 1 for r in contact.email_ids):
                contact.email_ids[0].is_primary = 0

            if contact.phone_nos and not any(int(r.is_primary_phone or 0) == 1 for r in contact.phone_nos):
                contact.phone_nos[0].is_primary_phone = 0
                contact.phone_nos[0].is_primary_mobile_no = 0

            contact.save(ignore_permissions=True)

        frappe.db.commit()

        return api_response(True, "Contacts processed successfully", results)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "create_contact_api")
        return api_response(False, "Failed to create/update contact")
    
            
@frappe.whitelist()
def save_token(fcm_token=None):
    try:
        # Validate customer exists
        user=frappe.session.user
        employee = None
        if get_employee_by_user(user):
            employee = get_employee_by_user(user).get("name")
        if frappe.db.exists("User Device Info", {"user": user}):
            token = frappe.get_doc("User Device Info", frappe.db.get_value("User Device Info", {"user": user}, "name"))
            token.fcm_token = fcm_token
            token.employee=employee
            token.save(ignore_permissions=True)
        else:
            token = frappe.get_doc(
                doctype="User Device Info",
                fcm_token=fcm_token,
                user=frappe.session.user,
                employee=employee
            ).insert(ignore_permissions=True)


        return api_response(
             True,
             "Device Info saved successfully"
        )

    except Exception:
        frappe.log_error(frappe.get_traceback(), "create_device_info_api")
        return api_response(False, "Failed to save device info")
  

# lots 

import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst  # 18/12

@frappe.whitelist(allow_guest=True)
def get_pricing_rules(item_code=None, page=1, page_size=20, mobile_no=None):

    api_auth()
    require_post()

    frappe.set_user("Administrator")   # Always admin → no permission issues

    # --------------------------
    # 1️⃣ GET USER FROM MOBILE
    # --------------------------
    customer = None
    user_email = None
    is_dealer = False

    if mobile_no:
        customer = frappe.get_all(
            "Customer",
            filters={"mobile_no": mobile_no},
            fields=["name", "customer_group"],
            limit=1
        )

        if customer:
            cust = customer[0]

            # mark dealer
            if "dealer" in (cust.customer_group or "").lower():
                is_dealer = True

            # get portal user
            portal_user = frappe.get_all(
                "Portal User",
                filters={"parent": cust.name},
                fields=["user"],
                limit=1
            )

            if portal_user:
                user_email = portal_user[0].user

    # --------------------------
    # 2️⃣ PAGINATION
    # --------------------------
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    root_filters = {"disable": 0}

    # --------------------------
    # 3️⃣ FIND CHILD TABLE IN PRICING RULE
    # --------------------------
    child_doctype = None
    for df in frappe.get_meta("Pricing Rule").fields:
        if df.fieldtype == "Table" and "Item" in (df.options or ""):
            child_doctype = df.options
            break

    if not child_doctype:
        return api_response(True, "Pricing rules fetched", {
            "total": 0, "page": page, "page_size": page_size,
            "total_pages": 0, "data": [],
            "error": "Child table not found"
        })

    # --------------------------
    # 4️⃣ FILTER RULES BY ITEM CODE
    # --------------------------
    if item_code:
        rule_names = frappe.get_all(
            child_doctype,
            filters={"item_code": item_code},
            pluck="parent"
        )

        if not rule_names:
            return api_response(True, "Pricing rules fetched", {
                "total": 0, "page": page, "page_size": page_size,
                "total_pages": 0, "data": []
            })

        root_filters["name"] = ["in", rule_names]

    # --------------------------
    # 5️⃣ FETCH DEALER PRICE LIST FROM ITEM PRICE
    # --------------------------
    # fetch only DEALER price list, ignore Farmer
    dealer_price_row = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code},
        fields=["price_list"],
    )

    dealer_price_list = None

    for row in dealer_price_row:
        if "dealer" in row.price_list.lower():
            dealer_price_list = row.price_list
            break

    # --------------------------
    # 6️⃣ CHECK USER PERMISSION FOR DEALER PRICE LIST
    # --------------------------
    has_access = False

    if user_email and dealer_price_list:
        perm = frappe.get_all(
            "User Permission",
            filters={
                "user": user_email,
                "allow": "Price List",
                "for_value": dealer_price_list
            },
            limit=1
        )
        if perm:
            has_access = True

    # --------------------------
    # 7️⃣ FETCH PRICING RULES
    # --------------------------
    allowed_fields = [
        "title", "pricing_rule_type", "rate_or_discount",
        "discount_percentage", "margin_type",
        "margin_rate_or_amount", "min_qty", "max_qty",
        "valid_from", "valid_upto", "priority", "company",
        "rate"
    ]

    meta_fields = [df.fieldname for df in frappe.get_meta("Pricing Rule").fields]
    fields = [f for f in allowed_fields if f in meta_fields]

    start = (page - 1) * page_size

    try:
        data = frappe.get_list(
            "Pricing Rule",
            filters=root_filters,
            fields=fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        # SORT LOTS BY min_qty ASC
        data = sorted(data, key=lambda x: x.get("min_qty") or 0)

        # --------------------------
        # 8️⃣ APPLY ACCESS LOGIC
        # --------------------------
        # for row in data:
        #     if not has_access:    # NO ACCESS → HIDE PRICES
        #         row["rate"] = None
        #         row["discount_percentage"] = None
                
        for row in data:
            if not has_access:
                row["rate"] = None
                row["discount_percentage"] = None
            else:
                # ADD GST ON PRICING RULE RATE
                if row.get("rate"):
                    try:
                        gst_data = get_item_price_withgst(
                            item_code=item_code,
                            customer=customer[0].name if customer else None,
                            customer_group=customer[0].customer_group if customer else None,
                            company=frappe.defaults.get_global_default("company"),
                            currency=frappe.defaults.get_global_default("currency"),
                            qty=1,
                            base_rate_override=row["rate"]   
                            
                        )
                        # row["rate"] = round(row["rate"] + (gst_data.get("difference") or 0), 2)
                        gst_difference = gst_data.get("difference") or 0
                        # row["rate"] = round(row["rate"] + gst_difference, 2)
                        row["rate"] = round(row["rate"] + gst_difference, 2)
                    except Exception:
                        pass


        # --------------------------
        # 9️⃣ PAGINATION OUTPUT
        # --------------------------
        total = frappe.db.count("Pricing Rule", root_filters)
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Pricing rules fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data,
            "price_list_used": dealer_price_list,
            "has_access": has_access
        })

    except Exception as e:
        return api_response(True, "Pricing rules fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": [],
            "error": str(e)
        })

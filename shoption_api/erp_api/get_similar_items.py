

# updated code with MOQ logic 16/12
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_similar_items(item_code=None, mobile_no=None, page=1, page_size=20):

#     api_auth()
#     require_post()

#     # --------------------------
#     # VALIDATION
#     # --------------------------
#     if not item_code:
#         return api_response(False, "item_code is required")

#     if not frappe.db.exists("Item", item_code):
#         return api_response(False, "Invalid item_code")

#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # --------------------------
#     # FIND CUSTOMER → USER + GROUP
#     # --------------------------
#     customer = frappe.get_all(
#         "Customer",
#         filters={"mobile_no": mobile_no},
#         fields=["name", "customer_group"],
#         limit=1
#     )

#     user_id = None
#     customer_group = None

#     if customer:
#         customer_group = customer[0].customer_group

#         portal_user = frappe.get_all(
#             "Portal User",
#             filters={"parent": customer[0].name},
#             fields=["user"],
#             limit=1
#         )

#         if portal_user:
#             user_id = portal_user[0].user

#     # --------------------------
#     # SET USER CONTEXT
#     # --------------------------
#     if user_id:
#         frappe.set_user(user_id)
#     else:
#         frappe.set_user("Administrator")     # guest → lock price

#     # --------------------------
#     # CORRECT FIELD NAME
#     # --------------------------
#     generic = frappe.db.get_value("Item", item_code, "custom_genric_name")

#     if not generic:
#         return api_response(True, "No generic name found", {
#             "generic_name": None,
#             "data": []
#         })

#     # --------------------------
#     # PAGINATION
#     # --------------------------
#     try:
#         page, page_size = int(page), int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     # --------------------------
#     # FIELDS (same as get_items)
#     # --------------------------
#     meta = frappe.get_meta("Item")
#     fields_available = {df.fieldname for df in meta.fields}

#     fields = ["name as item_code", "item_name"]

#     opt_fields = [
#         "item_group", "brand", "stock_uom", "gst_hsn_code",
#         "custom_sub_category", "custom_image_path",
#         "custom_image_1"
#     ]

#     for f in opt_fields:
#         if f in fields_available:
#             fields.append(f)

#     # --------------------------
#     # FETCH SIMILAR ITEMS
#     # --------------------------
#     items = frappe.get_list(
#         "Item",
#         filters={"custom_genric_name": generic},
#         fields=fields,
#         limit_start=start,
#         limit_page_length=page_size,
#         order_by="creation desc"
#     )

#     # --------------------------
#     # PRICE + MOQ LOGIC
#     # --------------------------
#     for row in items:

#         # -------- PRICE --------
#         price_row = frappe.get_list(
#             "Item Price",
#             filters={"item_code": row["item_code"]},
#             fields=[
#                 "price_list",
#                 "custom_mrp",
#                 "price_list_rate",
#                 "discount",
#                 "custom_oem_code"
#             ],
#             order_by="valid_from desc",
#             limit=1
#         )

#         if user_id and price_row:
#             p = price_row[0]
#             row["price_list"] = p.get("price_list")
#             row["mrp"] = p.get("custom_mrp")
#             row["price"] = p.get("price_list_rate")
#             row["discount"] = p.get("discount")
#             row["oem_code"] = p.get("custom_oem_code")
#         else:
#             row["price_list"] = None
#             row["mrp"] = None
#             row["price"] = None
#             row["discount"] = None
#             row["oem_code"] = None

#         # -------- MOQ (NEW) --------
#         row["moq"] = None

#         if customer_group:
#             item_full_doc = frappe.get_doc("Item", row["item_code"])

#             for moq_row in item_full_doc.get("custom_moq", []):
#                 if moq_row.customer_group == customer_group:
#                     row["moq"] = moq_row.min_qty
#                     break

#     # --------------------------
#     # FINAL RESPONSE
#     # --------------------------
#     total = frappe.db.count("Item", {"custom_genric_name": generic})
#     total_pages = (total + page_size - 1) // page_size

#     return api_response(True, "Similar items fetched", {
#         "item_code": item_code,
#         "generic_name": generic,
#         "total": total,
#         "page": page,
#         "page_size": page_size,
#         "total_pages": total_pages,
#         "data": items
#     })

# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_similar_items(item_code=None, mobile_no=None, page=1, page_size=20):

#     api_auth()
#     require_post()

#     # --------------------------
#     # VALIDATION
#     # --------------------------
#     if not item_code:
#         return api_response(False, "item_code is required")

#     if not frappe.db.exists("Item", item_code):
#         return api_response(False, "Invalid item_code")

#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # --------------------------
#     # FIND CUSTOMER → USER + GROUP
#     # --------------------------
#     customer = frappe.get_all(
#         "Customer",
#         filters={"mobile_no": mobile_no},
#         fields=["name", "customer_group"],
#         limit=1
#     )

#     user_id = None
#     customer_group = None

#     if customer:
#         customer_group = customer[0].customer_group

#         portal_user = frappe.get_all(
#             "Portal User",
#             filters={"parent": customer[0].name},
#             fields=["user"],
#             limit=1
#         )

#         if portal_user:
#             user_id = portal_user[0].user

#     # --------------------------
#     # SET USER CONTEXT
#     # --------------------------
#     if user_id:
#         frappe.set_user(user_id)
#     else:
#         frappe.set_user("Administrator")

#     # --------------------------
#     # GENERIC NAME
#     # --------------------------
#     generic = frappe.db.get_value("Item", item_code, "custom_genric_name")

#     if not generic:
#         return api_response(True, "No generic name found", {
#             "generic_name": None,
#             "data": []
#         })

#     # --------------------------
#     # PAGINATION
#     # --------------------------
#     try:
#         page, page_size = int(page), int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     # --------------------------
#     # ITEM FIELDS
#     # --------------------------
#     meta = frappe.get_meta("Item")
#     fields_available = {df.fieldname for df in meta.fields}

#     fields = ["name as item_code", "item_name"]

#     opt_fields = [
#         "item_group", "brand", "stock_uom", "gst_hsn_code",
#         "custom_sub_category", "custom_image_path", "custom_image_1"
#     ]

#     for f in opt_fields:
#         if f in fields_available:
#             fields.append(f)

#     # --------------------------
#     # FETCH SIMILAR ITEMS
#     # --------------------------
#     items = frappe.get_list(
#         "Item",
#         filters={"custom_genric_name": generic},
#         fields=fields,
#         limit_start=start,
#         limit_page_length=page_size,
#         order_by="creation desc"
#     )

#     # --------------------------
#     # PRICE + MOQ LOGIC
#     # --------------------------
#     for row in items:

#         # -------- PRICE FILTERS (ONLY FARMER OVERRIDE) --------
#         price_filters = {
#             "item_code": row["item_code"]
#         }

#         if customer_group == "Farmer":
#             price_filters["price_list"] = f"{row.get('brand')}-Farmer"

#         price_row = frappe.get_list(
#             "Item Price",
#             filters=price_filters,
#             fields=[
#                 "price_list",
#                 "custom_mrp",
#                 "price_list_rate",
#                 # "custom_app_diplay_rate",
#                 "discount",
#                 "custom_oem_code"
#             ],
#             order_by="valid_from desc",
#             limit=1
#         )

#         if user_id and price_row:
#             p = price_row[0]
#             row["price_list"] = p.get("price_list")
#             row["mrp"] = p.get("custom_mrp")
#             row["price"] = p.get("price_list_rate")
#             # row["price"] = p.get("custom_app_diplay_rate")
#             row["discount"] = p.get("discount")
#             row["oem_code"] = p.get("custom_oem_code")
#         else:
#             row["price_list"] = None
#             row["mrp"] = None
#             row["price"] = None
#             row["discount"] = None
#             row["oem_code"] = None

#         # -------- MOQ (UNCHANGED) --------
#         row["moq"] = None

#         if customer_group:
#             item_full_doc = frappe.get_doc("Item", row["item_code"])
#             for moq_row in item_full_doc.get("custom_moq", []):
#                 if moq_row.customer_group == customer_group:
#                     row["moq"] = moq_row.min_qty
#                     break
        

#     # --------------------------
#     # FINAL RESPONSE
#     # --------------------------
#     total = frappe.db.count("Item", {"custom_genric_name": generic})
#     total_pages = (total + page_size - 1) // page_size

#     return api_response(True, "Similar items fetched", {
#         "item_code": item_code,
#         "generic_name": generic,
#         "total": total,
#         "page": page,
#         "page_size": page_size,
#         "total_pages": total_pages,
#         "data": items
#     })


# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response
# from shoption_api.cart.cart import get_item_price_withgst

# @frappe.whitelist(allow_guest=True)
# def get_similar_items(item_code=None, mobile_no=None, page=1, page_size=20):

#     api_auth()
#     require_post()

#     # --------------------------
#     # VALIDATION
#     # --------------------------
#     if not item_code:
#         return api_response(False, "item_code is required")

#     if not frappe.db.exists("Item", item_code):
#         return api_response(False, "Invalid item_code")

#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # --------------------------
#     # FIND CUSTOMER → USER + GROUP
#     # --------------------------
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

#     # --------------------------
#     # SET USER CONTEXT
#     # --------------------------
#     if user_id:
#         frappe.set_user(user_id)
#     else:
#         frappe.set_user("Administrator")

#     # --------------------------
#     # GENERIC NAME
#     # --------------------------
#     generic = frappe.db.get_value("Item", item_code, "custom_genric_name")

#     if not generic:
#         return api_response(True, "No generic name found", {
#             "generic_name": None,
#             "data": []
#         })

#     # --------------------------
#     # PAGINATION
#     # --------------------------
#     try:
#         page, page_size = int(page), int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     # --------------------------
#     # ITEM FIELDS
#     # --------------------------
#     meta = frappe.get_meta("Item")
#     fields_available = {df.fieldname for df in meta.fields}

#     fields = ["name as item_code", "item_name"]

#     opt_fields = [
#         "item_group", "brand", "stock_uom", "gst_hsn_code",
#         "custom_sub_category", "custom_image_path", "custom_image_1"
#     ]

#     for f in opt_fields:
#         if f in fields_available:
#             fields.append(f)

#     # --------------------------
#     # FETCH SIMILAR ITEMS
#     # --------------------------
#     items = frappe.get_list(
#         "Item",
#         filters={"custom_genric_name": generic},
#         fields=fields,
#         limit_start=start,
#         limit_page_length=page_size,
#         order_by="creation desc"
#     )

#     # --------------------------
#     # PRICE + MOQ + GST LOGIC
#     # --------------------------
#     for row in items:

#         # -------- PRICE FILTERS --------
#         price_filters = {"item_code": row["item_code"]}

#         if customer_group == "Farmer":
#             price_filters["price_list"] = f"{row.get('brand')}-Farmer"

#         price_row = frappe.get_list(
#             "Item Price",
#             filters=price_filters,
#             fields=[
#                 "price_list",
#                 "custom_mrp",
#                 "price_list_rate",
#                 "discount",
#                 "custom_oem_code"
#             ],
#             order_by="valid_from desc",
#             limit=1
#         )

#         if user_id and price_row:
#             p = price_row[0]
#             row["price_list"] = p.get("price_list")
#             row["mrp"] = p.get("custom_mrp")
#             row["price"] = p.get("price_list_rate")
#             row["discount"] = p.get("discount")
#             row["oem_code"] = p.get("custom_oem_code")
#         else:
#             row["price_list"] = None
#             row["mrp"] = None
#             row["price"] = None
#             row["discount"] = None
#             row["oem_code"] = None

#         # -------- MOQ --------
#         row["moq"] = None
#         if customer_group:
#             item_full_doc = frappe.get_doc("Item", row["item_code"])
#             for moq_row in item_full_doc.get("custom_moq", []):
#                 if moq_row.customer_group == customer_group:
#                     row["moq"] = moq_row.min_qty
#                     break

#         # -------- GST PRICE (FIXED) --------
#         row["gst_price"] = None
#         if user_id and customer_group and row.get("price"):
#             try:
#                 gst_data = get_item_price_withgst(
#                     item_code=row["item_code"],
#                     customer=customer_name,
#                     customer_group=customer_group,
#                     company=frappe.defaults.get_global_default("company"),
#                     currency=frappe.defaults.get_global_default("currency"),
#                     qty=1,
#                     brand=row.get("brand")
#                 )
#                 row["gst_price"] = gst_data.get("rate_incl_gst")
#             except Exception:
#                 row["gst_price"] = None

#     # --------------------------
#     # FINAL RESPONSE
#     # --------------------------
#     total = frappe.db.count("Item", {"custom_genric_name": generic})
#     total_pages = (total + page_size - 1) // page_size

#     return api_response(True, "Similar items fetched", {
#         "item_code": item_code,
#         "generic_name": generic,
#         "total": total,
#         "page": page,
#         "page_size": page_size,
#         "total_pages": total_pages,
#         "data": items
#     })

# updated code 18/12 with key name changes
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst

@frappe.whitelist(allow_guest=True)
def get_similar_items2(item_code=None, mobile_no=None, page=1, page_size=20):

    api_auth()
    require_post()

    # --------------------------
    # VALIDATION
    # --------------------------
    if not item_code:
        return api_response(False, "item_code is required")

    if not frappe.db.exists("Item", item_code):
        return api_response(False, "Invalid item_code")

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    # --------------------------
    # FIND CUSTOMER → USER + GROUP
    # --------------------------
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

    # --------------------------
    # SET USER CONTEXT
    # --------------------------
    frappe.set_user(user_id if user_id else "Administrator")

    # --------------------------
    # GENERIC NAME
    # --------------------------
    generic = frappe.db.get_value("Item", item_code, "custom_genric_name")

    if not generic:
        return api_response(True, "No generic name found", {
            "generic_name": None,
            "data": []
        })

    # --------------------------
    # PAGINATION
    # --------------------------
    try:
        page, page_size = int(page), int(page_size)
    except:
        page, page_size = 1, 20

    start = (page - 1) * page_size

    # --------------------------
    # ITEM FIELDS
    # --------------------------
    meta = frappe.get_meta("Item")
    fields_available = {df.fieldname for df in meta.fields}

    fields = ["name as item_code", "item_name"]

    optional_fields = [
        "item_group", "brand", "stock_uom", "gst_hsn_code",
        "custom_sub_category", "custom_image_path", "custom_image_1"
    ]

    for f in optional_fields:
        if f in fields_available:
            fields.append(f)

    # --------------------------
    # FETCH SIMILAR ITEMS
    # --------------------------
    items = frappe.get_list(
        "Item",
        filters={"custom_genric_name": generic},
        fields=fields,
        limit_start=start,
        limit_page_length=page_size,
        order_by="creation desc"
    )

    # --------------------------
    # PRICE + MOQ + GST LOGIC
    # --------------------------
    for row in items:

        price_filters = {
            "item_code": ["in", item_codes],
            "selling": 1
        }
        price_row=[]
        if customer_group and customer_group.lower() == "farmer":
            price_filters["price_list"] = ["like", "%-Farmer"]
        elif customer_group and customer_group.lower() == "dealer":
            price_filters["price_list"] = ["like", "%-Dealer"]

        if customer_group and customer_group.lower() == "farmer" and user_id:
            price_row = frappe.get_all(
                "Item Price",
                filters=price_filters,
                fields=[
                    "item_code", "price_list", "price_list_rate",
                    "custom_mrp", "custom_discount", "custom_oem_code",
                    "valid_from"
                ],
                order_by="valid_from desc"
            )
        elif user_id:
            price_row = frappe.get_list(
                "Item Price",
                filters=price_filters,
                fields=[
                    "item_code", "price_list", "price_list_rate",
                    "custom_mrp", "custom_discount", "custom_oem_code",
                    "valid_from"
                ],
                order_by="valid_from desc"
            )

        base_price = None
        gst_price = None

        if user_id and price_row:
            p = price_row[0]
            base_price = p.get("price_list_rate")

            row["price_list"] = p.get("price_list")
            row["mrp"] = p.get("custom_mrp")
            row["discount"] = p.get("discount")
            row["oem_code"] = p.get("custom_oem_code")

            # -------- GST PRICE --------
            try:
                gst_data = get_item_price_withgst(
                    item_code=row["item_code"],
                    customer=customer_name,
                    customer_group=customer_group,
                    company=frappe.defaults.get_global_default("company"),
                    currency=frappe.defaults.get_global_default("currency"),
                    qty=1,
                    brand=row.get("brand")
                )
                gst_price = gst_data.get("rate_incl_gst")
            except Exception:
                gst_price = None
        else:
            row["price_list"] = None
            row["mrp"] = None
            row["discount"] = None
            row["oem_code"] = None

        # -------- FINAL PRICE MAPPING --------
        row["no_gst_price"] = base_price
        row["price"] = gst_price
        row["actual_rate"] = gst_price

        # -------- MOQ --------
        row["moq"] = None
        if customer_group:
            item_full_doc = frappe.get_doc("Item", row["item_code"])
            for moq_row in item_full_doc.get("custom_moq", []):
                if moq_row.customer_group == customer_group:
                    row["moq"] = moq_row.min_qty
                    break

    # --------------------------
    # FINAL RESPONSE
    # --------------------------
    total = frappe.db.count("Item", {"custom_genric_name": generic})
    total_pages = (total + page_size - 1) // page_size

    return api_response(True, "Similar items fetched", {
        "item_code": item_code,
        "generic_name": generic,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": items
    })
    #  optimized code 
    
@frappe.whitelist(allow_guest=True)
def get_similar_items(item_code=None, mobile_no=None, page=1, page_size=20):

    api_auth()
    require_post()

    # --------------------------
    # 1️⃣ VALIDATION
    # --------------------------
    if not item_code or not mobile_no:
        return api_response(False, "item_code and mobile_no are required")

    if not frappe.db.exists("Item", item_code):
        return api_response(False, "Invalid item_code")

    # --------------------------
    # 2️⃣ CUSTOMER + USER
    # --------------------------
    customer = frappe.db.get_value(
        "Customer",
        {"mobile_no": mobile_no},
        ["name", "customer_group"],
        as_dict=True
    )

    customer_name = customer.name if customer else None
    customer_group = customer.customer_group if customer else None

    user_id = frappe.db.get_value(
        "Portal User",
        {"parent": customer_name},
        "user"
    ) if customer_name else None

    frappe.set_user(user_id or "Administrator")

    # --------------------------
    # 3️⃣ GENERIC NAME
    # --------------------------
    generic = frappe.db.get_value("Item", item_code, "custom_genric_name")
    if not generic:
        return api_response(True, "No generic name found", {
            "generic_name": None,
            "data": []
        })

    # --------------------------
    # 4️⃣ PAGINATION
    # --------------------------
    page = int(page or 1)
    page_size = int(page_size or 20)
    start = (page - 1) * page_size

    # --------------------------
    # 5️⃣ FETCH ITEMS
    # --------------------------
    items = frappe.get_list(
        "Item",
        filters={"custom_genric_name": generic,"disabled":0},
        fields=[
            "name as item_code",
            "item_name",
            "item_group",
            "brand",
            "stock_uom",
            "gst_hsn_code",
            "custom_sub_category",
            "custom_image_path",
            "custom_image_1"
        ],
        limit_start=start,
        limit_page_length=page_size,
        order_by="creation desc"
    )

    if not items:
        return api_response(True, "No items found", {"data": []})

    item_codes = [i["item_code"] for i in items]

    price_filters = {
        "item_code": ["in", item_codes],
        "selling": 1
    }
    price_rows=[]
    if customer_group and customer_group.lower() == "farmer":
        price_filters["price_list"] = ["like", "%-Farmer"]
    elif customer_group and customer_group.lower() == "dealer":
        price_filters["price_list"] = ["like", "%-Dealer"]

    if customer_group and customer_group.lower() == "farmer" and user_id:
        price_rows = frappe.get_all(
            "Item Price",
            filters=price_filters,
            fields=[
                "item_code", "price_list", "price_list_rate",
                "custom_mrp", "custom_discount", "custom_oem_code",
                "valid_from"
            ],
            order_by="valid_from desc"
        )
    elif user_id:
        price_rows = frappe.get_list(
            "Item Price",
            filters=price_filters,
            fields=[
                "item_code", "price_list", "price_list_rate",
                "custom_mrp", "custom_discount", "custom_oem_code",
                "valid_from"
            ],
            order_by="valid_from desc"
        )

    price_map = {}
    for p in price_rows:
        if p.item_code not in price_map:
            price_map[p.item_code] = p
    brand_ids = list({i.brand for i in items if i.brand})
    brand_map = {}
    if brand_ids:
        brands = frappe.get_all(
            "Brand",
            filters={"name": ["in", brand_ids]},
            fields=["name", "brand as brand_name"]
        )
        brand_map = {b.name: b.brand_name for b in brands}

    # --------------------------
    # 7️⃣ BULK MOQ
    # --------------------------
    moq_map = {}
    if customer_group:
        moq_rows = frappe.get_all(
            "MOQ Items",
            filters={
                "parent": ["in", item_codes],
                "customer_group": customer_group
            },
            fields=["parent", "min_qty"]
        )
        moq_map = {m.parent: m.min_qty for m in moq_rows}

    # --------------------------
    # 8️⃣ BULK ITEM TAX TEMPLATE
    # --------------------------
    item_tax_rows = frappe.get_all(
        "Item Tax",
        filters={"parent": ["in", item_codes]},
        fields=["parent", "item_tax_template"]
    )

    item_tax_map = {
        r.parent: r.item_tax_template for r in item_tax_rows
    }

    # --------------------------
    # 9️⃣ BULK GST %
    # --------------------------
    tax_templates = list(set(item_tax_map.values()))

    gst_map = {}
    if tax_templates:
        gst_rows = frappe.get_all(
            "Item Tax Template",
            filters={"name": ["in", tax_templates]},
            fields=["name", "gst_rate"]
        )
        gst_map = {g.name: g.gst_rate for g in gst_rows}

    # --------------------------
    # 🔟 GST CALC FUNCTION
    # --------------------------
    def calc_gst(price, gst_percent):
        if not price:
            return None
        return round(price + (price * gst_percent / 100), 2)

    # --------------------------
    # 1️⃣1️⃣ FINAL MAP
    # --------------------------
    for row in items:
        code = row["item_code"]
        price = price_map.get(code)
        if not user_id:
                row.update({
                    "price_list": None,
                    "mrp": None,
                    "discount": None,
                    "oem_code": None,
                    "no_gst_price": None,
                    "price": None,
                    "actual_rate": None,
                    "moq": 1,
                    "brand_name": brand_map.get(row.get("brand")),
                    "brand_id": row.get("brand")
                })
                continue
        base_price = price.price_list_rate if price else None

        tax_template = item_tax_map.get(code)
        gst_percent = gst_map.get(tax_template, 0)

        gst_price = calc_gst(base_price, gst_percent)

        row.update({
            "price_list": price.price_list if price else None,
            "mrp": price.custom_mrp if price else None,
            "discount": price.custom_discount if price else None,
            "oem_code": price.custom_oem_code if price else None,
            "no_gst_price": base_price,
            "price": gst_price,
            "actual_rate": gst_price,
            "moq": moq_map.get(code),
            "brand" : brand_map.get(row.get("brand")),
            "brand_id":row.get("brand")
        })

    # --------------------------
    # 1️⃣2️⃣ PAGINATION
    # --------------------------
    total = frappe.db.count("Item", {"custom_genric_name": generic})
    total_pages = (total + page_size - 1) // page_size

    return api_response(True, "Similar items fetched", {
        "item_code": item_code,
        "generic_name": generic,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": items
    })

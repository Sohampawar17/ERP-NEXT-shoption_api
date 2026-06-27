# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response
# from shoption_api.cart.cart import get_item_price_withgst  # 18/12

# @frappe.whitelist(allow_guest=True)
# def get_items(category=None, brand=None, subcategory=None, search=None,
#               is_active=1, page=1, page_size=20, mobile_no=None):


#     api_auth()
#     require_post()

#     # -----------------------------------------
#     # Mobile required
#     # -----------------------------------------
#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

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

#     frappe.set_user(user_id if user_id else "Administrator")

#     # -----------------------------------------
#     # Pagination
#     # -----------------------------------------
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     meta = frappe.get_meta("Item")
#     fields_available = {df.fieldname for df in meta.fields}

#     # -----------------------------------------
#     # Filters
#     # -----------------------------------------
#     filters = {}

#     if category and "item_group" in fields_available:
#         filters["item_group"] = category

#     if brand and "brand" in fields_available:
#         filters["brand"] = brand

#     if subcategory:
#         if "custom_sub_category" in fields_available:
#             filters["custom_sub_category"] = subcategory
#         elif "item_group" in fields_available:
#             filters["item_group"] = subcategory

#     if is_active and "disabled" in fields_available:
#         filters["disabled"] = 0

#     if search and "item_name" in fields_available:
#         filters["item_name"] = ["like", f"%{search}%"]

#     # -----------------------------------------
#     # Item fields
#     # -----------------------------------------
#     fields = ["name as item_code", "item_name"]

#     optional_fields = [
#         "item_group", "brand", "stock_uom",
#         "gst_hsn_code", "custom_sub_category",
#         "custom_image_path", "custom_image_1"
#     ]

#     for f in optional_fields:
#         if f in fields_available:
#             fields.append(f)
    
#     try:
#         # -----------------------------------------
#         # 2️⃣ Fetch Items
#         # -----------------------------------------
#         data = frappe.get_list(
#             "Item",
#             filters=filters,
#             fields=fields,
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         if not data:
#             return api_response(True, "No items found", {
#                 "total": 0,
#                 "page": page,
#                 "page_size": page_size,
#                 "total_pages": 0,
#                 "data": []
#             })

#         item_codes = [d["item_code"] for d in data]

#         # -----------------------------------------
#         # 3️⃣ BULK ITEM PRICE
#         # -----------------------------------------
#         price_filters = {
#             "item_code": ["in", item_codes]
#         }

#         # if customer_group == "Farmer":
#         #     price_filters["price_list"] = ["like", "%-Farmer"]
            
#         if customer_group == "Farmer" or not user_id:
#             price_filters["price_list"] = ["like", "%-Farmer"]

#         price_rows = frappe.get_list(
#             "Item Price",
#             filters=price_filters,
#             fields=[
#                 "item_code",
#                 "price_list",
#                 "custom_mrp",
#                 "price_list_rate",
#                 "custom_discount",
#                 "custom_oem_code"
#             ],
#             order_by="valid_from desc"
#         )

#         price_map = {}
#         for p in price_rows:
#             if p.item_code not in price_map:
#                 price_map[p.item_code] = p

#         # if user_id and price_row:
#         #     p = price_row[0]
#         #     base_price = p.get("price_list_rate")

#         #     row["price_list"] = p.get("price_list")
#         #     row["mrp"] = p.get("custom_mrp")
#         #     row["discount"] = p.get("custom_discount")
#         #     row["oem_code"] = p.get("custom_oem_code")
#         # else:
#         #     row["price_list"] = None
#         #     row["mrp"] = None
#         #     row["discount"] = None
#         #     row["oem_code"] = None

#         # -----------------------------------------
#         # 4️⃣ BULK MOQ
#         # -----------------------------------------
#         moq_map = {}
#         if customer_group:
#             moq_rows = frappe.get_all(
#                 "MOQ Items",  # ⚠️ child table name
#                 filters={
#                     "parent": ["in", item_codes],
#                     "customer_group": customer_group
#                 },
#                 fields=["parent", "min_qty"]
#             )
#             moq_map = {m.parent: m.min_qty for m in moq_rows}

#         # -----------------------------------------
#         # 5️⃣ BULK GST TEMPLATE
#         # -----------------------------------------
#         item_tax_rows = frappe.get_all(
#             "Item Tax",
#             filters={"parent": ["in", item_codes]},
#             fields=["parent", "item_tax_template"]
#         )

#         item_tax_map = {
#             r.parent: r.item_tax_template for r in item_tax_rows
#         }

#         # templates = list(set(filter(None, item_tax_map.values())))

#         # tax_rate_map = {}
#         # if templates:
#         #     tax_details = frappe.get_all(
#         #         "Item Tax Template Detail",
#         #         filters={"parent": ["in", templates]},
#         #         fields=["parent", "tax_rate"]
#         #     )

#         #     for t in tax_details:
#         #         tax_rate_map.setdefault(t.parent, 0)
#         #         tax_rate_map[t.parent] += t.tax_rate

#         def calc_gst(price, gst_percent):
#             if not price:
#                 return None
#             return round(price + (price * gst_percent / 100), 2)

#         # -----------------------------------------
#         # 6️⃣ FINAL MAP
#         # -----------------------------------------
#         for row in data:
#             code = row["item_code"]
#             # price = price_map.get(code) if user_id else 0 
#             price = price_map.get(code)

#             base_price = price.price_list_rate if price else None

#             tax_template = item_tax_map.get(code)
#             gst_percent = frappe.db.get_value("Item Tax Template",tax_template,"gst_rate")or 0
#             gst_price = calc_gst(base_price, gst_percent)

#             row.update({
#                 "price_list": price.price_list if price else None,
#                 "mrp": price.custom_mrp if price else None,
#                 "discount": price.custom_discount if price else None,
#                 "oem_code": price.custom_oem_code if price else None,
#                 "no_gst_price": base_price,
#                 "price": gst_price,
#                 "actual_rate": gst_price,
#                 "moq": moq_map.get(code)
#             })

#         # -----------------------------------------
#         # Pagination
#         # -----------------------------------------
#         total = frappe.db.count("Item", filters)
#         total_pages = (total + page_size - 1) // page_size

#         return api_response(True, "Item list fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": data
#         })

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_items API error")
#         return api_response(False, str(e))





import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst  # 18/12

@frappe.whitelist(allow_guest=True)
def get_items(category=None, brand=None, subcategory=None, search=None,
              is_active=1, page=1, page_size=20, mobile_no=None):

    api_auth()
    require_post()

    # -----------------------------------------
    # Mobile required
    # -----------------------------------------
    if not mobile_no:
        return api_response(False, "mobile_no is required")

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

    frappe.set_user(user_id if user_id else "Administrator")

    # -----------------------------------------
    # Pagination
    # -----------------------------------------
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    start = (page - 1) * page_size

    meta = frappe.get_meta("Item")
    fields_available = {df.fieldname for df in meta.fields}

    # -----------------------------------------
    # Filters
    # -----------------------------------------
    filters = {}

    if category and "item_group" in fields_available:
        filters["item_group"] = category

    if brand and "brand" in fields_available:
        filters["brand"] = brand

    if subcategory:
        if "custom_sub_category" in fields_available:
            filters["custom_sub_category"] = subcategory
        elif "item_group" in fields_available:
            filters["item_group"] = subcategory

    if is_active and "disabled" in fields_available:
        filters["disabled"] = 0

    if search and "item_name" in fields_available:
        filters["item_name"] = ["like", f"%{search}%"]

    # -----------------------------------------
    # Item fields
    # -----------------------------------------
    fields = ["name as item_code", "item_name"]

    optional_fields = [
        "item_group", "brand", "stock_uom",
        "gst_hsn_code", "custom_sub_category",
        "custom_image_path", "custom_image_1"
    ]

    for f in optional_fields:
        if f in fields_available:
            fields.append(f)

    try:
        # -----------------------------------------
        # Fetch Items
        # -----------------------------------------
        data = frappe.get_list(
            "Item",
            filters=filters,
            fields=fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        if not data:
            return api_response(True, "No items found", {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "data": []
            })

        item_codes = [d["item_code"] for d in data]

        # -----------------------------------------
        # BULK ITEM PRICE
        # -----------------------------------------
        price_filters = {
            "item_code": ["in", item_codes]
        }

        # ADDED: strict farmer enforcement flag
        force_farmer_price = False

        if customer_group == "Farmer" or not user_id:
            force_farmer_price = True
            price_filters["price_list"] = ["like", "%-Farmer"]

        price_rows = frappe.get_list(
            "Item Price",
            filters=price_filters,
            fields=[
                "item_code",
                "price_list",
                "custom_mrp",
                "price_list_rate",
                "custom_discount",
                "custom_oem_code"
            ],
            order_by="valid_from desc"
        )

        price_map = {}
        for p in price_rows:
            if p.item_code not in price_map:
                price_map[p.item_code] = p

        # -----------------------------------------
        # BULK MOQ
        # -----------------------------------------
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

        # -----------------------------------------
        # BULK GST TEMPLATE
        # -----------------------------------------
        item_tax_rows = frappe.get_all(
            "Item Tax",
            filters={"parent": ["in", item_codes]},
            fields=["parent", "item_tax_template"]
        )

        item_tax_map = {
            r.parent: r.item_tax_template for r in item_tax_rows
        }

        def calc_gst(price, gst_percent):
            if not price:
                return None
            return round(price + (price * gst_percent / 100), 2)

        # -----------------------------------------
        # FINAL MAP
        # -----------------------------------------
        for row in data:
            code = row["item_code"]
            price = price_map.get(code)

            # ADDED: HARD BLOCK non-farmer prices
            if force_farmer_price and price and "Farmer" not in price.price_list:
                price = None

            base_price = price.price_list_rate if price else None

            tax_template = item_tax_map.get(code)
            gst_percent = frappe.db.get_value(
                "Item Tax Template",
                tax_template,
                "gst_rate"
            ) or 0

            gst_price = calc_gst(base_price, gst_percent)

            row.update({
                "price_list": price.price_list if price else None,
                "mrp": price.custom_mrp if price else None,
                "discount": price.custom_discount if price else None,
                "oem_code": price.custom_oem_code if price else None,
                "no_gst_price": base_price,
                "price": gst_price,
                "actual_rate": gst_price,
                "moq": moq_map.get(code)
            })

        # -----------------------------------------
        # Pagination
        # -----------------------------------------
        total = frappe.db.count("Item", filters)
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Item list fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_items API error")
        return api_response(False, str(e))


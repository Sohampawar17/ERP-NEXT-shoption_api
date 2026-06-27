
# updated logic 
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_items_by_dealership_master(dealership_master_name=None, page=1, page_size=20):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     # -----------------------------
#     # VALIDATION
#     # -----------------------------
#     if not dealership_master_name:
#         return api_response(False, "dealership_master_name is required")

#     # -----------------------------
#     # PAGINATION
#     # -----------------------------
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     # -----------------------------
#     # FETCH ALL DEALERSHIP CATEGORIES
#     # -----------------------------
#     categories = frappe.get_all(
#         "Dealership Category",
#         filters={"dealership_category_name": dealership_master_name},
#         fields=[
#             "name",
#             "dealership_category_name",
#             "brand",
#             "category",
#             "sub_category"
#         ],
#         order_by="creation asc"
#     )

#     if not categories:
#         return api_response(False, "No dealership categories found")

#     # -----------------------------
#     # ITEM META (SAFE FIELDS)
#     # -----------------------------
#     meta = frappe.get_meta("Item")
#     fields_available = {df.fieldname for df in meta.fields}

#     item_fields = ["name as item_code", "item_name"]

#     if "brand" in fields_available: item_fields.append("brand")
#     if "item_group" in fields_available: item_fields.append("item_group")
#     if "custom_sub_category" in fields_available: item_fields.append("custom_sub_category")
#     if "stock_uom" in fields_available: item_fields.append("stock_uom")
#     if "gst_hsn_code" in fields_available: item_fields.append("gst_hsn_code")
#     if "custom_image_path" in fields_available: item_fields.append("custom_image_path")
#     if "custom_image_1" in fields_available: item_fields.append("custom_image_1")

#     response_categories = []

#     # -----------------------------
#     # LOOP EACH CATEGORY → FETCH ITEMS
#     # -----------------------------
#     for cat in categories:
#         filters = {"disabled": 0}

#         if cat.brand:
#             filters["brand"] = cat.brand

#         if cat.category:
#             filters["item_group"] = cat.category

#         if cat.sub_category:
#             if frappe.db.has_column("Item", "custom_sub_category"):
#                 filters["custom_sub_category"] = cat.sub_category
#             else:
#                 filters["item_group"] = cat.sub_category

#         items = frappe.get_list(
#             "Item",
#             filters=filters,
#             fields=item_fields,
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         response_categories.append({
#             "dealership_category_id": cat.name,
#             "dealership_category_name": cat.dealership_category_name,
#             "brand": cat.brand,
#             "category": cat.category,
#             "sub_category": cat.sub_category,
#             "items": items
#         })

#     # -----------------------------
#     # FINAL RESPONSE
#     # -----------------------------
#     return api_response(
#         True,
#         "Dealership items fetched successfully",
#         {
#             "dealership_master": dealership_master_name,
#             "page": page,
#             "page_size": page_size,
#             "categories": response_categories
#         }
#     )


# updated fields
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response
# from shoption_api.cart.cart import get_item_price_withgst
# @frappe.whitelist(allow_guest=True)
# def get_items_by_dealership_master(
#     dealership_master_name=None,
#     mobile_no=None,
#     page=1,
#     page_size=20
# ):
#     api_auth()
#     require_post()

#     # -----------------------------
#     # VALIDATION
#     # -----------------------------
#     if not dealership_master_name:
#         return api_response(False, "dealership_master_name is required")

#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # -----------------------------
#     # CUSTOMER → USER CONTEXT (SAME AS get_items)
#     # -----------------------------
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

#     # -----------------------------
#     # PAGINATION
#     # -----------------------------
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     # -----------------------------
#     # FETCH DEALERSHIP CATEGORIES
#     # -----------------------------
#     categories = frappe.get_all(
#         "Dealership Category",
#         filters={"dealership_category_name": dealership_master_name},
#         fields=[
#             "name",
#             "dealership_category_name",
#             "brand",
#             "category",
#             "sub_category"
#         ],
#         order_by="creation asc"
#     )

#     if not categories:
#         return api_response(False, "No dealership categories found")

#     # -----------------------------
#     # ITEM META
#     # -----------------------------
#     meta = frappe.get_meta("Item")
#     fields_available = {df.fieldname for df in meta.fields}

#     item_fields = ["name as item_code", "item_name"]

#     optional_fields = [
#         "brand", "item_group", "custom_sub_category",
#         "stock_uom", "gst_hsn_code",
#         "custom_image_path", "custom_image_1"
#     ]

#     for f in optional_fields:
#         if f in fields_available:
#             item_fields.append(f)

#     response_categories = []

#     # =====================================================
#     # LOOP EACH CATEGORY
#     # =====================================================
#     for cat in categories:
#         filters = {"disabled": 0}

#         if cat.brand:
#             filters["brand"] = cat.brand

#         if cat.category:
#             filters["item_group"] = cat.category

#         if cat.sub_category:
#             if "custom_sub_category" in fields_available:
#                 filters["custom_sub_category"] = cat.sub_category
#             else:
#                 filters["item_group"] = cat.sub_category

#         # if cat.sub_category:
#         #     if cat.sub_category not in sub_category_image_map:
#         #         sub_category_image_map[cat.sub_category] = frappe.db.get_value(
#         #             "Sub Categoury",
#         #             cat.sub_category,
#         #             "image_path"
#         #         )

#         #     subcategory_image = sub_category_image_map.get(cat.sub_category)


#         # -----------------------------
#         # FETCH ITEMS
#         # -----------------------------
#         items = frappe.get_list(
#             "Item",
#             filters=filters,
#             fields=item_fields,
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         if not items:
#             response_categories.append({
#                 "dealership_category_id": cat.name,
#                 "dealership_category_name": cat.dealership_category_name,
#                 "brand": cat.brand,
#                 "category": cat.category,
#                 "sub_category": cat.sub_category,
#                 "items": []
#             })
#             continue

#         item_codes = [i["item_code"] for i in items]

#         # -----------------------------
#         # PRICE LIST (SAME LOGIC)
#         # -----------------------------
#         price_filters = {"item_code": ["in", item_codes]}

#         if customer_group == "Farmer":
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

#         # -----------------------------
#         # MOQ (SAME LOGIC)
#         # -----------------------------
#         moq_map = {}
#         if customer_group:
#             moq_rows = frappe.get_all(
#                 "MOQ Items",
#                 filters={
#                     "parent": ["in", item_codes],
#                     "customer_group": customer_group
#                 },
#                 fields=["parent", "min_qty"]
#             )
#             moq_map = {m.parent: m.min_qty for m in moq_rows}

#         # -----------------------------
#         # TAX TEMPLATE
#         # -----------------------------
#         item_tax_rows = frappe.get_all(
#             "Item Tax",
#             filters={"parent": ["in", item_codes]},
#             fields=["parent", "item_tax_template"]
#         )

#         tax_map = {r.parent: r.item_tax_template for r in item_tax_rows}

#         # -----------------------------
#         # FINAL MAP (IDENTICAL OUTPUT)
#         # -----------------------------
#         for row in items:
#             code = row["item_code"]
#             # price = price_map.get(code)
#             # base_price = price.price_list_rate if price else None
            
#             price = price_map.get(code) if user_id else None
#             base_price = price.price_list_rate if price else None
            
#             tax_template = tax_map.get(code)
#             gst_percent = frappe.db.get_value(
#                 "Item Tax Template",
#                 tax_template,
#                 "gst_rate"
#             ) or 0

#             gst_price = (
#                 round(base_price + (base_price * gst_percent / 100), 2)
#                 if base_price else None
#             )

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

#         response_categories.append({
#             "dealership_category_id": cat.name,
#             "dealership_category_name": cat.dealership_category_name,
#             "brand": cat.brand,
#             "category": cat.category,
#             "sub_category": cat.sub_category,
#             # "sub_category_image": subcategory_image,
#             "items": items
#         })

#     # -----------------------------
#     # FINAL RESPONSE
#     # -----------------------------
#     return api_response(
#         True,
#         "Dealership items fetched successfully",
#         {
#             "dealership_master": dealership_master_name,
#             "page": page,
#             "page_size": page_size,
#             "categories": response_categories
#         }
#     )

# included subcategory image path
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst

@frappe.whitelist(allow_guest=True)
def get_items_by_dealership_master(
    dealership_master_name=None,
    mobile_no=None,
    page=1,
    page_size=20
):
    api_auth()
    require_post()

    # -----------------------------
    # VALIDATION
    # -----------------------------
    if not dealership_master_name:
        return api_response(False, "dealership_master_name is required")

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    # -----------------------------
    # CUSTOMER CONTEXT
    # -----------------------------
    customer = frappe.get_all(
        "Customer",
        filters={"mobile_no": mobile_no},
        fields=["name", "customer_group"],
        limit=1
    )

    user_id = None
    customer_group = None

    if customer:
        customer_group = customer[0].customer_group
        portal_user = frappe.get_all(
            "Portal User",
            filters={"parent": customer[0].name},
            fields=["user"],
            limit=1
        )
        if portal_user:
            user_id = portal_user[0].user

    frappe.set_user(user_id if user_id else "Administrator")

    # -----------------------------
    # PAGINATION
    # -----------------------------
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    start = (page - 1) * page_size

    # -----------------------------
    # FETCH DEALERSHIP CATEGORIES
    # -----------------------------
    categories = frappe.get_all(
        "Dealership Category",
        filters={"dealership_category_name": dealership_master_name},
        fields=["name", "dealership_category_name", "brand", "category", "sub_category"],
        order_by="creation asc"
    )

    if not categories:
        return api_response(False, "No dealership categories found")

    # -----------------------------
    # ITEM META
    # -----------------------------
    meta = frappe.get_meta("Item")
    fields_available = {df.fieldname for df in meta.fields}

    item_fields = ["name as item_code", "item_name"]
    optional_fields = [
        "brand", "item_group", "custom_sub_category",
        "stock_uom", "gst_hsn_code",
        "custom_image_path", "custom_image_1"
    ]

    for f in optional_fields:
        if f in fields_available:
            item_fields.append(f)

    response_categories = []
    sub_category_image_map = {}

    # =====================================================
    # LOOP EACH CATEGORY
    # =====================================================
    for cat in categories:
        filters = {"disabled": 0}

        if cat.brand:
            filters["brand"] = cat.brand

        if cat.category:
            filters["item_group"] = cat.category

        if cat.sub_category:
            if "custom_sub_category" in fields_available:
                filters["custom_sub_category"] = cat.sub_category
            else:
                filters["item_group"] = cat.sub_category

    
        # -----------------------------
        # FETCH ITEMS
        # -----------------------------
        items = frappe.get_list(
            "Item",
            filters=filters,
            fields=item_fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        if not items:
            subcategoury_data=frappe.db.get_value("Sub Categoury", cat.sub_category, ["sub_categoury","image_path"], as_dict=True) if cat.sub_category else None
            subcategory_image = subcategoury_data.image_path if subcategoury_data else None
            response_categories.append({
                "dealership_category_id": cat.name,
                "dealership_category_name": cat.dealership_category_name,
                "brand": cat.brand,
                "category": cat.category,
                "sub_category":  cat.sub_category,
                "sub_category_name": frappe.db.get_value("Sub Categoury", cat.sub_category, "sub_categoury") if cat.sub_category else None,
                "sub_category_image": subcategory_image,
                "items": []
            })
            continue

        item_codes = [i["item_code"] for i in items]

        # -----------------------------
        # PRICE LIST
        # -----------------------------
        price_filters = {"item_code": ["in", item_codes]}
        if customer_group == "Farmer":
            price_filters["price_list"] = ["like", "%-Farmer"]

        price_rows = frappe.get_list(
            "Item Price",
            filters=price_filters,
            fields=[
                "item_code", "price_list", "custom_mrp",
                "price_list_rate", "custom_discount", "custom_oem_code"
            ],
            order_by="valid_from desc"
        )

        price_map = {}
        for p in price_rows:
            if p.item_code not in price_map:
                price_map[p.item_code] = p

        # -----------------------------
        # MOQ
        # -----------------------------
        moq_map = {}
        if customer_group:
            moq_rows = frappe.get_all(
                "MOQ Items",
                filters={"parent": ["in", item_codes], "customer_group": customer_group},
                fields=["parent", "min_qty"]
            )
            moq_map = {m.parent: m.min_qty for m in moq_rows}

        # -----------------------------
        # TAX
        # -----------------------------
        tax_map = {
            r.parent: r.item_tax_template
            for r in frappe.get_all(
                "Item Tax",
                filters={"parent": ["in", item_codes]},
                fields=["parent", "item_tax_template"]
            )
        }

        # -----------------------------
        # FINAL ITEM MAP
        # -----------------------------
        for row in items:
            code = row["item_code"]
            price = price_map.get(code) if user_id else None
            base_price = price.price_list_rate if price else None

            gst_percent = frappe.db.get_value(
                "Item Tax Template",
                tax_map.get(code),
                "gst_rate"
            ) or 0

            gst_price = (
                round(base_price + (base_price * gst_percent / 100), 2)
                if base_price else None
            )

            row.update({
                "price_list": price.price_list if price else None,
                "mrp": price.custom_mrp if price else None,
                "discount": price.custom_discount if price else None,
                "oem_code": price.custom_oem_code if price else None,
                "no_gst_price": base_price,
                "price": gst_price,
                "actual_rate": gst_price,
                "moq": moq_map.get(code),
                "brand":frappe.db.get_value("Brand",  row["brand"], "brand"),
            })
        subcategoury_data=frappe.db.get_value("Sub Categoury", cat.sub_category, ["sub_categoury","image_path"], as_dict=True) if cat.sub_category else None
        subcategory_image = subcategoury_data.image_path if subcategoury_data else None
        response_categories.append({
            "dealership_category_id": cat.name,
            "dealership_category_name": cat.dealership_category_name,
            "brand": cat.brand,
            "category": cat.category,
            "sub_category":cat.sub_category,
            "sub_category_name": subcategoury_data.sub_categoury if subcategoury_data else None,
            "sub_category_image": subcategory_image,
            "items": items
        })

    # -----------------------------
    # FINAL RESPONSE
    # -----------------------------
    return api_response(
        True,
        "Dealership items fetched successfully",
        {
            "dealership_master": dealership_master_name,
            "page": page,
            "page_size": page_size,
            "categories": response_categories
        }
    )



import frappe

def get_allowed_item_codes_by_dealership(dealership_master_name):
    """
    Returns SET of allowed item_codes for a dealership master
    NO pagination
    NO pricing
    NO user context
    """

    if not dealership_master_name:
        return set()

    categories = frappe.get_all(
        "Dealership Category",
        filters={"dealership_category_name": dealership_master_name},
        fields=["brand", "category", "sub_category"]
    )

    if not categories:
        return set()

    meta = frappe.get_meta("Item")
    fields_available = {df.fieldname for df in meta.fields}

    allowed_item_codes = set()

    for cat in categories:
        filters = {"disabled": 0}

        if cat.brand:
            filters["brand"] = cat.brand

        if cat.category:
            filters["item_group"] = cat.category

        if cat.sub_category:
            if "custom_sub_category" in fields_available:
                filters["custom_sub_category"] = cat.sub_category
            else:
                filters["item_group"] = cat.sub_category

        items = frappe.get_all(
            "Item",
            filters=filters,
            fields=["name"]
        )

        for item in items:
            allowed_item_codes.add(str(item.name).strip())

    return allowed_item_codes
